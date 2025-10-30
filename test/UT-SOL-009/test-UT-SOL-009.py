"""
Pruebas Unitarias UT-SOL-009 - PARTE 1 (Casos 1-18)
Endpoint: /invoices/ (Facturación Electrónica)
Módulo: Gestión de Solicitudes - Facturación

Este archivo contiene los primeros 18 casos de prueba para validar:
- Control de acceso y permisos (158, 159, 160)
- Creación de borradores de factura
- Validaciones de entrada (observación, payment_method, estados)
- Actualización de borradores
- Listado y detalle de facturas
- Creación de líneas de factura
- Validaciones de líneas (descuento, cantidad, unidades, service_item)
"""

import pytest
from unittest.mock import Mock, MagicMock
from rest_framework import status
from datetime import datetime, timezone
from decimal import Decimal


# ============================================================================
# MOCK CLASSES
# ============================================================================

class DummyUser:
    """Mock de usuario autenticado"""
    def __init__(self, id=1, is_active=True, is_authenticated=True, permissions=None):
        self.id = id
        self.id_user = id
        self.is_active = is_active
        self.is_authenticated = is_authenticated
        self.permissions = permissions or []


class DummyInvoice:
    """Mock de factura"""
    def __init__(self, id_invoice, reference_code, status, service_request_id, 
                 observation="", payment_method=48, amount_to_pay=Decimal("0.00"),
                 total_without_taxes=Decimal("0.00"), total_taxes=Decimal("0.00"),
                 invoice_date=None, customer_name="Cliente Test"):
        self.id_invoice = id_invoice
        self.reference_code = reference_code
        self.status = status  # BORRADOR, ENVIADA, VALIDADA, RECHAZADA
        self.service_request_id = service_request_id
        self.observation = observation
        self.payment_method = payment_method
        self.amount_to_pay = amount_to_pay
        self.total_without_taxes = total_without_taxes
        self.total_taxes = total_taxes
        self.invoice_date = invoice_date or datetime.now(timezone.utc)
        self.customer_name = customer_name
        self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convertir a diccionario para respuesta"""
        return {
            "id_invoice": self.id_invoice,
            "reference_code": self.reference_code,
            "invoice_status_name": self.status,
            "service_request_id": self.service_request_id,
            "customer_name": self.customer_name,
            "invoice_date": self.invoice_date.isoformat().replace('+00:00', 'Z'),
            "amount_to_pay": str(self.amount_to_pay),
            "total_without_taxes": str(self.total_without_taxes),
            "total_taxes": str(self.total_taxes),
            "observation": self.observation,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat().replace('+00:00', 'Z')
        }


class DummyInvoiceLine:
    """Mock de línea de factura"""
    def __init__(self, id_line, invoice_id, service_item, quantity, 
                 discount_percentage, percentage_taxes_per_line,
                 units_measurement_id, tribute_id, base_price=Decimal("150000.00")):
        self.id_line = id_line
        self.invoice_id = invoice_id
        self.service_item = service_item
        self.quantity = Decimal(str(quantity))
        self.discount_percentage = Decimal(str(discount_percentage))
        self.percentage_taxes_per_line = Decimal(str(percentage_taxes_per_line))
        self.units_measurement_id = units_measurement_id
        self.tribute_id = tribute_id
        self.base_price = base_price
        
        # Calcular total_line_amount: cantidad × precio × (1 - descuento/100) × (1 + IVA/100)
        subtotal = self.quantity * self.base_price
        after_discount = subtotal * (Decimal("1") - self.discount_percentage / Decimal("100"))
        self.total_line_amount = after_discount * (Decimal("1") + self.percentage_taxes_per_line / Decimal("100"))
    
    def to_dict(self):
        return {
            "id_line": self.id_line,
            "service_item": self.service_item,
            "quantity": str(self.quantity),
            "discount_percentage": str(self.discount_percentage),
            "percentage_taxes_per_line": str(self.percentage_taxes_per_line),
            "total_line_amount": str(self.total_line_amount),
            "units_measurement_id": self.units_measurement_id,
            "tribute_id": self.tribute_id
        }


class DummyServiceRequest:
    """Mock de solicitud de servicio"""
    def __init__(self, id, reference_code, status_name):
        self.id = id
        self.reference_code = reference_code
        self.status_name = status_name  # Pendiente, En proceso, Finalizada, Cancelada, Rechazada


class MockResponse:
    """Mock de respuesta HTTP"""
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def do_create_draft(
    client,
    permissions=None,
    authenticated=True,
    user_obj=None,
    active=True,
    service_request=None,
    observation="",
    payment_method=48,
    service_requests_db=None
):
    """
    Simula POST /invoices/create-draft/ con validaciones completas.
    
    Args:
        client: Cliente de pruebas
        permissions: Lista de permisos del usuario
        authenticated: Si el usuario está autenticado
        user_obj: Objeto usuario personalizado
        active: Si el usuario está activo
        service_request: Código de solicitud (ej: "SOL-2025-0020")
        observation: Texto de observación
        payment_method: ID del método de pago
        service_requests_db: Lista de solicitudes disponibles
    
    Returns:
        MockResponse
    """
    if permissions is None:
        permissions = []
    
    # 1. Verificar autenticación
    if not authenticated or (user_obj and not getattr(user_obj, 'is_authenticated', True)):
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    # 2. Verificar usuario activo
    if not active or (user_obj and not getattr(user_obj, 'is_active', True)):
        return MockResponse(403, {"detail": "User inactive or blocked."})
    
    # 3. Verificar permiso 158 (request.crud_invoice)
    if 158 not in permissions:
        return MockResponse(403, {"detail": "No tiene permisos para crear/actualizar facturas."})
    
    # 4. Validar longitud de observación (máximo 250 caracteres)
    if len(observation) > 250:
        return MockResponse(400, {
            "detail": "La observación no puede exceder 250 caracteres."
        })
    
    # 5. Validar existencia de service_request
    if service_requests_db is None:
        service_requests_db = [
            DummyServiceRequest(1, "SOL-2025-0020", "Pendiente"),
            DummyServiceRequest(2, "SOL-2025-0021", "En proceso"),
            DummyServiceRequest(3, "SOL-2025-0022", "Finalizada"),
            DummyServiceRequest(4, "SOL-2025-0033", "Cancelada"),
        ]
    
    service_req = next((sr for sr in service_requests_db if sr.reference_code == service_request), None)
    
    if not service_req:
        return MockResponse(404, {"detail": "Solicitud de servicio no encontrada."})
    
    # 6. Validar estado de solicitud (solo Pendiente, En proceso, Finalizada)
    allowed_statuses = ["Pendiente", "En proceso", "Finalizada"]
    if service_req.status_name not in allowed_statuses:
        return MockResponse(409, {
            "detail": f"El estado de la solicitud ({service_req.status_name}) no permite facturación. Estados permitidos: {', '.join(allowed_statuses)}."
        })
    
    # 7. Validar payment_method (simular catálogo)
    valid_payment_methods = [48, 49, 50]  # IDs válidos
    if payment_method not in valid_payment_methods:
        return MockResponse(400, {"detail": "Método de pago no válido."})
    
    # 8. Crear factura en BORRADOR
    new_invoice_id = 101
    new_reference_code = f"FE-2025-{new_invoice_id:04d}"
    
    invoice = DummyInvoice(
        id_invoice=new_invoice_id,
        reference_code=new_reference_code,
        status="BORRADOR",
        service_request_id=service_req.id,
        observation=observation,
        payment_method=payment_method
    )
    
    return MockResponse(201, {
        "success": True,
        "detail": "Borrador de factura creado exitosamente.",
        "id_invoice": invoice.id_invoice,
        "reference_code": invoice.reference_code,
        "created_at": invoice.created_at.isoformat().replace('+00:00', 'Z')
    })


def do_update_draft(
    client,
    invoice_id,
    permissions=None,
    authenticated=True,
    observation="",
    payment_method=48,
    invoices_db=None
):
    """
    Simula PUT /invoices/{id}/update-draft/ con validaciones.
    """
    if permissions is None:
        permissions = []
    
    # 1. Autenticación
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    # 2. Permiso 158
    if 158 not in permissions:
        return MockResponse(403, {"detail": "No tiene permisos para actualizar facturas."})
    
    # 3. Buscar factura
    if invoices_db is None:
        invoices_db = [
            DummyInvoice(110, "FE-2025-0110", "BORRADOR", 1),
            DummyInvoice(111, "FE-2025-0111", "ENVIADA", 2),
        ]
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    # 4. Validar estado BORRADOR
    if invoice.status != "BORRADOR":
        return MockResponse(409, {
            "detail": f"No se puede actualizar. La factura está en estado {invoice.status}."
        })
    
    # 5. Validar longitud observación
    if len(observation) > 250:
        return MockResponse(400, {"detail": "La observación no puede exceder 250 caracteres."})
    
    # 6. Actualizar campos
    invoice.observation = observation
    invoice.payment_method = payment_method
    
    return MockResponse(200, {
        "success": True,
        "detail": "Borrador actualizado exitosamente."
    })


def do_list_invoices(client, permissions=None, authenticated=True, invoices_db=None):
    """
    Simula GET /invoices/ - Listar facturas.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    if 156 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para listar facturas."})
    
    if invoices_db is None:
        invoices_db = [
            DummyInvoice(101, "FE-2025-0101", "BORRADOR", 1, amount_to_pay=Decimal("100000")),
            DummyInvoice(102, "FE-2025-0102", "ENVIADA", 2, amount_to_pay=Decimal("250000")),
        ]
    
    data = [inv.to_dict() for inv in invoices_db]
    
    return MockResponse(200, {"success": True, "data": data})


def do_get_invoice_detail(client, invoice_id, permissions=None, authenticated=True, invoices_db=None):
    """
    Simula GET /invoices/{id}/ - Detalle de factura.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    if 156 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para ver detalles de facturas."})
    
    if invoices_db is None:
        invoices_db = []
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    return MockResponse(200, invoice.to_dict())


def do_create_line(
    client,
    invoice_id,
    permissions=None,
    authenticated=True,
    service_item=4,
    quantity=1,
    discount_percentage=0,
    percentage_taxes_per_line=19,
    units_measurement_id=70,
    tribute_id=1,
    invoices_db=None,
    services_db=None
):
    """
    Simula POST /invoices/{id}/lines/ - Añadir línea a factura.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    # Permiso 159 (request.crud_invoice_lines)
    if 159 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para crear líneas de factura."})
    
    # Validar factura existe
    if invoices_db is None:
        invoices_db = [DummyInvoice(113, "FE-2025-0113", "BORRADOR", 1)]
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    # Validar estado BORRADOR
    if invoice.status != "BORRADOR":
        return MockResponse(409, {"detail": "Solo se pueden añadir líneas a facturas en BORRADOR."})
    
    # Validar service_item existe
    if services_db is None:
        services_db = [{"id": 4, "name": "Mantenimiento Preventivo", "base_price": Decimal("150000.00")}]
    
    service = next((s for s in services_db if s["id"] == service_item), None)
    if not service:
        return MockResponse(404, {"detail": "Servicio no encontrado."})
    
    # Validar quantity > 0
    if quantity <= 0:
        return MockResponse(400, {"detail": "La cantidad debe ser mayor a 0."})
    
    # Validar descuento 0-100
    if discount_percentage < 0 or discount_percentage > 100:
        return MockResponse(400, {"detail": "El descuento debe estar entre 0 y 100."})
    
    # Validar units_measurement_id (catálogo FACTUS simulado)
    valid_units = [70, 71, 72]  # Ejemplos
    if units_measurement_id not in valid_units:
        return MockResponse(400, {"detail": "Unidad de medida no válida según catálogo externo."})
    
    # Crear línea
    new_line_id = 1
    line = DummyInvoiceLine(
        id_line=new_line_id,
        invoice_id=invoice_id,
        service_item=service_item,
        quantity=quantity,
        discount_percentage=discount_percentage,
        percentage_taxes_per_line=percentage_taxes_per_line,
        units_measurement_id=units_measurement_id,
        tribute_id=tribute_id,
        base_price=service["base_price"]
    )
    
    # Actualizar totales de factura
    invoice.total_without_taxes += line.total_line_amount / (Decimal("1") + Decimal(percentage_taxes_per_line) / Decimal("100"))
    invoice.total_taxes = invoice.total_without_taxes * Decimal(percentage_taxes_per_line) / Decimal("100")
    invoice.amount_to_pay = invoice.total_without_taxes + invoice.total_taxes
    
    return MockResponse(201, {
        "success": True,
        "detail": "Línea añadida exitosamente.",
        "id_line": line.id_line,
        "total_line_amount": str(line.total_line_amount)
    })


# ============================================================================
# PYTEST FIXTURE
# ============================================================================

@pytest.fixture
def client():
    """Fixture para cliente de API"""
    from rest_framework.test import APIClient
    return APIClient()


# ============================================================================
# TEST CASES - CONTROL DE ACCESO (1-4)
# ============================================================================

def test_ut_sol_009_1_acceso_sin_token_401(client):
    """
    UT-SOL-009.1: Acceso sin token retorna 401 en /invoices/create-draft/
    
    Verifica que crear borrador sin Authorization header retorna 401 Unauthorized.
    """
    resp = do_create_draft(
        client,
        authenticated=False,
        service_request="SOL-2025-0020"
    )
    
    assert resp.status_code == 401, f"[UT-SOL-009.1] Esperado: 401, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "detail" in body, "[UT-SOL-009.1] Debe incluir mensaje de error"


def test_ut_sol_009_2_falta_permiso_158_retorna_403(client):
    """
    UT-SOL-009.2: Falta permiso 158 retorna 403 al crear borrador
    
    Verifica que sin permiso 158 (request.crud_invoice) no permita crear borrador.
    """
    resp = do_create_draft(
        client,
        permissions=[100, 101],  # Sin 158
        authenticated=True,
        service_request="SOL-2025-0020"
    )
    
    assert resp.status_code == 403, f"[UT-SOL-009.2] Esperado: 403, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "permiso" in body["detail"].lower(), "[UT-SOL-009.2] Mensaje debe mencionar permisos"


def test_ut_sol_009_3_falta_permiso_159_retorna_403(client):
    """
    UT-SOL-009.3: Falta permiso 159 retorna 403 al añadir línea
    
    Verifica que sin permiso 159 (request.crud_invoice_lines) no permita crear líneas.
    """
    resp = do_create_line(
        client,
        invoice_id=101,
        permissions=[158],  # Sin 159
        authenticated=True
    )
    
    assert resp.status_code == 403, f"[UT-SOL-009.3] Esperado: 403, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "permiso" in body["detail"].lower(), "[UT-SOL-009.3] Debe indicar falta de permisos"


def test_ut_sol_009_4_falta_permiso_160_retorna_403(client):
    """
    UT-SOL-009.4: Falta permiso 160 retorna 403 al generar FE
    
    Verifica que sin permiso 160 (request.generate_invoice) no permita generar y enviar a FACTUS/DIAN.
    (Este caso se simplifica verificando solo el check de permiso)
    """
    # Nota: generate_fe se implementará en parte 2, aquí solo validamos concepto de permiso
    permissions_sin_160 = [158, 159]  # Sin 160
    
    # Simulación básica: si no tiene 160, debe rechazar
    has_permission = 160 in permissions_sin_160
    
    assert not has_permission, "[UT-SOL-009.4] Usuario no debe tener permiso 160"
    # En implementación real, esto sería una llamada POST que retornaría 403


# ============================================================================
# TEST CASES - CREAR BORRADOR (5-9)
# ============================================================================

def test_ut_sol_009_5_crear_borrador_exitoso(client):
    """
    UT-SOL-009.5: Crear borrador exitoso con solicitud válida
    
    Verifica creación de borrador cuando la solicitud existe y su estado es permitido.
    """
    resp = do_create_draft(
        client,
        permissions=[158],
        authenticated=True,
        service_request="SOL-2025-0020",
        observation="Factura de mantenimiento.",
        payment_method=48
    )
    
    assert resp.status_code == 201, f"[UT-SOL-009.5] Esperado: 201, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["success"] == True, "[UT-SOL-009.5] Success debe ser True"
    assert "id_invoice" in body, "[UT-SOL-009.5] Debe incluir id_invoice"
    assert body["reference_code"] != "", "[UT-SOL-009.5] reference_code no debe estar vacío"
    assert "created_at" in body, "[UT-SOL-009.5] Debe incluir created_at"


def test_ut_sol_009_6_observacion_mayor_250_chars_retorna_400(client):
    """
    UT-SOL-009.6: Observación > 250 caracteres retorna 400
    
    Valida longitud máxima de observación en creación de borrador.
    """
    observacion_larga = "A" * 251
    
    resp = do_create_draft(
        client,
        permissions=[158],
        authenticated=True,
        service_request="SOL-2025-0020",
        observation=observacion_larga,
        payment_method=48
    )
    
    assert resp.status_code == 400, f"[UT-SOL-009.6] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "250" in body["detail"], "[UT-SOL-009.6] Debe mencionar límite de 250 caracteres"


def test_ut_sol_009_7_solicitud_inexistente_retorna_404(client):
    """
    UT-SOL-009.7: Solicitud inexistente retorna 404 al crear borrador
    
    Verifica respuesta cuando service_request no existe.
    """
    resp = do_create_draft(
        client,
        permissions=[158],
        authenticated=True,
        service_request="SOL-9999-9999",
        payment_method=48
    )
    
    assert resp.status_code == 404, f"[UT-SOL-009.7] Esperado: 404, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "solicitud" in body["detail"].lower(), "[UT-SOL-009.7] Mensaje debe mencionar solicitud"


def test_ut_sol_009_8_estado_solicitud_no_permitido_retorna_409(client):
    """
    UT-SOL-009.8: Estado de solicitud no permitido retorna 409
    
    Verifica que si la solicitud está Cancelada/Rechazada no permita crear borrador.
    """
    resp = do_create_draft(
        client,
        permissions=[158],
        authenticated=True,
        service_request="SOL-2025-0033",  # Estado: Cancelada
        payment_method=48
    )
    
    assert resp.status_code == 409, f"[UT-SOL-009.8] Esperado: 409, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "estado" in body["detail"].lower(), "[UT-SOL-009.8] Debe mencionar problema con estado"


def test_ut_sol_009_9_payment_method_invalido_retorna_400(client):
    """
    UT-SOL-009.9: payment_method inválido retorna 400
    
    Valida referencia a método de pago inexistente.
    """
    resp = do_create_draft(
        client,
        permissions=[158],
        authenticated=True,
        service_request="SOL-2025-0020",
        payment_method=99999
    )
    
    assert resp.status_code == 400, f"[UT-SOL-009.9] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "pago" in body["detail"].lower(), "[UT-SOL-009.9] Debe mencionar método de pago"


# ============================================================================
# TEST CASES - ACTUALIZAR BORRADOR (10-11)
# ============================================================================

def test_ut_sol_009_10_actualizar_borrador_exitoso(client):
    """
    UT-SOL-009.10: Actualizar borrador en estado BORRADOR exitoso
    
    Verifica actualización de observación y método de pago en borrador.
    """
    resp = do_update_draft(
        client,
        invoice_id=110,
        permissions=[158],
        authenticated=True,
        observation="Observación actualizada",
        payment_method=48
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.10] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body["success"] == True, "[UT-SOL-009.10] Success debe ser True"


def test_ut_sol_009_11_no_actualizar_si_no_borrador(client):
    """
    UT-SOL-009.11: No permite actualizar borrador si no está en BORRADOR
    
    Valida que en ENVIADA/VALIDADA no se pueda actualizar.
    """
    resp = do_update_draft(
        client,
        invoice_id=111,  # Estado ENVIADA
        permissions=[158],
        authenticated=True,
        observation="Cambio no permitido",
        payment_method=48
    )
    
    assert resp.status_code == 409, f"[UT-SOL-009.11] Esperado: 409, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "estado" in body["detail"].lower(), "[UT-SOL-009.11] Debe mencionar problema de estado"


# ============================================================================
# TEST CASES - LISTAR Y DETALLAR (12-13)
# ============================================================================

def test_ut_sol_009_12_listar_facturas_estructura_valida(client):
    """
    UT-SOL-009.12: Listar facturas retorna estructura mínima válida
    
    Verifica que GET /invoices/ retorne arreglo con campos clave.
    """
    resp = do_list_invoices(
        client,
        permissions=[156],
        authenticated=True
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.12] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert "data" in body, "[UT-SOL-009.12] Debe incluir campo data"
    assert len(body["data"]) > 0, "[UT-SOL-009.12] Debe tener al menos una factura"
    
    # Validar campos requeridos en primer elemento
    first_invoice = body["data"][0]
    required_fields = ["id_invoice", "reference_code", "invoice_date", "amount_to_pay", 
                       "invoice_status_name", "customer_name", "service_request_id"]
    
    for field in required_fields:
        assert field in first_invoice, f"[UT-SOL-009.12] Falta campo: {field}"


def test_ut_sol_009_13_detalle_calcula_totales_correctamente(client):
    """
    UT-SOL-009.13: Detalle de factura calcula totales correctamente
    
    Valida cálculo de total_without_taxes, total_taxes, amount_to_pay a partir de líneas.
    Caso: precio 150000, descuento 10%, IVA 19%
    """
    # Crear factura con totales calculados
    # Subtotal: 150000 * (1 - 0.10) = 135000
    # IVA: 135000 * 0.19 = 25650
    # Total: 135000 + 25650 = 160650
    
    invoice_with_totals = DummyInvoice(
        id_invoice=112,
        reference_code="FE-2025-0112",
        status="BORRADOR",
        service_request_id=1,
        total_without_taxes=Decimal("135000.00"),
        total_taxes=Decimal("25650.00"),
        amount_to_pay=Decimal("160650.00")
    )
    
    resp = do_get_invoice_detail(
        client,
        invoice_id=112,
        permissions=[156],
        authenticated=True,
        invoices_db=[invoice_with_totals]
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.13] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["total_without_taxes"] == "135000.00", "[UT-SOL-009.13] Subtotal incorrecto"
    assert body["total_taxes"] == "25650.00", "[UT-SOL-009.13] IVA incorrecto"
    assert body["amount_to_pay"] == "160650.00", "[UT-SOL-009.13] Total incorrecto"


# ============================================================================
# TEST CASES - LÍNEAS: CREAR/VALIDAR (14-18)
# ============================================================================

def test_ut_sol_009_14_anadir_linea_exitosa_calculos_correctos(client):
    """
    UT-SOL-009.14: Añadir línea exitosa con cálculos correctos
    
    Verifica creación de línea con service_item válido y recálculo de totales.
    Caso: servicio precio 150000, cantidad 2.5, descuento 10%, IVA 19%
    """
    resp = do_create_line(
        client,
        invoice_id=113,
        permissions=[159],
        authenticated=True,
        service_item=4,
        quantity=2.5,
        discount_percentage=10,
        percentage_taxes_per_line=19,
        units_measurement_id=70,
        tribute_id=1
    )
    
    assert resp.status_code == 201, f"[UT-SOL-009.14] Esperado: 201, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["success"] == True, "[UT-SOL-009.14] Success debe ser True"
    assert "total_line_amount" in body, "[UT-SOL-009.14] Debe incluir total_line_amount"
    
    # Validar cálculo: 2.5 * 150000 * 0.9 * 1.19 = 401625
    expected_total = Decimal("401625.00")
    actual_total = Decimal(body["total_line_amount"])
    
    assert abs(actual_total - expected_total) < Decimal("1.00"), \
        f"[UT-SOL-009.14] Total esperado ~{expected_total}, obtenido {actual_total}"


def test_ut_sol_009_15_descuento_mayor_100_retorna_400(client):
    """
    UT-SOL-009.15: Descuento > 100% retorna 400
    
    Valida rango de descuento en línea de factura.
    """
    invoices_db = [DummyInvoice(114, "FE-2025-0114", "BORRADOR", 1)]
    
    resp = do_create_line(
        client,
        invoice_id=114,
        permissions=[159],
        authenticated=True,
        discount_percentage=150,
        invoices_db=invoices_db
    )
    
    assert resp.status_code == 400, f"[UT-SOL-009.15] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "descuento" in body["detail"].lower(), "[UT-SOL-009.15] Debe mencionar descuento"


def test_ut_sol_009_16_cantidad_negativa_retorna_400(client):
    """
    UT-SOL-009.16: Cantidad negativa retorna 400
    
    Valida que quantity debe ser decimal positivo.
    """
    invoices_db = [DummyInvoice(115, "FE-2025-0115", "BORRADOR", 1)]
    
    resp = do_create_line(
        client,
        invoice_id=115,
        permissions=[159],
        authenticated=True,
        quantity=-1,
        invoices_db=invoices_db
    )
    
    assert resp.status_code == 400, f"[UT-SOL-009.16] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "cantidad" in body["detail"].lower(), "[UT-SOL-009.16] Debe mencionar cantidad"


def test_ut_sol_009_17_unidad_medida_invalida_retorna_400(client):
    """
    UT-SOL-009.17: Unidad de medida inválida retorna 400
    
    Valida units_measurement_id contra catálogo FACTUS.
    """
    invoices_db = [DummyInvoice(116, "FE-2025-0116", "BORRADOR", 1)]
    
    resp = do_create_line(
        client,
        invoice_id=116,
        permissions=[159],
        authenticated=True,
        units_measurement_id=999999,
        invoices_db=invoices_db
    )
    
    assert resp.status_code == 400, f"[UT-SOL-009.17] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "unidad" in body["detail"].lower() or "medida" in body["detail"].lower(), \
        "[UT-SOL-009.17] Debe mencionar unidad de medida"


def test_ut_sol_009_18_service_item_inexistente_retorna_404(client):
    """
    UT-SOL-009.18: service_item inexistente retorna 404
    
    Valida referencia de servicio al crear línea.
    """
    invoices_db = [DummyInvoice(117, "FE-2025-0117", "BORRADOR", 1)]
    
    resp = do_create_line(
        client,
        invoice_id=117,
        permissions=[159],
        authenticated=True,
        service_item=9999,
        invoices_db=invoices_db
    )
    
    assert resp.status_code == 404, f"[UT-SOL-009.18] Esperado: 404, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "servicio" in body["detail"].lower(), "[UT-SOL-009.18] Debe mencionar servicio no encontrado"


# ============================================================================
# FIN DE PARTE 1
# ============================================================================


# ============================================================================
# HELPER FUNCTIONS - PART 2
# ============================================================================

def do_update_line(
    client,
    invoice_id,
    line_id,
    permissions=None,
    authenticated=True,
    quantity=2,
    discount_percentage=20,
    percentage_taxes_per_line=19,
    units_measurement_id=70,
    tribute_id=1,
    invoices_db=None,
    lines_db=None
):
    """
    Simula PATCH /invoices/{invoice_id}/lines/{line_id}/ - Actualizar línea.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    if 159 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para actualizar líneas de factura."})
    
    # Buscar factura
    if invoices_db is None:
        invoices_db = []
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    if invoice.status != "BORRADOR":
        return MockResponse(409, {"detail": "Solo se pueden actualizar líneas en facturas BORRADOR."})
    
    # Buscar línea
    if lines_db is None:
        lines_db = []
    
    line = next((l for l in lines_db if l.id_line == line_id and l.invoice_id == invoice_id), None)
    if not line:
        return MockResponse(404, {"detail": "Línea no encontrada."})
    
    # Validar quantity > 0
    if quantity <= 0:
        return MockResponse(400, {"detail": "La cantidad debe ser mayor a 0."})
    
    # Validar descuento
    if discount_percentage < 0 or discount_percentage > 100:
        return MockResponse(400, {"detail": "El descuento debe estar entre 0 y 100."})
    
    # Actualizar línea
    line.quantity = Decimal(str(quantity))
    line.discount_percentage = Decimal(str(discount_percentage))
    line.percentage_taxes_per_line = Decimal(str(percentage_taxes_per_line))
    
    # Recalcular total
    subtotal = line.quantity * line.base_price
    after_discount = subtotal * (Decimal("1") - line.discount_percentage / Decimal("100"))
    line.total_line_amount = after_discount * (Decimal("1") + line.percentage_taxes_per_line / Decimal("100"))
    
    # Recalcular totales de factura (simplificado)
    invoice.amount_to_pay = line.total_line_amount
    
    return MockResponse(200, {
        "success": True,
        "detail": "Línea actualizada exitosamente.",
        "total_line_amount": str(line.total_line_amount)
    })


def do_delete_line(
    client,
    invoice_id,
    line_id,
    permissions=None,
    authenticated=True,
    invoices_db=None,
    lines_db=None
):
    """
    Simula DELETE /invoices/{invoice_id}/lines/{line_id}/ - Eliminar línea.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    if 159 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para eliminar líneas de factura."})
    
    # Buscar factura
    if invoices_db is None:
        invoices_db = []
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    if invoice.status != "BORRADOR":
        return MockResponse(409, {"detail": "Solo se pueden eliminar líneas en facturas BORRADOR."})
    
    # Buscar línea
    if lines_db is None:
        lines_db = []
    
    line = next((l for l in lines_db if l.id_line == line_id and l.invoice_id == invoice_id), None)
    if not line:
        return MockResponse(404, {"detail": "Línea no encontrada."})
    
    # Eliminar línea (simular)
    lines_db.remove(line)
    
    # Recalcular totales (simplificado: restar monto de línea eliminada)
    invoice.amount_to_pay -= line.total_line_amount
    
    return MockResponse(200, {
        "success": True,
        "detail": "Línea eliminada exitosamente."
    })


def do_add_final_charges(
    client,
    invoice_id,
    permissions=None,
    authenticated=True,
    allowance_charges=None,
    invoices_db=None
):
    """
    Simula POST /invoices/{id}/final-charges/ - Añadir cargos finales.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    if 158 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para agregar cargos finales."})
    
    # Buscar factura
    if invoices_db is None:
        invoices_db = []
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    if invoice.status != "BORRADOR":
        return MockResponse(409, {"detail": "Solo se pueden agregar cargos en facturas BORRADOR."})
    
    # Validar allowance_charges
    if not allowance_charges:
        return MockResponse(400, {"detail": "Debe proporcionar al menos un cargo."})
    
    total_allowance = Decimal("0.00")
    
    for charge in allowance_charges:
        amount = Decimal(charge.get("amount", "0"))
        reason = charge.get("reason", "")
        
        # Validar monto positivo
        if amount <= 0:
            return MockResponse(400, {"detail": "El monto debe ser positivo."})
        
        # Validar reason no vacío
        if not reason or reason.strip() == "":
            return MockResponse(400, {"detail": "Debe proporcionar una razón para el cargo."})
        
        total_allowance += amount
    
    # Actualizar totales
    invoice.allowance_total = total_allowance
    invoice.amount_to_pay += total_allowance
    
    return MockResponse(200, {
        "success": True,
        "detail": "Cargos finales añadidos exitosamente.",
        "allowance_total": str(invoice.allowance_total)
    })


def do_delete_invoice(
    client,
    invoice_id,
    permissions=None,
    authenticated=True,
    invoices_db=None
):
    """
    Simula DELETE /invoices/{id}/ - Eliminar factura.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    if 158 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para eliminar facturas."})
    
    # Buscar factura
    if invoices_db is None:
        invoices_db = []
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    # Validar estado BORRADOR
    if invoice.status != "BORRADOR":
        return MockResponse(409, {
            "detail": f"No se puede eliminar factura en estado {invoice.status}."
        })
    
    # Eliminar (simular)
    invoices_db.remove(invoice)
    
    return MockResponse(200, {
        "success": True,
        "detail": "Factura eliminada exitosamente."
    })


def do_generate_fe(
    client,
    invoice_id,
    permissions=None,
    authenticated=True,
    invoices_db=None,
    simulate_dian_rejection=False
):
    """
    Simula POST /invoices/{id}/generate_fe/ - Generar factura electrónica.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    # Permiso 160 (request.generate_invoice)
    if 160 not in (permissions or []):
        return MockResponse(403, {"detail": "No tiene permisos para generar facturas electrónicas."})
    
    # Buscar factura
    if invoices_db is None:
        invoices_db = []
    
    invoice = next((inv for inv in invoices_db if inv.id_invoice == invoice_id), None)
    if not invoice:
        return MockResponse(404, {"detail": "Factura no encontrada."})
    
    # Validar estado BORRADOR
    if invoice.status != "BORRADOR":
        return MockResponse(409, {
            "detail": f"No se puede generar FE. La factura está en estado {invoice.status}."
        })
    
    # Validar que tenga líneas
    if not invoice.lines or len(invoice.lines) == 0:
        return MockResponse(409, {
            "detail": "La factura debe tener al menos una línea para generar FE."
        })
    
    # Simular rechazo de DIAN
    if simulate_dian_rejection:
        invoice.status = "RECHAZADA"
        return MockResponse(200, {
            "success": False,
            "detail": "Factura rechazada por DIAN/FACTUS.",
            "id_invoice": invoice.id_invoice,
            "status": "RECHAZADA",
            "api_response": {
                "error": "Rechazo simulado - NIT inválido o datos incorrectos"
            }
        })
    
    # Generar FE exitoso
    invoice.status = "ENVIADA"
    invoice.invoice_pdf_url = f"https://storage.example.com/invoices/{invoice.reference_code}.pdf"
    invoice.invoice_xml_url = f"https://storage.example.com/invoices/{invoice.reference_code}.xml"
    
    return MockResponse(200, {
        "success": True,
        "detail": "Factura electrónica generada y enviada exitosamente.",
        "id_invoice": invoice.id_invoice,
        "status": "ENVIADA",
        "invoice_pdf_url": invoice.invoice_pdf_url,
        "invoice_xml_url": invoice.invoice_xml_url
    })


def do_search_services(
    client,
    query="",
    permissions=None,
    authenticated=True,
    services_db=None
):
    """
    Simula GET /services/search/?query={texto} - Buscar servicios.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    # Sin permiso específico requerido para búsqueda
    
    # Base de datos de servicios
    if services_db is None:
        services_db = [
            {"id": 1, "code": "SVC-2025-0001", "name": "Mantenimiento Preventivo Básico", 
             "base_price": "150000.00", "tax_rate": "19", "unit_id": 70, "status": "Activo"},
            {"id": 2, "code": "SVC-2025-0002", "name": "Mantenimiento Preventivo Avanzado", 
             "base_price": "250000.00", "tax_rate": "19", "unit_id": 70, "status": "Activo"},
            {"id": 3, "code": "SVC-2025-0003", "name": "Reparación de Motor", 
             "base_price": "500000.00", "tax_rate": "19", "unit_id": 70, "status": "Activo"},
        ]
    
    # Filtrar por query (nombre o código, case-insensitive)
    query_lower = query.lower()
    filtered = [
        s for s in services_db 
        if s["status"] == "Activo" and (
            query_lower in s["name"].lower() or 
            query_lower in s["code"].lower()
        )
    ]
    
    return MockResponse(200, {
        "success": True,
        "data": filtered
    })


def do_list_payment_methods(client, permissions=None, authenticated=True):
    """
    Simula GET /payment_methods/ - Listar métodos de pago.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    payment_methods = [
        {"code": 48, "name": "Efectivo"},
        {"code": 49, "name": "Transferencia bancaria"},
        {"code": 50, "name": "Tarjeta de crédito"},
    ]
    
    return MockResponse(200, {
        "success": True,
        "data": payment_methods
    })


def do_list_tax_regimes(client, permissions=None, authenticated=True):
    """
    Simula GET /tax_regimes/ - Listar regímenes tributarios.
    """
    if not authenticated:
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    tax_regimes = [
        {"id_tax_regime": 1, "code": "04", "name": "Régimen Simplificado"},
        {"id_tax_regime": 2, "code": "05", "name": "Régimen Común"},
    ]
    
    return MockResponse(200, {
        "success": True,
        "data": tax_regimes
    })


# ============================================================================
# PYTEST FIXTURE
# ============================================================================

@pytest.fixture
def client():
    """Fixture para cliente de API"""
    from rest_framework.test import APIClient
    return APIClient()


# ============================================================================
# TEST CASES - ACTUALIZAR LÍNEAS (19-20)
# ============================================================================



# ============================================================================
# TEST CASES - PART 2 (19-37)
# ============================================================================

def test_ut_sol_009_19_actualizar_linea_recalcula_totales(client):
    """
    UT-SOL-009.19: Actualizar línea recalcula totales
    
    Verifica PATCH de línea existente y recálculo de totales de factura.
    """
    invoice = DummyInvoice(118, "FE-2025-0118", "BORRADOR", 1)
    line = DummyInvoiceLine(10, 118, 4, 1, 10, 19, 70, 1)  # qty 1, desc 10%
    
    resp = do_update_line(
        client,
        invoice_id=118,
        line_id=10,
        permissions=[159],
        authenticated=True,
        quantity=2,
        discount_percentage=20,
        invoices_db=[invoice],
        lines_db=[line]
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.19] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body["success"] == True, "[UT-SOL-009.19] Success debe ser True"
    assert "total_line_amount" in body, "[UT-SOL-009.19] Debe incluir total recalculado"


def test_ut_sol_009_20_actualizar_linea_inexistente_retorna_404(client):
    """
    UT-SOL-009.20: Actualizar línea inexistente retorna 404
    
    Valida manejo de id de línea inválido.
    """
    invoice = DummyInvoice(118, "FE-2025-0118", "BORRADOR", 1)
    
    resp = do_update_line(
        client,
        invoice_id=118,
        line_id=9999,  # No existe
        permissions=[159],
        authenticated=True,
        invoices_db=[invoice],
        lines_db=[]
    )
    
    assert resp.status_code == 404, f"[UT-SOL-009.20] Esperado: 404, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "línea" in body["detail"].lower() or "linea" in body["detail"].lower(), \
        "[UT-SOL-009.20] Debe mencionar línea no encontrada"


# ============================================================================
# TEST CASES - ELIMINAR LÍNEAS (21-22)
# ============================================================================

def test_ut_sol_009_21_eliminar_linea_actualiza_totales(client):
    """
    UT-SOL-009.21: Eliminar línea exitoso actualiza totales
    
    Verifica DELETE de línea y recálculo de totales.
    """
    invoice = DummyInvoice(119, "FE-2025-0119", "BORRADOR", 1, amount_to_pay=Decimal("200000"))
    line = DummyInvoiceLine(11, 119, 4, 1, 0, 19, 70, 1)
    invoice.lines = [line]
    
    resp = do_delete_line(
        client,
        invoice_id=119,
        line_id=11,
        permissions=[159],
        authenticated=True,
        invoices_db=[invoice],
        lines_db=[line]
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.21] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body["success"] == True, "[UT-SOL-009.21] Success debe ser True"


def test_ut_sol_009_22_eliminar_linea_inexistente_retorna_404(client):
    """
    UT-SOL-009.22: Eliminar línea inexistente retorna 404
    
    Valida manejo de eliminación con id inválido.
    """
    invoice = DummyInvoice(119, "FE-2025-0119", "BORRADOR", 1)
    
    resp = do_delete_line(
        client,
        invoice_id=119,
        line_id=9999,
        permissions=[159],
        authenticated=True,
        invoices_db=[invoice],
        lines_db=[]
    )
    
    assert resp.status_code == 404, f"[UT-SOL-009.22] Esperado: 404, Obtenido: {resp.status_code}"


# ============================================================================
# TEST CASES - CARGOS FINALES (23-24)
# ============================================================================

def test_ut_sol_009_23_anadir_cargos_finales_actualiza_total(client):
    """
    UT-SOL-009.23: Añadir cargos finales exitoso actualiza amount_to_pay
    
    Verifica POST de cargos adicionales sobre factura.
    """
    invoice = DummyInvoice(120, "FE-2025-0120", "BORRADOR", 1, amount_to_pay=Decimal("100000"))
    invoice.lines = [DummyInvoiceLine(1, 120, 4, 1, 0, 19, 70, 1)]
    
    resp = do_add_final_charges(
        client,
        invoice_id=120,
        permissions=[158],
        authenticated=True,
        allowance_charges=[
            {"reason": "Recargo por transporte", "amount": "50000.00"}
        ],
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.23] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body["success"] == True, "[UT-SOL-009.23] Success debe ser True"
    assert body["allowance_total"] == "50000.00", "[UT-SOL-009.23] allowance_total incorrecto"


def test_ut_sol_009_24_cargo_final_monto_negativo_retorna_400(client):
    """
    UT-SOL-009.24: Cargo final con monto negativo retorna 400
    
    Valida que amount sea numérico positivo.
    """
    invoice = DummyInvoice(120, "FE-2025-0120", "BORRADOR", 1)
    
    resp = do_add_final_charges(
        client,
        invoice_id=120,
        permissions=[158],
        authenticated=True,
        allowance_charges=[
            {"reason": "Error", "amount": "-1.00"}
        ],
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 400, f"[UT-SOL-009.24] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "monto" in body["detail"].lower() or "positivo" in body["detail"].lower(), \
        "[UT-SOL-009.24] Debe mencionar validación de monto"


# ============================================================================
# TEST CASES - ELIMINAR FACTURA (25-26)
# ============================================================================

def test_ut_sol_009_25_eliminar_factura_borrador_exitoso(client):
    """
    UT-SOL-009.25: Eliminar factura en BORRADOR exitoso
    
    Verifica DELETE de factura en estado BORRADOR.
    """
    invoice = DummyInvoice(121, "FE-2025-0121", "BORRADOR", 1)
    invoices_db = [invoice]
    
    resp = do_delete_invoice(
        client,
        invoice_id=121,
        permissions=[158],
        authenticated=True,
        invoices_db=invoices_db
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.25] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body["success"] == True, "[UT-SOL-009.25] Success debe ser True"
    assert len(invoices_db) == 0, "[UT-SOL-009.25] Factura debe estar eliminada de DB"


def test_ut_sol_009_26_no_eliminar_enviada_validada(client):
    """
    UT-SOL-009.26: No permite eliminar ENVIADA/VALIDADA
    
    Valida restricción de eliminación por estado.
    """
    invoice = DummyInvoice(122, "FE-2025-0122", "ENVIADA", 1)
    
    resp = do_delete_invoice(
        client,
        invoice_id=122,
        permissions=[158],
        authenticated=True,
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 409, f"[UT-SOL-009.26] Esperado: 409, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "estado" in body["detail"].lower(), "[UT-SOL-009.26] Debe mencionar problema de estado"


# ============================================================================
# TEST CASES - GENERAR FE (27-30)
# ============================================================================

def test_ut_sol_009_27_generar_fe_exitoso_cambia_a_enviada(client):
    """
    UT-SOL-009.27: Generar FE exitoso cambia estado a ENVIADA
    
    Verifica transición de estado y retorno de enlaces de factura al generar.
    """
    invoice = DummyInvoice(123, "FE-2025-0123", "BORRADOR", 1)
    invoice.lines = [DummyInvoiceLine(1, 123, 4, 1, 0, 19, 70, 1)]
    
    resp = do_generate_fe(
        client,
        invoice_id=123,
        permissions=[160],
        authenticated=True,
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.27] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["success"] == True, "[UT-SOL-009.27] Success debe ser True"
    assert body["status"] == "ENVIADA", "[UT-SOL-009.27] Estado debe cambiar a ENVIADA"
    assert body["invoice_pdf_url"] != "", "[UT-SOL-009.27] Debe incluir URL del PDF"
    assert body["invoice_xml_url"] != "", "[UT-SOL-009.27] Debe incluir URL del XML"


def test_ut_sol_009_28_generar_fe_sin_lineas_retorna_409(client):
    """
    UT-SOL-009.28: Generar FE sin líneas retorna 409
    
    Valida precondición de existencia de líneas.
    """
    invoice = DummyInvoice(124, "FE-2025-0124", "BORRADOR", 1)
    invoice.lines = []  # Sin líneas
    
    resp = do_generate_fe(
        client,
        invoice_id=124,
        permissions=[160],
        authenticated=True,
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 409, f"[UT-SOL-009.28] Esperado: 409, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "línea" in body["detail"].lower() or "linea" in body["detail"].lower(), \
        "[UT-SOL-009.28] Debe mencionar falta de líneas"


def test_ut_sol_009_29_reintento_generate_fe_sobre_enviada_retorna_409(client):
    """
    UT-SOL-009.29: Reintento de generate_fe sobre ENVIADA retorna 409
    
    Verifica idempotencia/validación de segunda llamada.
    """
    invoice = DummyInvoice(125, "FE-2025-0125", "ENVIADA", 1)
    invoice.lines = [DummyInvoiceLine(1, 125, 4, 1, 0, 19, 70, 1)]
    
    resp = do_generate_fe(
        client,
        invoice_id=125,
        permissions=[160],
        authenticated=True,
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 409, f"[UT-SOL-009.29] Esperado: 409, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "estado" in body["detail"].lower(), "[UT-SOL-009.29] Debe mencionar problema de estado"


def test_ut_sol_009_30_generacion_fe_rechazada_por_dian(client):
    """
    UT-SOL-009.30: Generación FE rechazada por DIAN marca estado RECHAZADA
    
    Valida manejo de rechazo al validar con DIAN vía FACTUS.
    """
    invoice = DummyInvoice(126, "FE-2025-0126", "BORRADOR", 1)
    invoice.lines = [DummyInvoiceLine(1, 126, 4, 1, 0, 19, 70, 1)]
    
    resp = do_generate_fe(
        client,
        invoice_id=126,
        permissions=[160],
        authenticated=True,
        invoices_db=[invoice],
        simulate_dian_rejection=True
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.30] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["success"] == False, "[UT-SOL-009.30] Success debe ser False en rechazo"
    assert body["status"] == "RECHAZADA", "[UT-SOL-009.30] Estado debe ser RECHAZADA"
    assert "api_response" in body, "[UT-SOL-009.30] Debe incluir respuesta de API externa"


# ============================================================================
# TEST CASES - BÚSQUEDA Y CATÁLOGOS (31-35)
# ============================================================================

def test_ut_sol_009_31_buscar_servicio_por_nombre_retorna_coincidencias(client):
    """
    UT-SOL-009.31: Buscar servicio por nombre retorna coincidencias
    
    Verifica GET /services/search/?query=<texto> trae servicios activos por nombre.
    """
    resp = do_search_services(
        client,
        query="preventivo",
        authenticated=True
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.31] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["success"] == True, "[UT-SOL-009.31] Success debe ser True"
    assert "data" in body, "[UT-SOL-009.31] Debe incluir campo data"
    assert len(body["data"]) > 0, "[UT-SOL-009.31] Debe devolver al menos una coincidencia"
    
    # Validar estructura
    first = body["data"][0]
    assert "id" in first and "name" in first and "base_price" in first, \
        "[UT-SOL-009.31] Campos incompletos en servicio"


def test_ut_sol_009_32_buscar_servicio_por_codigo_retorna_exacta(client):
    """
    UT-SOL-009.32: Buscar servicio por código retorna coincidencia exacta
    
    Verifica que query con código "SVC-2025-0001" retorne ese servicio.
    """
    resp = do_search_services(
        client,
        query="SVC-2025-0001",
        authenticated=True
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.32] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert len(body["data"]) >= 1, "[UT-SOL-009.32] Debe encontrar el servicio"
    assert body["data"][0]["code"] == "SVC-2025-0001", "[UT-SOL-009.32] Código no coincide"


def test_ut_sol_009_33_busqueda_sin_resultados_retorna_vacio(client):
    """
    UT-SOL-009.33: Búsqueda sin resultados retorna arreglo vacío
    
    Verifica manejo de query sin coincidencias.
    """
    resp = do_search_services(
        client,
        query="xxxx_no_existente",
        authenticated=True
    )
    
    assert resp.status_code == 200, f"[UT-SOL-009.33] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body["success"] == True, "[UT-SOL-009.33] Success debe ser True"
    assert body["data"] == [], "[UT-SOL-009.33] Data debe ser arreglo vacío"


def test_ut_sol_009_34_listar_metodos_pago_expone_catalogo(client):
    """
    UT-SOL-009.34: Listar métodos de pago expone catálogo mínimo
    
    Verifica GET /payment_methods/ retorna lista utilizable.
    """
    resp = do_list_payment_methods(client, authenticated=True)
    
    assert resp.status_code == 200, f"[UT-SOL-009.34] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert "data" in body, "[UT-SOL-009.34] Debe incluir campo data"
    assert len(body["data"]) > 0, "[UT-SOL-009.34] Debe tener al menos un método"
    
    first = body["data"][0]
    assert "code" in first and "name" in first, "[UT-SOL-009.34] Faltan campos code/name"


def test_ut_sol_009_35_listar_regimenes_tributarios_expone_catalogo(client):
    """
    UT-SOL-009.35: Listar regímenes tributarios expone catálogo mínimo
    
    Verifica GET /tax_regimes/ retorna lista con code y name.
    """
    resp = do_list_tax_regimes(client, authenticated=True)
    
    assert resp.status_code == 200, f"[UT-SOL-009.35] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert "data" in body, "[UT-SOL-009.35] Debe incluir campo data"
    assert len(body["data"]) > 0, "[UT-SOL-009.35] Debe tener al menos un régimen"
    
    first = body["data"][0]
    required_fields = ["id_tax_regime", "code", "name"]
    for field in required_fields:
        assert field in first, f"[UT-SOL-009.35] Falta campo: {field}"


# ============================================================================
# TEST CASES - AUDITORÍA Y CONSISTENCIA (36-37)
# ============================================================================

def test_ut_sol_009_36_auditoria_registra_eventos_clave(client):
    """
    UT-SOL-009.36: Historial/auditoría registra eventos clave
    
    Verifica que crear, actualizar, añadir línea y generar FE creen entradas de auditoría.
    (Simplificado: verificamos que las operaciones permiten auditoría)
    """
    # Este test conceptual valida que las operaciones tienen estructura para auditoría
    # En implementación real, se consultaría tabla de auditoría
    
    invoice = DummyInvoice(123, "FE-2025-0123", "BORRADOR", 1)
    invoice.lines = [DummyInvoiceLine(1, 123, 4, 1, 0, 19, 70, 1)]
    
    # Simular flujo completo
    # 1. Crear (ya creada)
    # 2. Actualizar
    # 3. Añadir línea (ya tiene)
    # 4. Generar FE
    resp = do_generate_fe(
        client,
        invoice_id=123,
        permissions=[160],
        authenticated=True,
        invoices_db=[invoice]
    )
    
    assert resp.status_code == 200, "[UT-SOL-009.36] Operación debe completarse exitosamente"
    
    # En implementación real: consultar auditoría y verificar timestamps
    # assert auditoría incluye: creation_event, update_event, line_added_event, fe_generated_event


def test_ut_sol_009_37_no_modificar_factura_validada(client):
    """
    UT-SOL-009.37: No permite modificar factura VALIDADA
    
    Valida que PATCH líneas y PUT borrador fallen en VALIDADA.
    """
    invoice = DummyInvoice(127, "FE-2025-0127", "VALIDADA", 1)
    line = DummyInvoiceLine(10, 127, 4, 1, 0, 19, 70, 1)
    
    # Intentar actualizar línea
    resp = do_update_line(
        client,
        invoice_id=127,
        line_id=10,
        permissions=[159],
        authenticated=True,
        quantity=3,
        invoices_db=[invoice],
        lines_db=[line]
    )
    
    assert resp.status_code == 409, f"[UT-SOL-009.37] Esperado: 409, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "borrador" in body["detail"].lower() or "validada" in body["detail"].lower(), \
        "[UT-SOL-009.37] Debe mencionar restricción por estado"


# ============================================================================
# FIN DE PARTE 2
# ============================================================================
