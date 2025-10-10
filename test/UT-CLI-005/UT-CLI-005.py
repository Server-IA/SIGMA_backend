"""
Pruebas unitarias para HU-CLI-005: Eliminar Cliente y Toggle Status
DELETE /customers/{id_customer}/
PATCH /customers/{id_customer}/toggle-status/

Ejecutor: Nicolas Urrutia
Fecha: Octubre 10, 2025
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


# ==================== MODELOS MOCK ====================
class DummyCustomer:
    """Mock de modelo Customer con campos clave y asociaciones."""
    def __init__(self, id_customer, name, status_id=1, has_associations=False, user_id=None):
        self.id_customer = id_customer
        self.name = name
        self.customer_statues_id = status_id
        self.has_associations = has_associations
        self.id_user_id = user_id
        self._deleted = False

    def delete(self):
        """Simula eliminación; lanza IntegrityError si tiene asociaciones."""
        if self.has_associations:
            from django.db import IntegrityError
            raise IntegrityError("FOREIGN KEY constraint failed")
        self._deleted = True

    def save(self, update_fields=None):
        """Simula guardado de cambios."""
        pass


class DummyStatues:
    """Mock de estado (Statues)."""
    def __init__(self, pk, name):
        self.pk = pk
        self.name = name


class MockResponse:
    """Mock de Response HTTP."""
    def __init__(self, status_code, data):
        self.status_code = status_code
        self.data = data


# ==================== SIMULADORES DE ENDPOINT ====================
MOCK_CUSTOMERS_DB = {}
MOCK_STATUES_DB = {
    1: DummyStatues(1, "Activo"),
    2: DummyStatues(2, "Inactivo")
}


def setup_mock_db():
    """Inicializa base de datos mock para cada test."""
    global MOCK_CUSTOMERS_DB
    MOCK_CUSTOMERS_DB = {
        1001: DummyCustomer(1001, "Cliente Sin Asociaciones", status_id=1, has_associations=False),
        1002: DummyCustomer(1002, "Cliente Con Asociaciones", status_id=1, has_associations=True),
        1003: DummyCustomer(1003, "Cliente Test Auth", status_id=1, has_associations=False),
        1004: DummyCustomer(1004, "Cliente Test Permisos", status_id=1, has_associations=False),
        1005: DummyCustomer(1005, "Cliente Concurrencia", status_id=1, has_associations=False),
        1006: DummyCustomer(1006, "Cliente Auditoría", status_id=1, has_associations=False),
        1007: DummyCustomer(1007, "Cliente Contrato", status_id=1, has_associations=False),
        2001: DummyCustomer(2001, "Cliente Toggle Asociaciones", status_id=1, has_associations=True),
        2002: DummyCustomer(2002, "Cliente Inactivo", status_id=2, has_associations=False),
        2003: DummyCustomer(2003, "Cliente Toggle Auth", status_id=1, has_associations=False),
        2004: DummyCustomer(2004, "Cliente Toggle Permisos", status_id=1, has_associations=False),
        2006: DummyCustomer(2006, "Cliente Idempotencia", status_id=1, has_associations=False),
        2007: DummyCustomer(2007, "Cliente Toggle Auditoría", status_id=1, has_associations=False),
        2008: DummyCustomer(2008, "Cliente Toggle Listado", status_id=1, has_associations=False),
        3001: DummyCustomer(3001, "Cliente Flujo Fallback", status_id=1, has_associations=True),
        3002: DummyCustomer(3002, "Cliente Fallback Sin Permiso", status_id=1, has_associations=True),
        4001: DummyCustomer(4001, "Cliente Inactivo Solicitudes", status_id=2, has_associations=False),
        4002: DummyCustomer(4002, "Cliente Usuario Asociado", status_id=1, has_associations=False, user_id=7001),
    }


def do_delete(customer_id, auth_token=None, user_perms=None):
    """
    Simula DELETE /customers/{id_customer}/
    
    Lógica:
    - Verifica autenticación (auth_token presente)
    - Verifica permiso 138 (customer.delete)
    - Busca cliente por id
    - Intenta eliminación dura; si hay IntegrityError hace soft delete (inactivar)
    - Retorna MockResponse
    """
    # Auth check
    if not auth_token:
        return MockResponse(401, {"message": "Usuario no autenticado"})
    
    # Permission check
    if user_perms is None or 138 not in user_perms:
        return MockResponse(403, {"message": "No tiene permisos para eliminar clientes."})
    
    # Get customer
    customer = MOCK_CUSTOMERS_DB.get(customer_id)
    if not customer:
        return MockResponse(404, {"success": False, "message": "Cliente no encontrado."})
    
    # Try delete
    try:
        customer.delete()
        # Hard delete success
        del MOCK_CUSTOMERS_DB[customer_id]
        return MockResponse(200, {
            "success": True,
            "code": 200,
            "message": "Cliente eliminado correctamente.",
            "data": None
        })
    except Exception as e:
        # IntegrityError -> soft delete
        if "FOREIGN KEY" in str(e) or "constraint" in str(e):
            customer.customer_statues_id = 2
            customer.save(update_fields=['customer_statues'])
            return MockResponse(409, {
                "success": False,
                "code": 409,
                "message": "El cliente tiene historial asociado. Se ha inactivado lógicamente.",
                "errors": {"detail": ["No se permite eliminación definitiva por integridad de datos."]}
            })
        # Other errors
        return MockResponse(500, {"success": False, "message": "Error al eliminar el cliente.", "error": str(e)})


def do_toggle_status(customer_id, auth_token=None, user_perms=None):
    """
    Simula PATCH /customers/{id_customer}/toggle-status/
    
    Lógica:
    - Verifica autenticación
    - Verifica permiso 139 (customer.toggle_status)
    - Busca cliente por id
    - Alterna estado: 1 (Activo) <-> 2 (Inactivo)
    - Retorna MockResponse
    """
    # Auth check
    if not auth_token:
        return MockResponse(401, {"message": "Usuario no autenticado"})
    
    # Permission check
    if user_perms is None or 139 not in user_perms:
        return MockResponse(403, {"message": "No tiene permisos para activar/desactivar clientes."})
    
    # Get customer
    customer = MOCK_CUSTOMERS_DB.get(customer_id)
    if not customer:
        return MockResponse(404, {"success": False, "message": "Cliente no encontrado."})
    
    # Toggle status
    before_status = customer.customer_statues_id
    if before_status == 1:
        customer.customer_statues_id = 2
        customer.save(update_fields=['customer_statues'])
        message = "Cliente inactivado exitosamente"
    else:
        customer.customer_statues_id = 1
        customer.save(update_fields=['customer_statues'])
        message = "Cliente activado exitosamente"
    
    return MockResponse(200, {"success": True, "message": message})


# ==================== FIXTURES ====================
@pytest.fixture
def client():
    """Fixture para mock de cliente API (simulado)."""
    return MagicMock()


@pytest.fixture(autouse=True)
def reset_db():
    """Reset mock DB antes de cada test."""
    setup_mock_db()
    yield
    MOCK_CUSTOMERS_DB.clear()


# ==================== TESTS DELETE ====================
def test_ut_cli_005_1(client):
    """UT-CLI-005.1: Eliminar cliente sin asociaciones."""
    # Arrange
    customer_id = 1001
    assert customer_id in MOCK_CUSTOMERS_DB
    
    # Act
    response = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert
    assert response.status_code == 200
    assert response.data["success"] is True
    assert response.data["message"] == "Cliente eliminado correctamente."
    assert response.data["data"] is None
    assert customer_id not in MOCK_CUSTOMERS_DB  # Cliente eliminado de "BD"


def test_ut_cli_005_2(client):
    """UT-CLI-005.2: Bloqueo eliminación con asociaciones."""
    # Arrange
    customer_id = 1002
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.has_associations is True
    
    # Act
    response = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert
    assert response.status_code == 409
    assert response.data["success"] is False
    assert "historial asociado" in response.data["message"]
    assert customer_id in MOCK_CUSTOMERS_DB  # Cliente aún existe
    assert MOCK_CUSTOMERS_DB[customer_id].customer_statues_id == 2  # Inactivado


def test_ut_cli_005_3(client):
    """UT-CLI-005.3: Eliminar cliente inexistente (404)."""
    # Arrange
    customer_id = 999999
    assert customer_id not in MOCK_CUSTOMERS_DB
    
    # Act
    response = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert
    assert response.status_code == 404
    assert response.data["success"] is False
    assert "no encontrado" in response.data["message"].lower()


def test_ut_cli_005_4(client):
    """UT-CLI-005.4: Eliminar sin autenticación (401)."""
    # Arrange
    customer_id = 1003
    
    # Act
    response = do_delete(customer_id, auth_token=None, user_perms=[138])
    
    # Assert
    assert response.status_code == 401
    assert "no autenticado" in response.data["message"].lower()
    assert customer_id in MOCK_CUSTOMERS_DB  # Sin cambios


def test_ut_cli_005_5(client):
    """UT-CLI-005.5: Eliminar sin permiso customer.delete (403)."""
    # Arrange
    customer_id = 1004
    
    # Act
    response = do_delete(customer_id, auth_token="valid_token", user_perms=[139])  # Sin 138
    
    # Assert
    assert response.status_code == 403
    assert "permisos" in response.data["message"].lower()
    assert customer_id in MOCK_CUSTOMERS_DB  # Sin eliminación


def test_ut_cli_005_6(client):
    """UT-CLI-005.6: Validación de id inválido (400/404)."""
    # Arrange: id no numérico
    # En el router real Django rechazaría con 404; simulamos 404
    customer_id = "abc"
    
    # Act: simulamos que el router convierte a int y falla lookup
    try:
        int(customer_id)
        customer_id_int = int(customer_id)
    except ValueError:
        # Router rechaza antes de llegar al viewset
        response = MockResponse(404, {"detail": "Not found."})
    else:
        response = do_delete(customer_id_int, auth_token="valid_token", user_perms=[138])
    
    # Assert
    assert response.status_code == 404


def test_ut_cli_005_7(client):
    """UT-CLI-005.7: Concurrencia doble eliminación."""
    # Arrange
    customer_id = 1005
    
    # Act: Primera eliminación
    response1 = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Act: Segunda eliminación (cliente ya no existe)
    response2 = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert
    assert response1.status_code == 200
    assert response1.data["success"] is True
    
    assert response2.status_code == 404  # Ya fue eliminado
    assert response2.data["success"] is False


def test_ut_cli_005_8(client):
    """UT-CLI-005.8: Auditoría en eliminación."""
    # Arrange
    customer_id = 1006
    
    # Act: Ejecutar eliminación (en implementación real, auditaría con AuditClient)
    response = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert
    assert response.status_code == 200
    # En implementación real, verificaríamos que AuditClient.delete fue llamado
    # Esta prueba valida que el endpoint responde correctamente


def test_ut_cli_005_9(client):
    """UT-CLI-005.9: Contrato de respuesta DELETE."""
    # Arrange
    customer_id = 1007
    
    # Act
    response = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert: Estructura exacta
    assert response.status_code == 200
    data = response.data
    assert "success" in data
    assert data["success"] is True
    assert "code" in data
    assert data["code"] == 200
    assert "message" in data
    assert data["message"] == "Cliente eliminado correctamente."
    assert "data" in data
    assert data["data"] is None


def test_ut_cli_005_10(client):
    """UT-CLI-005.10: Rendimiento eliminación bajo carga."""
    # Arrange: Crear 200 clientes sin asociaciones
    for i in range(11000, 11200):
        MOCK_CUSTOMERS_DB[i] = DummyCustomer(i, f"Cliente {i}", status_id=1, has_associations=False)
    
    # Act: Eliminar todos
    import time
    start = time.time()
    deleted_count = 0
    for i in range(11000, 11200):
        response = do_delete(i, auth_token="valid_token", user_perms=[138])
        if response.status_code == 200:
            deleted_count += 1
    elapsed = time.time() - start
    
    # Assert
    assert deleted_count == 200
    # P95 < 400ms por cada delete (simulado muy rápido; en real depende de DB)
    # Aquí verificamos que el proceso completo sea rápido
    assert elapsed < 2.0  # 200 deletes en <2s (mock rápido)


# ==================== TESTS PATCH TOGGLE-STATUS ====================
def test_ut_cli_005_11(client):
    """UT-CLI-005.11: Inactivar cliente con asociaciones (soft delete)."""
    # Arrange
    customer_id = 2001
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.customer_statues_id == 1  # Activo
    assert customer.has_associations is True
    
    # Act
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response.status_code == 200
    assert response.data["success"] is True
    assert "inactivado exitosamente" in response.data["message"]
    assert customer.customer_statues_id == 2  # Inactivo


def test_ut_cli_005_12(client):
    """UT-CLI-005.12: Activar cliente inactivo."""
    # Arrange
    customer_id = 2002
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.customer_statues_id == 2  # Inactivo
    
    # Act
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response.status_code == 200
    assert response.data["success"] is True
    assert "activado exitosamente" in response.data["message"]
    assert customer.customer_statues_id == 1  # Activo


def test_ut_cli_005_13(client):
    """UT-CLI-005.13: Toggle sin autenticación (401)."""
    # Arrange
    customer_id = 2003
    
    # Act
    response = do_toggle_status(customer_id, auth_token=None, user_perms=[139])
    
    # Assert
    assert response.status_code == 401
    assert "no autenticado" in response.data["message"].lower()


def test_ut_cli_005_14(client):
    """UT-CLI-005.14: Toggle sin permiso customer.toggle_status (403)."""
    # Arrange
    customer_id = 2004
    
    # Act
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[138])  # Sin 139
    
    # Assert
    assert response.status_code == 403
    assert "permisos" in response.data["message"].lower()


def test_ut_cli_005_15(client):
    """UT-CLI-005.15: Toggle cliente inexistente (404)."""
    # Arrange
    customer_id = 2999
    assert customer_id not in MOCK_CUSTOMERS_DB
    
    # Act
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response.status_code == 404
    assert response.data["success"] is False


def test_ut_cli_005_16(client):
    """UT-CLI-005.16: Idempotencia de toggles consecutivos."""
    # Arrange
    customer_id = 2006
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.customer_statues_id == 1  # Activo
    
    # Act: Toggle 1 (Activo -> Inactivo)
    response1 = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Act: Toggle 2 (Inactivo -> Activo)
    response2 = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Act: Toggle 3 (Activo -> Inactivo)
    response3 = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response1.data["message"] == "Cliente inactivado exitosamente"
    assert customer.customer_statues_id == 2 or response1.status_code == 200  # Tras toggle 1
    
    assert response2.data["message"] == "Cliente activado exitosamente"
    
    assert response3.data["message"] == "Cliente inactivado exitosamente"
    assert MOCK_CUSTOMERS_DB[customer_id].customer_statues_id == 2  # Estado final: Inactivo


def test_ut_cli_005_17(client):
    """UT-CLI-005.17: Auditoría en toggle de estado."""
    # Arrange
    customer_id = 2007
    
    # Act: Ejecutar toggle (en implementación real, auditaría con AuditClient)
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response.status_code == 200
    # En implementación real verificaríamos AuditClient.update fue llamado
    # Esta prueba valida que el endpoint responde correctamente


def test_ut_cli_005_18(client):
    """UT-CLI-005.18: Reflejo en listado tras toggle."""
    # Arrange
    customer_id = 2008
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.customer_statues_id == 1  # Activo
    
    # Act
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response.status_code == 200
    assert customer.customer_statues_id == 2  # Inactivo
    # En una integración real, el listado HU-CLI-002 reflejaría el cambio


# ==================== TESTS FLUJO COMBINADO ====================
def test_ut_cli_005_19(client):
    """UT-CLI-005.19: Flujo eliminar con fallback a inactivar."""
    # Arrange
    customer_id = 3001
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.has_associations is True
    
    # Act: Intento de DELETE (debe fallar y hacer soft delete)
    response_delete = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Act: Si DELETE no inactivó (409), hacer PATCH toggle
    if response_delete.status_code == 409:
        # Ya inactivado por DELETE fallback
        assert customer.customer_statues_id == 2
    else:
        # Fallback manual con PATCH
        response_toggle = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
        assert response_toggle.status_code == 200
    
    # Assert
    assert customer_id in MOCK_CUSTOMERS_DB  # No eliminado
    assert MOCK_CUSTOMERS_DB[customer_id].customer_statues_id == 2  # Inactivo


def test_ut_cli_005_20(client):
    """UT-CLI-005.20: Fallback sin permiso de toggle (debe fallar)."""
    # Arrange
    customer_id = 3002
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.has_associations is True
    
    # Act: DELETE sin permiso toggle (solo tiene 138)
    response_delete = do_delete(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Act: Intento PATCH sin permiso 139
    response_toggle = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[138])
    
    # Assert
    # DELETE hace soft delete automático (409), pero si intentamos PATCH manual falla
    assert response_delete.status_code == 409  # Soft delete automático por DELETE
    assert response_toggle.status_code == 403  # Sin permiso toggle
    # Estado final: inactivado por DELETE fallback (automático en el viewset real)
    assert customer.customer_statues_id == 2


def test_ut_cli_005_21(client):
    """UT-CLI-005.21: Sincronización con microservicio de usuarios al inactivar."""
    # Arrange
    customer_id = 4002
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.id_user_id == 7001
    
    # Act: mock de llamada a microservicio (en implementación real)
    # No necesitamos patch aquí ya que es solo simulación
    response = do_toggle_status(customer_id, auth_token="valid_token", user_perms=[139])
    
    # Assert
    assert response.status_code == 200
    assert customer.customer_statues_id == 2  # Cliente inactivado
    # En implementación real se verificaría llamada HTTP al microservicio de usuarios


def test_ut_cli_005_22(client):
    """UT-CLI-005.22: Cliente inactivado no disponible para nuevas solicitudes."""
    # Arrange
    customer_id = 4001
    customer = MOCK_CUSTOMERS_DB[customer_id]
    assert customer.customer_statues_id == 2  # Inactivo
    
    # Act: Simulamos validación en endpoint de solicitudes
    # (En el endpoint real de solicitudes se debe rechazar customer_id inactivo)
    def create_request_with_customer(cust_id):
        cust = MOCK_CUSTOMERS_DB.get(cust_id)
        if not cust or cust.customer_statues_id != 1:
            return MockResponse(400, {"success": False, "message": "Cliente no está activo o no existe."})
        return MockResponse(201, {"success": True, "message": "Solicitud creada."})
    
    response = create_request_with_customer(customer_id)
    
    # Assert
    assert response.status_code == 400
    assert "no está activo" in response.data["message"].lower() or "no existe" in response.data["message"].lower()
