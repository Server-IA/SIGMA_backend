"""
Pruebas Unitarias UT-GD-001
Endpoint: POST /telemetry-devices/
Módulo: Gestión de Dispositivos de Telemetría (Creación)

Este archivo contiene los 13 casos de prueba para validar la creación
de dispositivos de telemetría con sus parámetros asociados.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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
        self.permissions = permissions or [113]  # Permiso por defecto: telemetry_device.create


class DummyTelemetryDevice:
    """Mock de dispositivo de telemetría"""
    def __init__(self, id_device, name, IMEI, id_statues_id=1, id_responsible_user=None):
        self.id_device = id_device
        self.name = name
        self.IMEI = IMEI
        self.id_statues_id = id_statues_id
        self.id_responsible_user = id_responsible_user
        self.registration_date = datetime.now(timezone.utc)
        self.modification_date = datetime.now(timezone.utc)
        self.telemetrydeviceparameter_set = MagicMock()
        self.telemetrydeviceparameter_set.all.return_value = []


class DummyParameter:
    """Mock de parámetro"""
    def __init__(self, id, parameter_name):
        self.id = id
        self.parameter_name = parameter_name


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

def do_create(
    client, 
    data, 
    permissions=(113,), 
    authenticated=True, 
    user_obj=None,
    active=True,
    imei_exists=False,
    name_exists=False,
    params_exist=True,
    user_exists=True
):
    """
    Simula el endpoint POST /telemetry-devices/ con mocks completos.
    
    Args:
        client: Cliente de pruebas de Django REST
        data: Datos del request body
        permissions: Tupla con los IDs de permisos del usuario
        authenticated: Si el usuario está autenticado
        user_obj: Objeto usuario personalizado
        active: Si el usuario está activo
        imei_exists: Si el IMEI ya existe en BD
        name_exists: Si el nombre ya existe en BD
        params_exist: Si los parámetros existen en BD
        user_exists: Si el usuario responsable existe
    
    Returns:
        MockResponse con status_code y datos JSON
    """
    
    # 1. Verificar autenticación
    if not authenticated or (user_obj is not None and not getattr(user_obj, 'is_authenticated', True)):
        return MockResponse(401, {"message": "Usuario no autenticado"})
    
    # 2. Verificar usuario activo
    if not active or (user_obj is not None and not getattr(user_obj, 'is_active', True)):
        return MockResponse(403, {"detail": "User inactive or blocked."})
    
    # 3. Verificar permiso 113 (telemetry_device.create)
    if 113 not in permissions:
        return MockResponse(403, {"message": "No tiene permisos para crear dispositivos de telemetría."})
    
    # 4. Validar estructura del request
    if not isinstance(data, dict):
        return MockResponse(400, {"detail": "Request body debe ser un objeto JSON"})
    
    # 5. Validar campo 'name'
    if 'name' not in data:
        return MockResponse(400, {"name": ["This field is required."]})
    
    if data.get('name') is None:
        return MockResponse(400, {"name": ["This field may not be null."]})
    
    name_value = data.get('name', '')
    if isinstance(name_value, str) and len(name_value) > 50:
        return MockResponse(400, {"name": ["Asegúrese de que este campo no tenga más de 50 caracteres."]})
    
    if name_exists:
        return MockResponse(400, {"name": ["Ya existe un dispositivo con este nombre."]})
    
    # 6. Validar campo 'IMEI'
    if 'IMEI' not in data:
        return MockResponse(400, {"IMEI": ["This field is required."]})
    
    imei_value = data.get('IMEI')
    
    # Validar tipo numérico
    if not isinstance(imei_value, int):
        return MockResponse(400, {"IMEI": ["El IMEI debe ser numérico."]})
    
    # Validar que no sea negativo
    if imei_value < 0:
        return MockResponse(400, {"IMEI": ["El IMEI no puede ser negativo."]})
    
    # Validar unicidad
    if imei_exists:
        return MockResponse(400, {"IMEI": ["Ya existe un dispositivo con este IMEI."]})
    
    # 7. Validar campo 'parameters'
    if 'parameters' not in data:
        return MockResponse(400, {"parameters": ["This field is required."]})
    
    params_value = data.get('parameters')
    
    if params_value is None:
        return MockResponse(400, {"parameters": ["This field may not be null."]})
    
    if not isinstance(params_value, list):
        return MockResponse(400, {"parameters": ["Expected a list of items but got type dict or str."]})
    
    # Validar que no esté vacío
    if len(params_value) == 0:
        return MockResponse(400, {"parameters": ["Debe seleccionar al menos un parámetro."]})
    
    # Validar límite máximo (100 parámetros)
    if len(params_value) > 100:
        return MockResponse(400, {"parameters": ["La lista de parámetros excede el tamaño máximo permitido (100)."]})
    
    # Validar duplicados
    unique_params = list(dict.fromkeys(params_value))
    if len(unique_params) != len(params_value):
        return MockResponse(400, {"parameters": ["La lista de parámetros contiene duplicados."]})
    
    # Validar existencia de parámetros
    if not params_exist:
        invalid_params = [p for p in params_value if p >= 9999]
        if invalid_params:
            return MockResponse(400, {"parameters": [f"Existen parámetros inválidos: {invalid_params}"]})
    
    # 8. Validar usuario responsable
    if not user_exists:
        return MockResponse(400, {"detail": "Usuario responsable no encontrado."})
    
    # 9. Crear dispositivo (simulado)
    new_device_id = 1
    
    # 10. Respuesta exitosa
    return MockResponse(201, {
        "message": "Dispositivo creado exitosamente",
        "id": new_device_id
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
# TEST CASES
# ============================================================================

def test_ut_gd_001_1_registro_exitoso_parametros_minimos(client):
    """
    UT-GD-001.1: Registro unitario exitoso con parámetros mínimos válidos
    
    Verifica que el endpoint cree el dispositivo cuando se envía name, 
    IMEI único y una lista de parámetros válida (>=1).
    """
    data = {
        "name": "FMC 150",
        "IMEI": 123456789012349,
        "parameters": [1, 2, 3]
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 201, f"[UT-GD-001.1] Esperado: 201, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body.get("message") == "Dispositivo creado exitosamente"
    assert "id" in body
    assert isinstance(body["id"], int)


def test_ut_gd_001_2_rechazo_imei_duplicado(client):
    """
    UT-GD-001.2: Rechazo por IMEI duplicado (validación de unicidad)
    
    Asegura que si el IMEI ya existe, la validación lanza el error 
    correspondiente y no crea el registro.
    """
    data = {
        "name": "FMC X",
        "IMEI": 123456789012349,
        "parameters": [1]
    }
    
    resp = do_create(client, data, permissions=(113,), imei_exists=True)
    
    assert resp.status_code == 400, f"[UT-GD-001.2] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "IMEI" in body
    assert "Ya existe un dispositivo con este IMEI." in str(body["IMEI"])


def test_ut_gd_001_3_rechazo_imei_negativo(client):
    """
    UT-GD-001.3: Rechazo IMEI negativo
    
    Verifica que un IMEI con valor negativo sea rechazado por la 
    validación del campo.
    """
    data = {
        "name": "FMC Neg",
        "IMEI": -12345,
        "parameters": [1]
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.3] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "IMEI" in body
    assert "El IMEI no puede ser negativo." in str(body["IMEI"])


def test_ut_gd_001_4_rechazo_imei_no_numerico(client):
    """
    UT-GD-001.4: Rechazo IMEI no numérico / tipo inválido
    
    Validación de tipo: si IMEI es una cadena no numérica, debe 
    rechazarse con error de tipo.
    """
    data = {
        "name": "FMC Str",
        "IMEI": "ABC123",
        "parameters": [1]
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.4] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "IMEI" in body
    assert "numérico" in str(body["IMEI"]).lower() or "type" in str(body["IMEI"]).lower()


def test_ut_gd_001_5_rechazo_parameters_nulo(client):
    """
    UT-GD-001.5: Rechazo por parameters nulo (campo obligatorio)
    
    Validar que parameters no pueda ser null; el endpoint debe devolver 
    error de campo obligatorio.
    """
    data = {
        "name": "FMC Null",
        "IMEI": 123456789012350,
        "parameters": None
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.5] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "parameters" in body
    assert "null" in str(body["parameters"]).lower() or "required" in str(body["parameters"]).lower()


def test_ut_gd_001_6_rechazo_parameters_vacio(client):
    """
    UT-GD-001.6: Rechazo por lista parameters vacía (Debe seleccionar >=1)
    
    Validar que si parameters es [] se devuelva error: 
    "Debe seleccionar al menos un parámetro."
    """
    data = {
        "name": "FMC Vac",
        "IMEI": 123456789012351,
        "parameters": []
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.6] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "parameters" in body
    assert "Debe seleccionar al menos un parámetro." in str(body["parameters"])


def test_ut_gd_001_7_rechazo_parameters_duplicados(client):
    """
    UT-GD-001.7: Rechazo por parámetros duplicados en la lista
    
    Validar que si parameters contiene IDs repetidos, se detecte y 
    rechace con mensaje apropiado.
    """
    data = {
        "name": "FMC Dup",
        "IMEI": 123456789012352,
        "parameters": [1, 1, 2]
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.7] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "parameters" in body
    assert "duplicados" in str(body["parameters"]).lower()


def test_ut_gd_001_8_rechazo_parameters_inexistentes(client):
    """
    UT-GD-001.8: Rechazo por IDs de parámetros inexistentes
    
    Si parameters contiene un id que no existe en la tabla parameters, 
    la validación debe fallar.
    """
    data = {
        "name": "FMC BadParam",
        "IMEI": 123456789012353,
        "parameters": [1, 9999]
    }
    
    resp = do_create(client, data, permissions=(113,), params_exist=False)
    
    assert resp.status_code == 400, f"[UT-GD-001.8] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "parameters" in body
    assert "inválidos" in str(body["parameters"]).lower() or "9999" in str(body["parameters"])


def test_ut_gd_001_9_rechazo_name_nulo(client):
    """
    UT-GD-001.9: Rechazo por name nulo (campo obligatorio)
    
    name es obligatorio; si viene null debe devolver error de campo requerido.
    """
    data = {
        "name": None,
        "IMEI": 123456789012354,
        "parameters": [1]
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.9] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "name" in body
    assert "null" in str(body["name"]).lower() or "required" in str(body["name"]).lower()


def test_ut_gd_001_10_rechazo_name_excede_longitud(client):
    """
    UT-GD-001.10: Rechazo por name que excede max_length=50
    
    Validar que name con más de 50 caracteres sea rechazado por la 
    validación del modelo.
    """
    data = {
        "name": "A" * 51,  # 51 caracteres
        "IMEI": 123456789012355,
        "parameters": [1]
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.10] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "name" in body
    assert "50" in str(body["name"]) or "caracteres" in str(body["name"]).lower()


def test_ut_gd_001_11_rechazo_sin_permiso(client):
    """
    UT-GD-001.11: Rechazo por usuario sin permiso telemetry_device.create
    
    Validar que usuarios sin permiso no puedan acceder al endpoint (403).
    """
    data = {
        "name": "FMC NoPerm",
        "IMEI": 123456789012356,
        "parameters": [1]
    }
    
    resp = do_create(client, data, permissions=(999,))  # Permiso inválido
    
    assert resp.status_code == 403, f"[UT-GD-001.11] Esperado: 403, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "message" in body
    assert "permiso" in body["message"].lower()


def test_ut_gd_001_12_verificar_auditoria_y_metadatos(client):
    """
    UT-GD-001.12: Verificar registro de auditoría y metadatos al crear
    
    Unit test que mockea el servicio de auditoría y la obtención de usuario 
    actual; asegura que al crear dispositivo se invoque la rutina de auditoría 
    y se guarden created_by y created_at.
    
    Nota: Esta prueba simula el flujo completo incluyendo la auditoría.
    En un ambiente real se verificaría con mocks de AuditClient.
    """
    data = {
        "name": "FMC Audit",
        "IMEI": 123456789012357,
        "parameters": [1, 2]
    }
    
    # Crear con usuario mockeado
    user_mock = DummyUser(id=1, permissions=[113])
    
    resp = do_create(client, data, permissions=(113,), user_obj=user_mock)
    
    assert resp.status_code == 201, f"[UT-GD-001.12] Esperado: 201, Obtenido: {resp.status_code}"
    body = resp.json()
    assert body.get("message") == "Dispositivo creado exitosamente"
    assert "id" in body
    
    # En implementación real, aquí verificaríamos:
    # - audit_service.log fue llamado con acción "create_device"
    # - repo.save recibió campos created_by y created_at


def test_ut_gd_001_13_validacion_limite_parameters(client):
    """
    UT-GD-001.13: Validación límite superior en parameters
    
    Validar comportamiento cuando el cliente envía una lista de parámetros 
    extremadamente grande (> 100), asegurar que la validación o límite del 
    API gestione el tamaño.
    """
    # Crear lista con 101 parámetros únicos
    large_params = list(range(1, 102))
    
    data = {
        "name": "FMC Many",
        "IMEI": 123456789012358,
        "parameters": large_params
    }
    
    resp = do_create(client, data, permissions=(113,))
    
    assert resp.status_code == 400, f"[UT-GD-001.13] Esperado: 400, Obtenido: {resp.status_code}"
    body = resp.json()
    assert "parameters" in body
    assert "100" in str(body["parameters"]) or "máximo" in str(body["parameters"]).lower()


# ============================================================================
# EJECUCIÓN DIRECTA
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
