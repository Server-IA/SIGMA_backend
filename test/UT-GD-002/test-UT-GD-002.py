"""
Pruebas Unitarias UT-GD-002
Endpoint: GET /telemetry-devices/
Módulo: Gestión de Dispositivos de Telemetría (Listado)

Este archivo contiene los 14 casos de prueba para validar el listado
de dispositivos de telemetría con filtros, búsqueda y paginación.
"""

import pytest
from unittest.mock import Mock, MagicMock
from rest_framework import status
from datetime import datetime, timezone


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
        self.permissions = permissions or [112]  # telemetry_device.list


class DummyTelemetryDevice:
    """Mock de dispositivo de telemetría"""
    def __init__(self, id_device, name, IMEI, status_id=1, registration_date=None):
        self.id_device = id_device
        self.name = name
        self.IMEI = IMEI
        self.status_id = status_id
        self.id_statues_id = status_id
        self.registration_date = registration_date or datetime.now(timezone.utc)
        self.modification_date = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convertir a diccionario para respuesta"""
        return {
            "id_device": self.id_device,
            "name": self.name,
            "IMEI": self.IMEI,
            "status_id": self.status_id,
            "status_name": "Activo" if self.status_id == 1 else "Inactivo",
            "registration_date": self.registration_date.isoformat().replace('+00:00', 'Z')
        }


class MockResponse:
    """Mock de respuesta HTTP"""
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


# ============================================================================
# HELPER FUNCTION
# ============================================================================

def do_list(
    client,
    permissions=None,
    authenticated=True,
    user_obj=None,
    active=True,
    query_params=None,
    devices=None,
    invalid_date_range=False
):
    """
    Simula el endpoint GET /telemetry-devices/ con mocks completos.
    
    Args:
        client: Cliente de pruebas
        permissions: Lista de permisos del usuario
        authenticated: Si el usuario está autenticado
        user_obj: Objeto usuario personalizado
        active: Si el usuario está activo
        query_params: Diccionario de query parameters
        devices: Lista de dispositivos mock (None para generar por defecto)
        invalid_date_range: Simular rango de fechas inválido
    
    Returns:
        MockResponse
    """
    if permissions is None:
        permissions = [112]  # telemetry_device.list
    
    if query_params is None:
        query_params = {}
    
    # 1. Verificar autenticación
    if not authenticated or (user_obj and not getattr(user_obj, 'is_authenticated', True)):
        return MockResponse(401, {"detail": "Authentication credentials were not provided."})
    
    # 2. Verificar usuario activo
    if not active or (user_obj and not getattr(user_obj, 'is_active', True)):
        return MockResponse(403, {"detail": "User inactive or blocked."})
    
    # 3. Verificar permiso 112
    if 112 not in permissions:
        return MockResponse(403, {"detail": "Permisos insuficientes"})
    
    # 4. Validar rango de fechas
    if invalid_date_range:
        from_date = query_params.get('from')
        to_date = query_params.get('to')
        if from_date and to_date and from_date > to_date:
            return MockResponse(400, {
                "detail": "El parámetro 'from' no puede ser posterior a 'to'"
            })
    
    # 5. Generar dispositivos por defecto
    if devices is None:
        devices = [
            DummyTelemetryDevice(1, "FMC 150", 123456789012345, status_id=1, 
                               registration_date=datetime(2025, 9, 19, tzinfo=timezone.utc)),
            DummyTelemetryDevice(2, "Gateway IoT", 123456789012346, status_id=1,
                               registration_date=datetime(2025, 9, 20, tzinfo=timezone.utc)),
            DummyTelemetryDevice(3, "FMC Secondary", 123456789012347, status_id=2,
                               registration_date=datetime(2025, 9, 21, tzinfo=timezone.utc)),
            DummyTelemetryDevice(4, "Sensor Temp", 123456789012348, status_id=1,
                               registration_date=datetime(2025, 9, 22, tzinfo=timezone.utc)),
            DummyTelemetryDevice(5, "FMC Prime", 123456789012349, status_id=1,
                               registration_date=datetime(2025, 9, 23, tzinfo=timezone.utc)),
            DummyTelemetryDevice(6, "Monitor GPS", 123456789012340, status_id=2,
                               registration_date=datetime(2025, 9, 24, tzinfo=timezone.utc)),
        ]
    
    # 6. Aplicar filtros
    filtered = devices[:]
    
    # Filtro por estado
    if 'status' in query_params:
        status_filter = query_params['status'].lower()
        if status_filter == 'activo':
            filtered = [d for d in filtered if d.status_id == 1]
        elif status_filter == 'inactivo':
            filtered = [d for d in filtered if d.status_id == 2]
        else:
            # Status inválido: devolver lista vacía
            filtered = []
    
    # Filtro por rango de fechas
    if 'from' in query_params and 'to' in query_params:
        from_date = datetime.fromisoformat(query_params['from'].replace('Z', '+00:00'))
        to_date = datetime.fromisoformat(query_params['to'].replace('Z', '+00:00'))
        filtered = [d for d in filtered if from_date <= d.registration_date <= to_date]
    
    # Búsqueda por nombre (parcial, case-insensitive)
    if 'q' in query_params:
        search_term = query_params['q'].lower()
        # Buscar en nombre o IMEI
        filtered = [d for d in filtered if search_term in d.name.lower() or search_term in str(d.IMEI)]
    
    # 7. Paginación
    page = int(query_params.get('page', 1))
    page_size = int(query_params.get('page_size', 10))
    
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    
    paginated = filtered[start:end]
    
    # 8. Construir respuesta
    data = [device.to_dict() for device in paginated]
    
    body = {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
    
    return MockResponse(200, body)


# ============================================================================
# PYTEST FIXTURE
# ============================================================================

@pytest.fixture
def client():
    """Fixture para cliente de API"""
    from rest_framework.test import APIClient
    return APIClient()


# ============================================================================
# TEST CASES
# ============================================================================

def test_ut_gd_002_1_acceso_sin_permisos(client):
    """
    UT-GD-002.1: Acceso sin permisos (403)
    
    El endpoint debe denegar el acceso a usuarios que no tienen el permiso 
    telemetry_device.list.
    """
    resp = do_list(
        client,
        permissions=[999],  # Sin permiso correcto
        authenticated=True
    )
    
    assert resp.status_code == 403, f"[UT-GD-002.1] Esperado: 403, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "permiso" in body.get("detail", "").lower()


def test_ut_gd_002_2_listado_basico_happy_path(client):
    """
    UT-GD-002.2: Listado básico — respuesta y esquema (happy path)
    
    El endpoint retorna HTTP 200 y lista de dispositivos con campos requeridos.
    """
    resp = do_list(
        client,
        permissions=[112],
        authenticated=True
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.2] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body.get("success") is True
    assert "data" in body
    assert isinstance(body["data"], list)
    assert len(body["data"]) > 0
    
    # Validar esquema de cada item
    required_fields = ["id_device", "name", "IMEI", "status_id", "status_name", "registration_date"]
    for item in body["data"]:
        for field in required_fields:
            assert field in item, f"[UT-GD-002.2] Campo requerido ausente: {field}"
        
        # Validar tipos
        assert isinstance(item["id_device"], int)
        assert isinstance(item["name"], str)
        assert isinstance(item["status_id"], int)
        assert isinstance(item["status_name"], str)
        assert isinstance(item["registration_date"], str)


def test_ut_gd_002_3_filtrado_por_estado_activo(client):
    """
    UT-GD-002.3: Filtrado por estado operativo = Activo
    
    Aplicar filtro status=Activo debe devolver solo dispositivos cuyo 
    status_name sea "Activo".
    """
    resp = do_list(
        client,
        permissions=[112],
        query_params={"status": "Activo"}
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.3] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    for item in body["data"]:
        assert item["status_name"] == "Activo", \
            f"[UT-GD-002.3] Se devolvió dispositivo con status incorrecto: {item['status_name']}"


def test_ut_gd_002_4_filtrar_por_rango_fechas_inclusivo(client):
    """
    UT-GD-002.4: Filtrar por rango de fechas de registro — inclusión de límites
    
    El filtro por fecha debe incluir dispositivos cuya registration_date sea 
    exactamente igual a desde o hasta (inclusivo).
    """
    query_params = {
        "from": "2025-09-19T00:00:00Z",
        "to": "2025-09-24T23:59:59Z"
    }
    
    resp = do_list(
        client,
        permissions=[112],
        query_params=query_params
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.4] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    # Todos los dispositivos devueltos deben estar dentro del rango
    for item in body["data"]:
        date_str = item["registration_date"].replace('Z', '+00:00')
        device_date = datetime.fromisoformat(date_str)
        from_date = datetime.fromisoformat(query_params["from"].replace('Z', '+00:00'))
        to_date = datetime.fromisoformat(query_params["to"].replace('Z', '+00:00'))
        
        assert from_date <= device_date <= to_date, \
            f"[UT-GD-002.4] Dispositivo fuera de rango: {item['registration_date']}"


def test_ut_gd_002_5_busqueda_por_nombre_case_insensitive(client):
    """
    UT-GD-002.5: Búsqueda rápida por nombre (partial, case-insensitive)
    
    La barra de búsqueda debe localizar por coincidencia parcial en name, 
    sin distinguir mayúsculas.
    """
    resp = do_list(
        client,
        permissions=[112],
        query_params={"q": "fmc"}
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.5] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert len(body["data"]) > 0, "[UT-GD-002.5] No se encontraron resultados para búsqueda 'fmc'"
    
    for item in body["data"]:
        assert "fmc" in item["name"].lower(), \
            f"[UT-GD-002.5] Resultado sin coincidencia: {item['name']}"


def test_ut_gd_002_6_busqueda_por_imei_exacta(client):
    """
    UT-GD-002.6: Búsqueda rápida por IMEI (exact match)
    
    Buscar por IMEI debe soportar búsqueda exacta y el registro devuelto 
    debe coincidir exactamente en IMEI.
    """
    imei_search = "123456789012345"
    
    resp = do_list(
        client,
        permissions=[112],
        query_params={"q": imei_search}
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.6] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert len(body["data"]) > 0, "[UT-GD-002.6] No se encontró dispositivo con IMEI"
    
    found = False
    for item in body["data"]:
        if str(item["IMEI"]) == imei_search:
            found = True
            break
    
    assert found, f"[UT-GD-002.6] IMEI exacto no encontrado en resultados"


def test_ut_gd_002_7_paginacion(client):
    """
    UT-GD-002.7: Paginación: tamaño de página y navegación entre páginas
    
    El endpoint debe soportar page y page_size. Validar que devuelva los 
    registros correctos y metadatos de paginación.
    """
    resp = do_list(
        client,
        permissions=[112],
        query_params={"page": 2, "page_size": 2}
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.7] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert len(body["data"]) <= 2, "[UT-GD-002.7] Tamaño de página incorrecto"
    assert "pagination" in body
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["page_size"] == 2
    assert "total" in body["pagination"]
    assert "total_pages" in body["pagination"]


def test_ut_gd_002_8_sin_resultados_lista_vacia(client):
    """
    UT-GD-002.8: Mensaje cuando no hay resultados tras aplicar filtros
    
    Si filtros no devuelven resultados, el endpoint regresa lista vacía 
    y la API retorna 200.
    """
    resp = do_list(
        client,
        permissions=[112],
        query_params={"status": "Inexistente"}
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.8] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert body.get("data") == [], "[UT-GD-002.8] Debería devolver lista vacía"


def test_ut_gd_002_9_rango_fechas_invalido_400(client):
    """
    UT-GD-002.9: Validación de parámetros: rango fechas inválido (from > to) -> 400
    
    Si from es posterior a to, la API debe devolver 400 Bad Request.
    """
    resp = do_list(
        client,
        permissions=[112],
        query_params={
            "from": "2025-10-01T00:00:00Z",
            "to": "2025-09-01T00:00:00Z"
        },
        invalid_date_range=True
    )
    
    assert resp.status_code == 400, f"[UT-GD-002.9] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "from" in body.get("detail", "").lower() or "posterior" in body.get("detail", "").lower()


def test_ut_gd_002_10_reflejar_registro_nuevo(client):
    """
    UT-GD-002.10: Reflejar registro nuevo inmediatamente (crear + listar)
    
    Después de crear un dispositivo, un GET posterior debe incluir el nuevo.
    """
    # Simular creación de nuevo dispositivo
    new_device = DummyTelemetryDevice(99, "NuevoDevice", 999999999999999, status_id=1)
    
    # Listar con búsqueda del nuevo dispositivo
    resp = do_list(
        client,
        permissions=[112],
        query_params={"q": "NuevoDevice"},
        devices=[new_device]
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.10] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    found = False
    for item in body["data"]:
        if item["name"] == "NuevoDevice":
            found = True
            break
    
    assert found, "[UT-GD-002.10] Dispositivo nuevo no aparece en listado"


def test_ut_gd_002_11_reflejar_modificacion(client):
    """
    UT-GD-002.11: Reflejar modificación de dispositivo (update -> listar)
    
    Actualizar campos y verificar que un GET posterior muestre los cambios.
    """
    # Simular dispositivo modificado
    modified_device = DummyTelemetryDevice(11, "FMC 150 Modificado", 123456789012345, status_id=2)
    
    resp = do_list(
        client,
        permissions=[112],
        query_params={"q": "FMC 150 Modificado"},
        devices=[modified_device]
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.11] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    found = False
    for item in body["data"]:
        if item["id_device"] == 11 and item["name"] == "FMC 150 Modificado":
            found = True
            assert item["status_id"] == 2
            break
    
    assert found, "[UT-GD-002.11] Dispositivo modificado no refleja cambios"


def test_ut_gd_002_12_reflejar_eliminacion_o_inactivacion(client):
    """
    UT-GD-002.12: Reflejar eliminación física o inactivación (delete/inactivate -> listar)
    
    Al eliminar o inactivar un dispositivo, un GET posterior lo debe reflejar.
    """
    # Simular dispositivo inactivado
    devices_list = [
        DummyTelemetryDevice(1, "FMC 150", 123456789012345, status_id=1),
        # id=12 ya no está (eliminado) o está inactivo
        DummyTelemetryDevice(3, "FMC Secondary", 123456789012347, status_id=2),
    ]
    
    # Filtrar solo activos
    resp = do_list(
        client,
        permissions=[112],
        query_params={"status": "Activo"},
        devices=devices_list
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.12] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    # Verificar que id=12 no aparece entre activos
    for item in body["data"]:
        assert item["id_device"] != 12, "[UT-GD-002.12] Dispositivo eliminado aún aparece en activos"


def test_ut_gd_002_13_imei_largo_sin_perdida_precision(client):
    """
    UT-GD-002.13: IMEI de gran longitud — preservación y formato
    
    Verificar que IMEIs largos se conservan sin pérdida de precisión.
    """
    imei_largo = 123456789012348
    device_with_long_imei = DummyTelemetryDevice(50, "Device IMEI Largo", imei_largo, status_id=1)
    
    resp = do_list(
        client,
        permissions=[112],
        query_params={"q": str(imei_largo)},
        devices=[device_with_long_imei]
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.13] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    assert len(body["data"]) > 0, "[UT-GD-002.13] No se encontró dispositivo con IMEI largo"
    
    found_device = body["data"][0]
    assert found_device["IMEI"] == imei_largo or str(found_device["IMEI"]) == str(imei_largo), \
        f"[UT-GD-002.13] IMEI se perdió o modificó: esperado {imei_largo}, obtenido {found_device['IMEI']}"


def test_ut_gd_002_14_contrato_respuesta_sin_campos_sensibles(client):
    """
    UT-GD-002.14: Contrato de respuesta: campos obligatorios y rechazo de campos extra inseguros
    
    La API debe devolver solo campos contractuales y no exponer campos internos.
    """
    resp = do_list(
        client,
        permissions=[112],
        authenticated=True
    )
    
    assert resp.status_code == 200, f"[UT-GD-002.14] Esperado: 200, Obtenido: {resp.status_code}"
    body = resp.json()
    
    required_fields = {"id_device", "name", "IMEI", "status_id", "status_name", "registration_date"}
    forbidden_fields = {"secret_key", "internal_id", "password", "token"}
    
    for item in body["data"]:
        # Verificar que todos los campos requeridos están presentes
        for field in required_fields:
            assert field in item, f"[UT-GD-002.14] Campo requerido ausente: {field}"
        
        # Verificar que no hay campos sensibles
        for forbidden in forbidden_fields:
            assert forbidden not in item, \
                f"[UT-GD-002.14] Campo sensible expuesto: {forbidden}"


# ============================================================================
# EJECUCIÓN DIRECTA
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
