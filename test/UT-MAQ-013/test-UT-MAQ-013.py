import os
import jwt
import json
from datetime import date, datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

# Models
from users.models.user import User
from machinery.models.machinery import Machinery
from machinery.models.machinery_usage_sheet import MachineryUsageSheet
from parameterization.models import (
    Statues, StatuesCategory,
    Units, UnitsCategory,
    Types, TypesCategory,
    Brands, BrandsCategory, Models
)


# -----------------------------
# Helpers de reporte en Markdown
# -----------------------------

class ReportCollector:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.entries = []

    def add(self, case_id, title, method, url, payload, expected, response):
        try:
            resp_json = response.json()
        except Exception:
            resp_json = getattr(response, 'data', None)

        entry = {
            "ID": case_id,
            "Titulo": title,
            "Metodo": method,
            "URL": url,
            "Payload": payload,
            "Esperado": expected,
            "Status": response.status_code,
            "Respuesta": resp_json,
        }
        self.entries.append(entry)

    def write_markdown(self):
        out_dir = os.path.join(self.base_dir, 'UT-MAQ-013')
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'reporte_UT_MAQ_013.md')

        lines = []
        lines.append(f"# Reporte de Pruebas HU-MAQ-013 – Actualizar Información de Uso\n")
        lines.append(f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
        lines.append("\n")

        for e in self.entries:
            aprobado = self._evaluate_approval(e)
            lines.append(f"## {e['ID']} – {e['Titulo']}")
            lines.append("")
            lines.append(f"- Metodo: {e['Metodo']}")
            lines.append(f"- URL: {e['URL']}")
            lines.append(f"- Status: {e['Status']}")
            lines.append(f"- Esperado: {e['Esperado']}")
            lines.append("")
            lines.append("### Payload enviado")
            lines.append("```json")
            lines.append(json.dumps(e['Payload'], ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
            lines.append("### Respuesta")
            lines.append("```json")
            lines.append(json.dumps(e['Respuesta'], ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
            lines.append(f"Resultado: {'APROBADO' if aprobado else 'NO APROBADO'}")
            lines.append("\n---\n")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _evaluate_approval(self, e):
        """
        Evalúa APROBADO/NO APROBADO respecto a la especificación dada.
        Nota: en algunos casos aceptamos el comportamiento actual del código (p.ej. 400 en vez de 404)
        pero marcamos NO APROBADO si difiere del documento de requisitos.
        """
        case_id = e["ID"]
        status_code = e["Status"]
        resp = e["Respuesta"] or {}

        if case_id == "UT-MAQ-001":
            return status_code == 200 and resp.get("success") is True
        if case_id == "UT-MAQ-002":
            return status_code == 200 and resp.get("success") is True
        if case_id == "UT-MAQ-003":
            return status_code == 403
        if case_id == "UT-MAQ-004":
            # Debe ser 400 por justificación obligatoria
            return status_code == 400 and "justification" in (resp.get("details") or {})
        if case_id == "UT-MAQ-005":
            return status_code == 200 and resp.get("success") is True
        if case_id == "UT-MAQ-006":
            # Aceptamos que el serializer devuelva uno de los dos errores en validación secuencial
            return status_code == 400 and any(k in (resp.get("details") or {}) for k in ["tenancy_type", "contract_end_date"])
        if case_id == "UT-MAQ-007":
            return status_code == 400 and all(k in (resp.get("details") or {}) for k in ["usage_hours", "distance_value"]) or status_code == 400
        if case_id == "UT-MAQ-008":
            return status_code == 400 and any(k in (resp.get("details") or {}) for k in ["usage_condition", "distance_unit", "tenancy_type"])  # con una es suficiente para rechazo
        if case_id == "UT-MAQ-009":
            # Especificación pide 404; el código actual responde 400. Marcamos NO APROBADO si no es 404.
            return status_code == 404
        if case_id == "UT-MAQ-010":
            return status_code == 200 and resp.get("success") is True
        return False


@pytest.fixture(scope="session")
def jwt_secret():
    # Garantiza que el autenticador tenga una clave para firmar/validar
    secret = os.getenv("JWT_SECRET", None) or "testsecret"
    os.environ["JWT_SECRET"] = secret
    return secret


def build_token(secret, include_perm_94=True):
    roles = []
    if include_perm_94:
        roles = [
            {
                "name": "tester",
                "permissions": [
                    {"id": 94, "name": "machinery_usage_sheet.update"}
                ],
            }
        ]
    payload = {
        "id": 1,
        "email": "tester@example.com",
        "rol": roles,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def api_client():
    # Importar aquí para evitar acceso a settings antes de tiempo
    from rest_framework.test import APIClient  # type: ignore
    return APIClient()


@pytest.fixture(scope="session")
def report_collector(request):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    collector = ReportCollector(base_dir)

    def fin():
        collector.write_markdown()

    request.addfinalizer(fin)
    return collector


# -----------------------------
# Datos base en BD real (test DB)
# -----------------------------

@pytest.fixture
def base_data(django_env_and_db):
    now = timezone.now()

    # Usuarios (evitar duplicados entre tests)
    user1, _ = User.objects.get_or_create(id_user=1)

    # Categorías esperadas por reglas (usar IDs fijos según reglas)
    cat_status_usage, _ = StatuesCategory.objects.update_or_create(
        id_statues_categories=3,
        defaults={
            "name": "Estados de uso de la maquinaria",
            "description": "",
            "modification_date": now,
            "creation_date": now,
        },
    )
    cat_units_len, _ = UnitsCategory.objects.update_or_create(
        id_units_categories=7,
        defaults={
            "name": "Longitud",
            "description": "",
            "modification_date": now,
            "creation_date": now,
        },
    )
    cat_types_tenancy, _ = TypesCategory.objects.update_or_create(
        id_types_categories=11,
        defaults={
            "name": "Tenencia",
            "description": "",
            "modification_date": now,
            "creation_date": now,
        },
    )

    # Otras categorías de apoyo
    cat_types_misc, _ = TypesCategory.objects.update_or_create(
        id_types_categories=21,
        defaults={
            "name": "Tipos varios",
            "description": "",
            "modification_date": now,
            "creation_date": now,
        },
    )

    # Estados (Statues)
    status_en_registro, _ = Statues.objects.update_or_create(
        id_statues=3,
        defaults={
            "name": "En registro",
            "description": "",
            "id_statues_categories": cat_status_usage,
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
        },
    )
    status_activa, _ = Statues.objects.update_or_create(
        id_statues=4,
        defaults={
            "name": "Activa",
            "description": "",
            "id_statues_categories": cat_status_usage,
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
        },
    )

    # Tenencia válida (cat 11) y otra inválida (cat 21)
    tenancy_valid, _ = Types.objects.update_or_create(
        id_types=1102,
        defaults={
            "name": "Arrendada",
            "description": "",
            "id_types_categories": cat_types_tenancy,
            "creation_date": now,
            "modification_date": now,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )
    tenancy_invalid, _ = Types.objects.update_or_create(
        id_types=777,
        defaults={
            "name": "Otro tipo",
            "description": "",
            "id_types_categories": cat_types_misc,
            "creation_date": now,
            "modification_date": now,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )

    # Units
    unit_valid, _ = Units.objects.update_or_create(
        id_units=701,
        defaults={
            "id_units_categories": cat_units_len,
            "name": "Kilómetro",
            "symbol": "km",
            "id_types": tenancy_valid,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )
    # Unidad inválida con otra categoría
    cat_units_other, _ = UnitsCategory.objects.update_or_create(
        id_units_categories=8,
        defaults={
            "name": "Otra cat",
            "description": "",
            "modification_date": now,
            "creation_date": now,
        },
    )
    unit_invalid, _ = Units.objects.update_or_create(
        id_units=888,
        defaults={
            "id_units_categories": cat_units_other,
            "name": "Unidad inválida",
            "symbol": "inv",
            "id_types": tenancy_valid,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )

    # Status de uso válidos/invalidos
    usage_status_valid, _ = Statues.objects.update_or_create(
        id_statues=6,
        defaults={
            "name": "Usado",
            "description": "",
            "id_statues_categories": cat_status_usage,
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
        },
    )
    # Estado de uso inválido con otra categoría
    cat_status_other, _ = StatuesCategory.objects.update_or_create(
        id_statues_categories=5,
        defaults={
            "name": "Otra categoría",
            "description": "",
            "modification_date": now,
            "creation_date": now,
        },
    )
    usage_status_invalid, _ = Statues.objects.update_or_create(
        id_statues=999,
        defaults={
            "name": "Estado Inválido",
            "description": "",
            "id_statues_categories": cat_status_other,
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
        },
    )

    # Marcas/Modelos requeridos por Machinery
    bc, _ = BrandsCategory.objects.update_or_create(
        id_brands_categories=1,
        defaults={
            "name": "General",
            "description": "",
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
        },
    )
    brand, _ = Brands.objects.update_or_create(
        id_brands=1,
        defaults={
            "name": "MarcaX",
            "description": "",
            "id_brands_categories": bc,
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )
    model, _ = Models.objects.update_or_create(
        id_model=1,
        defaults={
            "id_brand": brand,
            "name": "ModeloX",
            "description": "",
            "modification_date": now,
            "creation_date": now,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )

    # Types para machinery_type y secondary_type (usar cat misc)
    mach_type, _ = Types.objects.update_or_create(
        id_types=1001,
        defaults={
            "name": "Excavadora",
            "description": "",
            "id_types_categories": cat_types_misc,
            "creation_date": now,
            "modification_date": now,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )
    mach_secondary_type, _ = Types.objects.update_or_create(
        id_types=1002,
        defaults={
            "name": "Hidráulica",
            "description": "",
            "id_types_categories": cat_types_misc,
            "creation_date": now,
            "modification_date": now,
            "id_responsible_user": user1,
            "id_statues": status_activa,
        },
    )

    # Usar sufijo para evitar colisiones por unicidad (nombre/serial)
    suffix = int(now.timestamp() * 1000000)

    # Maquinarias: una en 'Activa' y otra 'En registro'
    mach_active = Machinery.objects.create(
        machinery_name=f"Maq A {suffix}",
        manufacturing_year=2020,
        serial_number=f"SN-A-{suffix}",
        machinery_type=mach_type,
        id_model=model,
        machinery_secondary_type=mach_secondary_type,
        id_city=1,
        image_path=None,
        id_device=None,
        justification=None,
        machinery_operational_status=status_activa,
        id_responsible_user=user1,
    )
    mach_reg = Machinery.objects.create(
        machinery_name=f"Maq B {suffix}",
        manufacturing_year=2021,
        serial_number=f"SN-B-{suffix}",
        machinery_type=mach_type,
        id_model=model,
        machinery_secondary_type=mach_secondary_type,
        id_city=1,
        image_path=None,
        id_device=None,
        justification=None,
        machinery_operational_status=status_en_registro,
        id_responsible_user=user1,
    )

    # Fichas de uso iniciales (sin fijar IDs explícitos)
    usage_non_own = MachineryUsageSheet.objects.create(
        id_machinery=mach_active,
        acquisition_date=date(2024, 1, 1),
        usage_condition=usage_status_valid,
        usage_hours=10.00,
        distance_value=100.000,
        distance_unit=unit_valid,
        tenancy_type=tenancy_valid,
        is_own=False,
        contract_end_date=date(2026, 9, 1),
        id_responsible_user=user1,
        justification="Inicial",
    )
    usage_own = MachineryUsageSheet.objects.create(
        id_machinery=mach_reg,
        acquisition_date=date(2023, 6, 1),
        usage_condition=usage_status_valid,
        usage_hours=5.00,
        distance_value=50.000,
        distance_unit=unit_valid,
        tenancy_type=None,
        is_own=True,
        contract_end_date=None,
        id_responsible_user=user1,
        justification=None,
    )

    return {
        "user": user1,
        "mach_active": mach_active,
        "mach_reg": mach_reg,
        "usage_non_own": usage_non_own,
        "usage_own": usage_own,
        "status_en_registro": status_en_registro,
        "status_activa": status_activa,
        "usage_status_valid": usage_status_valid,
        "usage_status_invalid": usage_status_invalid,
        "unit_valid": unit_valid,
        "unit_invalid": unit_invalid,
        "tenancy_valid": tenancy_valid,
        "tenancy_invalid": tenancy_invalid,
    }


def url_update(id_usage_sheet: int) -> str:
    # El nombre de ruta de @action puede ser frágil; usamos la URL directa para robustez.
    return f"/machinery-usage/{id_usage_sheet}/update/"


# -----------------------------
# Pruebas
# -----------------------------

def test_UT_MAQ_001_update_own_success(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "is_own": True,
        "usage_hours": 170.25,
        "distance_value": 1400.125,
        "distance_unit": base_data["unit_valid"].id_units,
        "usage_condition": base_data["usage_status_valid"].id_statues,
        "responsible_user": base_data["user"].id_user,
        "justification": "Corrección de horas y distancia tras auditoría.",
        # Incluir campos para que el serializer los limpie explícitamente
        "tenancy_type": "",
        "contract_end_date": "",
    }
    url = url_update(base_data["usage_non_own"].id_usage_sheet)
    resp = api_client.put(url, data=payload, format='json')

    # Verificaciones de BD
    updated = MachineryUsageSheet.objects.get(pk=base_data["usage_non_own"].id_usage_sheet)
    assert updated.is_own is True
    assert updated.tenancy_type is None
    assert updated.contract_end_date is None

    report_collector.add(
        "UT-MAQ-001",
        "Actualizar maquinaria propia con limpieza de tenencia",
        "PUT",
        url,
        payload,
        {"status": 200},
        resp,
    )
    assert resp.status_code == 200
    assert resp.json().get("success") is True


def test_UT_MAQ_002_update_non_own_success(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "is_own": False,
        "tenancy_type": base_data["tenancy_valid"].id_types,
        "contract_end_date": "2026-09-01",
        "responsible_user": base_data["user"].id_user,
        "justification": "Cambio de modalidad de tenencia.",
    }
    url = url_update(base_data["usage_own"].id_usage_sheet)
    before_mod = MachineryUsageSheet.objects.get(pk=base_data["usage_own"].id_usage_sheet).modification_date
    resp = api_client.patch(url, data=payload, format='json')

    updated = MachineryUsageSheet.objects.get(pk=base_data["usage_own"].id_usage_sheet)
    assert updated.is_own is False
    assert updated.tenancy_type_id == base_data["tenancy_valid"].id_types
    assert str(updated.contract_end_date) == "2026-09-01"
    assert updated.modification_date >= before_mod

    report_collector.add(
        "UT-MAQ-002",
        "Actualizar maquinaria no propia con campos obligatorios",
        "PATCH",
        url,
        payload,
        {"status": 200},
        resp,
    )
    assert resp.status_code == 200


def test_UT_MAQ_003_forbidden_without_permission(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=False)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "usage_hours": 200.5,
        "responsible_user": base_data["user"].id_user,
        "justification": "Intento sin permisos",
    }
    url = url_update(base_data["usage_non_own"].id_usage_sheet)
    resp = api_client.put(url, data=payload, format='json')

    # Sin cambios en BD
    unchanged = MachineryUsageSheet.objects.get(pk=base_data["usage_non_own"].id_usage_sheet)
    assert unchanged.usage_hours == 10.00

    report_collector.add(
        "UT-MAQ-003",
        "Rechazo por permisos insuficientes",
        "PUT",
        url,
        payload,
        {"status": 403},
        resp,
    )
    assert resp.status_code == 403


def test_UT_MAQ_004_justification_required_when_active(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Maquinaria ligada a usage_non_own está en estado 'Activa' (no 3)
    payload = {
        "usage_hours": 250.0,
        "responsible_user": base_data["user"].id_user,
        # sin justification
    }
    url = url_update(base_data["usage_non_own"].id_usage_sheet)
    resp = api_client.put(url, data=payload, format='json')

    details = (resp.json() or {}).get("details") or {}
    report_collector.add(
        "UT-MAQ-004",
        "Justificación obligatoria si no está en 'En registro'",
        "PUT",
        url,
        payload,
        {"status": 400},
        resp,
    )
    assert resp.status_code == 400
    assert "justification" in details


def test_UT_MAQ_005_allow_without_justification_when_registration(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # usage_own está amarrada a maquinaria en 'En registro' (id 3)
    payload = {
        "usage_hours": 50.0,
        "distance_value": 100.5,
        "responsible_user": base_data["user"].id_user,
        # sin justification
    }
    url = url_update(base_data["usage_own"].id_usage_sheet)
    resp = api_client.patch(url, data=payload, format='json')

    report_collector.add(
        "UT-MAQ-005",
        "Permitir actualización sin justificación en 'En registro'",
        "PATCH",
        url,
        payload,
        {"status": 200},
        resp,
    )
    assert resp.status_code == 200


def test_UT_MAQ_006_missing_fields_when_not_own(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Caso 1: falta tenancy_type
    payload1 = {
        "is_own": False,
        "responsible_user": base_data["user"].id_user,
        "justification": "Cambio sin completar campos obligatorios",
    }
    url = url_update(base_data["usage_own"].id_usage_sheet)
    resp1 = api_client.patch(url, data=payload1, format='json')
    details1 = (resp1.json() or {}).get("details") or {}
    assert resp1.status_code == 400
    assert "tenancy_type" in details1

    # Caso 2: falta contract_end_date
    payload2 = {
        "is_own": False,
        "tenancy_type": base_data["tenancy_valid"].id_types,
        "responsible_user": base_data["user"].id_user,
        "justification": "Cambio sin completar campos obligatorios",
    }
    resp2 = api_client.patch(url, data=payload2, format='json')
    details2 = (resp2.json() or {}).get("details") or {}
    assert resp2.status_code == 400
    assert "contract_end_date" in details2

    # Registramos solo el segundo intento en reporte (ambos validan la regla)
    report_collector.add(
        "UT-MAQ-006",
        "Faltan campos obligatorios cuando no es propia",
        "PATCH",
        url,
        payload2,
        {"status": 400},
        resp2,
    )


def test_UT_MAQ_007_negative_numbers_and_precision(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "usage_hours": -50.25,
        "distance_value": -100.567,
        "responsible_user": base_data["user"].id_user,
        "justification": "Prueba de validación números negativos",
    }
    url = url_update(base_data["usage_non_own"].id_usage_sheet)
    resp = api_client.put(url, data=payload, format='json')

    report_collector.add(
        "UT-MAQ-007",
        "Validación de números negativos",
        "PUT",
        url,
        payload,
        {"status": 400},
        resp,
    )
    assert resp.status_code == 400


def test_UT_MAQ_008_catalog_category_validation(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    payload = {
        "usage_condition": base_data["usage_status_invalid"].id_statues,  # cat != 3
        "distance_unit": base_data["unit_invalid"].id_units,              # cat != 7
        "tenancy_type": base_data["tenancy_invalid"].id_types,            # cat != 11
        "is_own": False,
        "contract_end_date": "2026-01-01",
        "responsible_user": base_data["user"].id_user,
        "justification": "Prueba validación catálogos",
    }
    url = url_update(base_data["usage_non_own"].id_usage_sheet)
    resp = api_client.put(url, data=payload, format='json')

    report_collector.add(
        "UT-MAQ-008",
        "Validación de categorías de catálogos",
        "PUT",
        url,
        payload,
        {"status": 400},
        resp,
    )
    assert resp.status_code == 400


def test_UT_MAQ_009_not_found_usage_sheet(jwt_secret, api_client, base_data, report_collector):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    missing_id = 999999
    payload = {
        "usage_hours": 100.0,
        "responsible_user": base_data["user"].id_user,
        "justification": "Prueba con ID inexistente",
    }
    url = url_update(missing_id)
    resp = api_client.put(url, data=payload, format='json')

    report_collector.add(
        "UT-MAQ-009",
        "Ficha de uso inexistente devuelve 404 (especificación)",
        "PUT",
        url,
        payload,
        {"status": 404},
        resp,
    )
    # Estricto según especificación: debe ser 404
    assert resp.status_code == 404


def test_UT_MAQ_010_partial_update_preserves_fields(jwt_secret, api_client, base_data, report_collector, monkeypatch):
    token = build_token(jwt_secret, include_perm_94=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    usage = MachineryUsageSheet.objects.get(pk=base_data["usage_non_own"].id_usage_sheet)
    original_reg = usage.registration_date
    # Antes del PATCH, registrar la fecha de modificación actual
    before_mod = usage.modification_date

    payload = {
        "usage_hours": 300.50,
        "responsible_user": base_data["user"].id_user,
        "justification": "Actualización parcial solo de horas",
    }
    url = url_update(usage.id_usage_sheet)
    resp = api_client.patch(url, data=payload, format='json')

    usage.refresh_from_db()
    assert usage.usage_hours == pytest.approx(300.50)
    assert usage.registration_date == original_reg
    # La modificación se sella con la fecha actual (auto_now del modelo sobrescribe)
    assert usage.modification_date is not None
    assert usage.modification_date >= before_mod
    assert usage.modification_date == date.today()

    report_collector.add(
        "UT-MAQ-010",
        "PATCH conserva no enviados y fechas",
        "PATCH",
        url,
        payload,
        {"status": 200},
        resp,
    )
    assert resp.status_code == 200
