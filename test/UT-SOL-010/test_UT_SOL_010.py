import json
import os
from types import SimpleNamespace
from datetime import datetime, timedelta

import jwt
import pytest
import requests
from django.test import RequestFactory
from rest_framework.test import APIClient

import service_requests.api.invoice_viewset as iv


class DummyAuditClient:
    def __init__(self, request=None):
        self.request = request
        self.created = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return True


@pytest.fixture
def audit_clients(monkeypatch):
    """Fixture that installs a DummyAuditClient and returns the list of created instances."""
    clients = []

    class LocalAuditClient:
        def __init__(self, request=None):
            self.request = request
            self.created = []
            clients.append(self)

        def create(self, **kwargs):
            self.created.append(kwargs)
            return True

    monkeypatch.setattr(iv, 'AuditClient', LocalAuditClient)
    return clients


class _DoesNotExist(Exception):
    pass


class DummyInvoice:
    DoesNotExist = _DoesNotExist

    class _mgr:
        def __init__(self, obj=None, exc=None):
            self._obj = obj
            self._exc = exc

        def get(self, id_invoice=None):
            if self._exc:
                raise self._exc
            return self._obj

    objects = _mgr()


def make_request(monkeypatch, user_payload=None, invoice_obj=None, requests_get=None, invoice_get_exc=None):
    """Helper to build request and apply common monkeypatches."""
    # Patch JWTAuthentication.authenticate with a minimal class
    def fake_authenticate(req):
        if user_payload is None:
            return None
        return (user_payload.get('user'), user_payload.get('payload'))

    class FakeJWTAuth:
        def authenticate(self, request):
            return fake_authenticate(request)

    monkeypatch.setattr(iv, 'JWTAuthentication', FakeJWTAuth)

    # AuditClient is provided by the optional fixture `audit_clients` when needed

    # Patch Invoice.objects.get behavior
    if invoice_get_exc is not None:
        DummyInvoice.objects = DummyInvoice._mgr(obj=None, exc=invoice_get_exc)
    else:
        DummyInvoice.objects = DummyInvoice._mgr(obj=invoice_obj, exc=None)
    monkeypatch.setattr(iv, 'Invoice', DummyInvoice)

    # Patch requests.get used when invoice.invoice_pdf_url exists
    if requests_get is not None:
            class FakeRequests:
                @staticmethod
                def get(url, timeout=30):
                    return requests_get(url, timeout=timeout)

                RequestException = requests.exceptions.RequestException

            monkeypatch.setattr(iv, 'requests', FakeRequests)

    factory = RequestFactory()
    request = factory.get(f'/invoices/{getattr(invoice_obj, "id_invoice", 7)}/download_pdf/')
    return request


def test_download_pdf_success(monkeypatch, audit_clients):
    # Arrange: user with permission 161
    user = SimpleNamespace(id=1, username='tester', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    # Fake invoice object
    class FI:
        id_invoice = 7
        status_id = iv.InvoiceViewSet.VALIDADA
        invoice_pdf_url = 'https://storage.example/f.pdf'
        reference_code = 'REF123'
        cufe = None
        invoice_number = None
        customer = None
        amount_to_pay = 123.45
        invoice_date = None

    pdf_bytes = b'%PDF-1.4 mock pdf content'

    class MockResp:
        def __init__(self, content):
            self.content = content
            self.status_code = 200

        def raise_for_status(self):
            return None

    def mock_requests_get(url, timeout=30):
        return MockResp(pdf_bytes)

    # Clear audit list and make request
    audit_clients.clear()
    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FI(), requests_get=mock_requests_get)

    # Act
    response = iv.download_invoice_pdf(request, 7)

    # Assert
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert b'%PDF-1.4 mock pdf content' in response.content
    assert 'Content-Disposition' in response
    assert 'factura_REF123.pdf' in response['Content-Disposition']
    # Content-Length header must match
    assert int(response['Content-Length']) == len(pdf_bytes)

    # Audit: ensure an audit record was created with expected fields
    assert audit_clients, "AuditClient was not instantiated"
    audit_instance = audit_clients[-1]
    assert audit_instance.created, "AuditClient.create was not called"
    audit_call = audit_instance.created[-1]
    assert audit_call.get('permission_id') == iv.PERM_INVOICE_DOWNLOAD
    assert audit_call.get('object_id') == str(7)
    assert 'actor_id' in audit_call and 'actor_name' in audit_call


def test_download_pdf_no_permission(monkeypatch):
    # Arrange: user without the download permission
    user = SimpleNamespace(id=2, username='noperm', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': 999}]}]}
    user_payload = {'user': user, 'payload': payload}

    # Fake invoice object (should not be reached)
    class FI:
        id_invoice = 8
        status_id = iv.InvoiceViewSet.VALIDADA
        invoice_pdf_url = 'https://storage.example/f2.pdf'
        reference_code = 'REF456'

    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FI())

    # Act
    response = iv.download_invoice_pdf(request, 8)

    # Assert
    assert response.status_code == 403
    assert b'No tiene permisos para descargar facturas' in response.content


def test_download_pdf_invoice_not_found(monkeypatch):
    # Arrange: valid user with permission but invoice does not exist
    user = SimpleNamespace(id=3, username='tester3', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=None, invoice_get_exc=DummyInvoice.DoesNotExist())

    # Act
    response = iv.download_invoice_pdf(request, 9999)

    # Assert
    assert response.status_code == 404
    assert b'Factura no encontrada' in response.content


def test_download_pdf_status_not_ready(monkeypatch):
    # status not ENVIADA or VALIDADA -> 400
    user = SimpleNamespace(id=5, username='tester5', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    class FI2:
        id_invoice = 10
        status_id = iv.InvoiceViewSet.BORRADOR
        invoice_pdf_url = 'https://storage.example/ignored.pdf'
        reference_code = 'REF-NOT-READY'

    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FI2())
    response = iv.download_invoice_pdf(request, 10)
    assert response.status_code == 400
    assert b'Factura no lista para descarga' in response.content


def test_download_pdf_storage_error(monkeypatch):
    # Arrange: valid user with permission but requests.get raises
    user = SimpleNamespace(id=4, username='tester4', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    class FI:
        id_invoice = 9
        status_id = iv.InvoiceViewSet.VALIDADA
        invoice_pdf_url = 'https://storage.example/fail.pdf'
        reference_code = 'REF789'

    def mock_requests_get_error(url, timeout=30):
        raise iv.requests.RequestException('network error')

    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FI(), requests_get=mock_requests_get_error)

    # Act
    response = iv.download_invoice_pdf(request, 9)

    # Assert
    assert response.status_code == 502
    assert b'Error al descargar desde almacenamiento' in response.content


def test_download_pdf_no_pdf_available(monkeypatch):
    # Invoice with no pdf url and no cufe -> 404
    user = SimpleNamespace(id=6, username='tester6', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    class FI3:
        id_invoice = 11
        status_id = iv.InvoiceViewSet.VALIDADA
        invoice_pdf_url = None
        cufe = None
        reference_code = 'REF-NOPDF'

    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FI3())
    response = iv.download_invoice_pdf(request, 11)
    assert response.status_code == 404
    assert b'No hay PDF disponible' in response.content


def test_download_pdf_via_cufe_success(monkeypatch, audit_clients):
    # Arrange: user with permission, invoice has no firebase url but has CUFE
    user = SimpleNamespace(id=20, username='cufeuser', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    class FIc:
        id_invoice = 21
        status_id = iv.InvoiceViewSet.VALIDADA
        invoice_pdf_url = None
        cufe = 'CUFE-XYZ'
        reference_code = 'REF-CUFE'

    pdf_bytes = b'%PDF-CUFE'

    class FakeFactus:
        def __init__(self):
            pass

        def get_invoice_pdf(self, cufe):
            assert cufe == 'CUFE-XYZ'
            return pdf_bytes, f'factura_{FIc.reference_code}.pdf'

    # install factus service mock
    monkeypatch.setattr(iv, 'FactusService', FakeFactus)

    # Clear audit and run
    audit_clients.clear()
    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FIc())

    # Act
    response = iv.download_invoice_pdf(request, 21)

    # Assert
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert pdf_bytes in response.content
    assert 'Content-Disposition' in response
    assert 'factura_REF-CUFE.pdf' in response['Content-Disposition']

    # Audit
    assert audit_clients, "AuditClient was not instantiated for CUFE path"
    ai = audit_clients[-1]
    assert ai.created and ai.created[-1].get('permission_id') == iv.PERM_INVOICE_DOWNLOAD


def test_download_pdf_empty_pdf_and_no_audit(monkeypatch, audit_clients):
    # Simulate empty pdf content -> treated as PDF vacío -> 500
    user = SimpleNamespace(id=7, username='tester7', is_authenticated=True)
    payload = {'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}]}
    user_payload = {'user': user, 'payload': payload}

    class FI4:
        id_invoice = 12
        status_id = iv.InvoiceViewSet.VALIDADA
        invoice_pdf_url = 'https://storage.example/empty.pdf'
        reference_code = 'REF-EMPTY'

    def mock_empty_get(url, timeout=30):
        class R:
            content = b''
            status_code = 200

            def raise_for_status(self):
                return None

        return R()

    # Clear audit clients
    audit_clients.clear()
    request = make_request(monkeypatch, user_payload=user_payload, invoice_obj=FI4(), requests_get=mock_empty_get)
    response = iv.download_invoice_pdf(request, 12)
    assert response.status_code == 500
    assert b'Error interno' in response.content
    # Audit should not have been created because PDF empty prevents audit step
    assert not audit_clients or all(len(ci.created) == 0 for ci in audit_clients)


@pytest.mark.django_db
def test_download_pdf_integration_api_client(monkeypatch, audit_clients):
    """Integration-like test: create DB invoice, use real JWT and APIClient, but patch external requests and AuditClient."""
    # Create minimal DB state (similar to other UT-SOL tests)
    from users.models.user import User
    from parameterization.models.statues_category import StatuesCategory
    from parameterization.models.statues import Statues
    from service_requests.models import Customer, TaxRegime, PersonType
    from django.utils import timezone

    now = timezone.now()
    # User
    user, _ = User.objects.get_or_create(id_user=1000)
    user.id = user.id_user
    user.is_authenticated = True

    # Statues category and statuses
    stat_cat, _ = StatuesCategory.objects.get_or_create(
        id_statues_categories=99,
        defaults={
            'name': 'test', 'description': 'test', 'modification_date': now, 'creation_date': now, 'id_responsible_user': user
        }
    )
    status_validada, _ = Statues.objects.get_or_create(
        id_statues=iv.InvoiceViewSet.VALIDADA,
        defaults={
            'name': 'VALIDADA', 'description': 'Validada', 'id_statues_categories': stat_cat, 'modification_date': now, 'creation_date': now, 'id_responsible_user': user
        }
    )

    # Tax regime and person type
    person_type, _ = PersonType.objects.get_or_create(id_person_type=1, defaults={'name': 'NATURAL'})
    tax_regime, _ = TaxRegime.objects.get_or_create(id_tax_regime=1, defaults={'name': 'COMUN'})

    # Customer
    cust, _ = Customer.objects.get_or_create(
        id_user=user,
        document_number=999999,
        defaults={
            'person_type': person_type,
            'legal_entity_name': 'TestCo',
            'name': 'Test',
            'first_last_name': 'User',
            'id_municipality': 1,
            'tax_regime': tax_regime,
            'customer_statues': status_validada,
            'creation_date': now,
            'modification_date': now,
            'id_responsible_user': user,
            'email': 'test@example.com'
        }
    )

    # Invoice
    from service_requests.models.invoice import Invoice

    invoice = Invoice.objects.create(
        customer=cust,
        tax_regime=tax_regime,
        reference_code='REF-INTEGRATION',
        status=status_validada,
        invoice_pdf_url='https://storage.example/integration.pdf'
    )

    # Patch external requests.get and AuditClient
    pdf_bytes = b'%PDF-integration'

    def mock_get(url, timeout=30):
        class R:
            content = pdf_bytes
            status_code = 200

            def raise_for_status(self):
                return None

        return R()

    monkeypatch.setattr(iv, 'requests', SimpleNamespace(get=mock_get, RequestException=requests.exceptions.RequestException))
    # ensure audit fixture list is empty for this test
    audit_clients.clear()

    # Create JWT
    JWT_TEST_SECRET = os.environ.get('JWT_SECRET', 'testsecret')
    claims = {
        'id': user.id,
        'email': getattr(user, 'email', 'test@example.com'),
        'name': getattr(user, 'first_name', 'Tester'),
        'rol': [{'permisos': [{'id': iv.PERM_INVOICE_DOWNLOAD}]}],
    }
    now_dt = datetime.utcnow()
    claims['iat'] = int(now_dt.timestamp())
    claims['exp'] = int((now_dt + timedelta(minutes=30)).timestamp())
    token = jwt.encode(claims, JWT_TEST_SECRET, algorithm='HS256')

    client = APIClient()
    headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

    resp = client.get(f'/invoices/{invoice.id_invoice}/download_pdf/', **headers)
    assert resp.status_code == 200
    assert resp['Content-Disposition'] and 'REF-INTEGRATION' in resp['Content-Disposition']
    assert int(resp['Content-Length']) == len(pdf_bytes)
    # Check audit
    assert audit_clients, "AuditClient not used in integration test"
    ai = audit_clients[-1]
    assert ai.created and ai.created[-1].get('permission_id') == iv.PERM_INVOICE_DOWNLOAD
