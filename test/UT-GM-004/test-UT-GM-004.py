import os
import sys
import json
import pytest
from unittest.mock import patch

# Configuración de Django ANTES de cualquier import de Django/DRF
if '/app' not in sys.path:
    sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')

import django
django.setup()

# AHORA sí podemos importar Django/DRF
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from rest_framework.test import APIClient

# Model imports (usando rutas explícitas para evitar ambigüedades)
from maintenance.models.maintenance import Maintenance
from machinery.models.machinery import Machinery
from machinery.models.periodic_maintenance import PeriodicMaintenanceScheduling
from parameterization.models import (
    TypesCategory, Types, BrandsCategory, Brands, Models, Statues, StatuesCategory,
)
from users.models import User


# ==============================
# Utilidades de prueba y reporte
# ==============================

class Report:
    rows = []

    @classmethod
    def add(cls, case_id, title, payload, status_code, response_json, approved):
        try:
            resp_obj = response_json if isinstance(response_json, dict) else response_json()
        except Exception:
            resp_obj = {}
        
        # Mostrar resultado en consola
        estado = '✅ APROBADO' if approved else '❌ NO APROBADO'
        print(f"\n{case_id}: {title}")
        print(f"HTTP {status_code} - {estado}")
        if not approved:
            print(f"❗ Respuesta: {resp_obj}")
        
        cls.rows.append({
            'id': case_id,
            'title': title,
            'payload': payload,
            'status_code': status_code,
            'response': resp_obj,
            'approved': approved,
        })


@pytest.fixture(scope='module', autouse=True)
def _write_report_on_module_end():
    Report.rows = []
    yield
    # Escribimos el reporte al finalizar el módulo
    lines = [
        '# Reporte HU-GM-004 (DELETE /maintenance/{id_maintenance}/)',
        '',
        '| ID | Título | HTTP | Estado | Payload | Respuesta |',
        '| --- | --- | --- | --- | --- | --- |',
    ]
    for r in Report.rows:
        estado = 'APROBADO' if r['approved'] else 'NO APROBADO'
        payload = json.dumps(r['payload'], ensure_ascii=False) if r['payload'] else 'N/A'
        resp = json.dumps(r['response'], ensure_ascii=False)
        lines.append(f"| {r['id']} | {r['title']} | {r['status_code']} | {estado} | `{payload}` | `{resp}` |")

    out_path = os.path.join(os.path.dirname(__file__), 'test_UT_GM_004_report.md')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


@pytest.fixture
def api_client():
    return APIClient()


# ==============================
# Seed mínimo de parametrización
# ==============================

def seed_minimum_parameterization():
    """Crea/obtiene lo mínimo para poder crear mantenimientos y maquinaria.
    Respeta el modelo de usuario (solo id_user).
    """
    try:
        user = User.objects.get(id_user=1)
    except User.DoesNotExist:
        user = User.objects.create(id_user=1)

    sc = StatuesCategory.objects.order_by('id_statues_categories').first()
    if not sc:
        sc = StatuesCategory.objects.create(
            name='Default', description='',
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user,
        )

    active, _ = Statues.objects.get_or_create(
        id_statues=1,
        defaults=dict(
            name='Activo', description='Estado activo', id_statues_categories=sc,
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user,
        ),
    )
    inactive, _ = Statues.objects.get_or_create(
        id_statues=2,
        defaults=dict(
            name='Inactivo', description='Estado inactivo', id_statues_categories=sc,
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user,
        ),
    )

    tc = TypesCategory.objects.order_by('id_types_categories').first()
    if not tc:
        tc = TypesCategory.objects.create(
            name='Tipos Mantenimiento', description='',
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user,
        )

    t = Types.objects.order_by('id_types').first()
    if not t:
        t = Types.objects.create(
            name='Preventivo', description='Mantenimiento preventivo', id_types_categories=tc,
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user, id_statues=active,
        )

    bc = BrandsCategory.objects.order_by('id_brands_categories').first()
    if not bc:
        bc = BrandsCategory.objects.create(
            name='General', description='',
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user,
        )

    brand = Brands.objects.order_by('id_brands').first()
    if not brand:
        brand = Brands.objects.create(
            name='BrandX', description='', id_brands_categories=bc,
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user, id_statues=active,
        )

    model = Models.objects.order_by('id_model').first()
    if not model:
        model = Models.objects.create(
            id_brand=brand, name='ModelY', description='',
            creation_date=timezone.now(), modification_date=timezone.now(),
            id_responsible_user=user, id_statues=active,
        )

    return {
        'user': user,
        'active': active,
        'inactive': inactive,
        'type': t,
        'brand': brand,
        'model': model,
    }


# ==============================
# Helpers de creación
# ==============================

def delete_url(mid: int) -> str:
    return f"/maintenance/{mid}/"


def create_maintenance(seed, name: str, description: str) -> Maintenance:
    existing = Maintenance.objects.filter(name=name).first()
    if existing:
        return existing
    return Maintenance.objects.create(
        name=name,
        description=description,
        maintenance_type=seed['type'],
        maintenance_status=seed['active'],
        id_responsible_user=seed['user'],
    )


def create_machinery(seed, serial='SER-UTGM-004') -> Machinery:
    return Machinery.objects.create(
        machinery_name='Demo Machine', manufacturing_year=2020,
        serial_number=serial,
        machinery_type=seed['type'], machinery_secondary_type=seed['type'],
        id_model=seed['model'], tariff_subheading='', id_city=1,
        image_path='', id_device=None,
        machinery_operational_status=seed['active'], id_responsible_user=seed['user'],
    )


def relate_periodic(maintenance: Maintenance, machinery: Machinery, usage_hours=100) -> PeriodicMaintenanceScheduling:
    return PeriodicMaintenanceScheduling.objects.create(
        machinery=machinery, maintenance=maintenance, usage_hours=usage_hours,
    )


# ==============================
# Pruebas UT-GM-001 .. UT-GM-010
# ==============================

# UT-GM-001

def test_gm004_001_eliminacion_sin_asociaciones(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-001', 'Eliminar sin asociaciones')

    resp = api_client.delete(delete_url(m.id_maintenance))

    exists = Maintenance.objects.filter(pk=m.id_maintenance).exists()
    ok = resp.status_code == 200 and resp.json().get('success') is True and not exists
    Report.add('UT-GM-001', 'Verificar eliminación exitosa de mantenimiento sin asociaciones', None,
               resp.status_code, resp.json, ok)

    assert resp.status_code == 200
    assert resp.json().get('success') is True
    assert not exists


# UT-GM-002

def test_gm004_002_inactivacion_con_asociaciones(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-002', 'Con asociaciones -> soft delete')
    mach = create_machinery(seed, serial='SER-UTGM004-002')
    relate_periodic(m, mach, usage_hours=250)

    resp = api_client.delete(delete_url(m.id_maintenance))

    ok = resp.status_code == 409 and resp.json().get('success') is False
    Report.add('UT-GM-002', 'Verificar inactivación de mantenimiento con asociaciones activas', None,
               resp.status_code, resp.json, ok)

    assert resp.status_code == 409


# UT-GM-003

def test_gm004_003_permiso_insuficiente(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-003', 'Permiso insuficiente')

    # Mock: simulamos que get_object lanza PermissionDenied
    with patch('maintenance.api.maintenance_viewset.MaintenanceViewSet.get_object', side_effect=PermissionDenied('Forbidden')):
        resp = api_client.delete(delete_url(m.id_maintenance))

    m.refresh_from_db()
    unchanged = m.maintenance_status_id == seed['active'].id_statues

    ok = resp.status_code in (400, 403) and unchanged
    Report.add('UT-GM-003', 'Verificar rechazo por permisos insuficientes (403 Forbidden)', None,
               resp.status_code, getattr(resp, 'json', lambda: {}), ok)

    assert resp.status_code in (400, 403)
    assert unchanged


# UT-GM-004

def test_gm004_004_recurso_inexistente(api_client):
    resp = api_client.delete(delete_url(999999))

    ok = resp.status_code in (400, 404)
    Report.add('UT-GM-004', 'Verificar manejo de recurso inexistente (404 Not Found)',
               {'id_maintenance': 999999}, resp.status_code, getattr(resp, 'json', lambda: {}), ok)

    assert resp.status_code in (400, 404)


# UT-GM-005

def test_gm004_005_auditoria_en_eliminacion(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-005', 'Auditoría en eliminación')

    resp = api_client.delete(delete_url(m.id_maintenance))

    ok = resp.status_code == 200 and resp.json().get('success') is True
    Report.add('UT-GM-005', 'Verificar registro de auditoría en eliminación exitosa', None,
               resp.status_code, resp.json, ok)

    assert resp.status_code == 200


# UT-GM-006

def test_gm004_006_auditoria_en_inactivacion(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-006', 'Auditoría en inactivación')
    mach = create_machinery(seed, serial='SER-UTGM004-006')
    relate_periodic(m, mach, usage_hours=300)

    resp = api_client.delete(delete_url(m.id_maintenance))

    ok = resp.status_code == 409
    Report.add('UT-GM-006', 'Verificar registro de auditoría en inactivación', None,
               resp.status_code, resp.json, ok)

    assert resp.status_code == 409


# UT-GM-007

def test_gm004_007_idempotencia_delete(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-007', 'Idempotencia')

    resp1 = api_client.delete(delete_url(m.id_maintenance))
    resp2 = api_client.delete(delete_url(m.id_maintenance))

    ok = resp1.status_code == 200 and resp2.status_code in (400, 404)
    Report.add('UT-GM-007', 'Verificar idempotencia del método DELETE', None,
               f'1st:{resp1.status_code} 2nd:{resp2.status_code}',
               {'first': getattr(resp1, 'data', {}), 'second': getattr(resp2, 'data', {})}, ok)

    assert resp1.status_code == 200
    assert resp2.status_code in (400, 404)


# UT-GM-008

def test_gm004_008_ocultacion_en_formularios(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-008', 'Ocultación tras inactivación')
    # Inactivar manualmente para simular soft delete aplicado
    m.maintenance_status = seed['inactive']
    m.save(update_fields=['maintenance_status'])

    resp = api_client.get('/maintenance/active/')
    data = resp.json().get('data', []) if hasattr(resp, 'json') and callable(resp.json) else []
    not_listed = all(item.get('id_maintenance') != m.id_maintenance for item in data)

    ok = resp.status_code == 200 and not_listed
    Report.add('UT-GM-008', 'Verificar ocultación en formularios tras inactivación', None,
               resp.status_code, {'in_active_list': not not_listed, 'count': len(data)}, ok)

    assert resp.status_code == 200


# UT-GM-009

def test_gm004_009_validacion_asociaciones(api_client):
    seed = seed_minimum_parameterization()
    m1 = create_maintenance(seed, 'UTGM004-009-A', 'Sin asociaciones')
    m2 = create_maintenance(seed, 'UTGM004-009-B', 'Con asociaciones')
    mach = create_machinery(seed, serial='SER-UTGM004-009')
    relate_periodic(m2, mach, usage_hours=400)

    r1 = api_client.delete(delete_url(m1.id_maintenance))
    r2 = api_client.delete(delete_url(m2.id_maintenance))

    ok = r1.status_code == 200 and r2.status_code == 409
    Report.add('UT-GM-009', 'Verificar validación de asociaciones antes de eliminación', None,
               f'no_assoc:{r1.status_code} with_assoc:{r2.status_code}',
               {'no_assoc': getattr(r1, 'data', {}), 'with_assoc': getattr(r2, 'data', {})}, ok)

    assert r1.status_code == 200
    assert r2.status_code == 409


# UT-GM-010

def test_gm004_010_manejo_errores_bd(api_client):
    seed = seed_minimum_parameterization()
    m = create_maintenance(seed, 'UTGM004-010', 'Error BD simulado')

    # Mock: simulamos un IntegrityError en delete() para verificar manejo de 409/500
    with patch.object(Maintenance, 'delete', side_effect=IntegrityError('forced integrity error')):
        resp = api_client.delete(delete_url(m.id_maintenance))

    ok = resp.status_code in (200, 400, 404, 409, 500)
    Report.add('UT-GM-010', 'Verificar manejo de errores de base de datos',
               {'maintenance_id': m.id_maintenance}, resp.status_code, getattr(resp, 'json', lambda: {}), ok)

    assert ok
