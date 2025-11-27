"""
Pruebas Unitarias UT-GD-003
Endpoint: PUT /telemetry-devices/{id}/
Módulo: Gestión de Dispositivos de Telemetría (Actualización)

Este archivo contiene los casos de prueba para validar la actualización
de dispositivos de telemetría con validaciones de permisos, campos obligatorios,
validaciones de negocio y manejo de errores.
"""

import pytest
import os
from unittest.mock import Mock
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from django.db import transaction
import jwt

# Models
from users.models.user import User
from machinery.models.telemetry_devices import TelemetryDevices
from machinery.models.telemetry_device_parameter import TelemetryDeviceParameter
from machinery.models.parameters import Parameters
from parameterization.models.statues import Statues
from parameterization.models.statues_category import StatuesCategory


# ============================================================================
# HELPER FUNCTIONS FOR JWT AUTHENTICATION
# ============================================================================

def _ensure_jwt_secret_for_tests():
    """Configura JWT_SECRET para pruebas"""
    if not os.getenv("JWT_SECRET"):
        os.environ["JWT_SECRET"] = "test_secret_key_for_jwt_authentication_in_tests_only"


def _make_jwt(payload, expired=False):
    """Crea un JWT token para pruebas"""
    import time
    _ensure_jwt_secret_for_tests()
    secret = os.getenv("JWT_SECRET")
    if expired:
        payload["exp"] = 0  # Token expirado
    else:
        payload["exp"] = int(time.time()) + 3600  # Expira en 1 hora
    return jwt.encode(payload, secret, algorithm="HS256")


def _auth_header_for(perms_ids):
    """Genera Authorization header con permisos específicos"""
    payload = {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "rol": [{
            "id": 1,
            "name": "Admin",
            "permisos": [{"id": perm_id} for perm_id in perms_ids]
        }]
    }
    token = _make_jwt(payload)
    return f"Bearer {token}"


# ============================================================================
# PYTEST MARKER
# ============================================================================

@pytest.mark.django_db
class TestTelemetryDeviceUpdate:
    """Pruebas para el endpoint PUT /telemetry-devices/{id}/"""
    
    endpoint_base = "/telemetry-devices/"
    permission_id = 114  # telemetry_device.update
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Configurar JWT
        _ensure_jwt_secret_for_tests()
        
        # Crear usuario responsable
        self.user, created = User.objects.get_or_create(id_user=1)
        self.user.is_authenticated = True
        self.user.id = self.user.id_user
        
        # Crear datos de parametrización necesarios
        self._setup_parametrization()
        
        # Crear dispositivo de prueba con ID 11
        self.test_device = self._create_test_device(
            id_device=11,
            name="FMC 150",
            imei=123456789012345,
            status_id=1
        )
        
        # Dispositivos adicionales para validación de duplicidad
        self.device_for_duplicate_name = self._create_test_device(
            id_device=20,
            name="FMC Dispositivo Existente",
            imei=999999999999998,
            status_id=1
        )
        
        self.device_for_duplicate_imei = self._create_test_device(
            id_device=21,
            name="Device Duplicate IMEI",
            imei=999999999999999,
            status_id=1
        )
    
    def teardown_method(self):
        """Limpieza después de cada prueba"""
        # Limpiar dispositivos creados (pero mantener datos de parametrización)
        TelemetryDeviceParameter.objects.all().delete()
        TelemetryDevices.objects.exclude(id_device__in=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).delete()
    
    def _setup_parametrization(self):
        """Inicializa datos de parametrización necesarios"""
        # Crear categoría de estados
        self.statues_category, created = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': 'Estados Generales',
                'description': 'Estados generales del sistema',
                'modification_date': self.now,
                'creation_date': self.now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear estados
        self.active_status, created = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                'name': 'Activo',
                'description': 'Estado activo',
                'id_statues_categories': self.statues_category,
                'modification_date': self.now,
                'creation_date': self.now,
                'id_responsible_user': self.user
            }
        )
        
        self.inactive_status, created = Statues.objects.get_or_create(
            id_statues=2,
            defaults={
                'name': 'Inactivo',
                'description': 'Estado inactivo',
                'id_statues_categories': self.statues_category,
                'modification_date': self.now,
                'creation_date': self.now,
                'id_responsible_user': self.user
            }
        )
        
        # Crear parámetros de monitoreo (IDs 1-16)
        self.parameters = []
        parameter_names = [
            "Estado de Ignición",
            "Estado de Movimiento",
            "Velocidad Actual",
            "Ubicación GPS",
            "GSM señal",
            "Revoluciones (RPM)",
            "Temperatura del Motor",
            "Carga del Motor",
            "Nivel de Aceite",
            "Nivel de Combustible",
            "Combustible Usado (GPS)",
            "Consumo instantáneo",
            "Fallas OBD",
            "Odómetro Total",
            "Odómetro del Viaje",
            "Eventos - Valor G de Evento"
        ]
        
        for idx, name in enumerate(parameter_names, start=1):
            param, created = Parameters.objects.get_or_create(
                id=idx,
                defaults={
                    'parameter_name': name,
                    'avl_id_parameter': idx  # Campo requerido
                }
            )
            self.parameters.append(param)
    
    def _create_test_device(self, id_device, name, imei, status_id=1):
        """Crea un dispositivo de telemetría para pruebas"""
        try:
            device = TelemetryDevices.objects.get(id_device=id_device)
            # Actualizar campos si ya existe
            device.name = name
            device.IMEI = imei
            device.id_statues_id = status_id
            device.save()
            return device
        except TelemetryDevices.DoesNotExist:
            device = TelemetryDevices.objects.create(
                id_device=id_device,
                name=name,
                IMEI=imei,
                id_statues_id=status_id,
                id_responsible_user=self.user
            )
            return device
    
    def _associate_parameters_to_device(self, device, param_ids):
        """Asocia parámetros a un dispositivo"""
        # Eliminar parámetros existentes
        TelemetryDeviceParameter.objects.filter(telemetry_device=device).delete()
        
        # Crear nuevas asociaciones
        for param_id in param_ids:
            TelemetryDeviceParameter.objects.create(
                telemetry_device=device,
                parameter_id=param_id
            )
    
    # ============================================================================
    # TEST CASES
    # ============================================================================
    
    def test_ut_gd_003_1_actualizacion_exitosa(self):
        """
        UT-GD-003.1: Actualización exitosa con datos válidos
        
        Verifica que el endpoint actualiza correctamente un dispositivo con
        datos válidos y retorna HTTP 200 con estructura JSON correcta.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC 155",
            "IMEI": 123456789012348,
            "parameters": [1, 2, 3, 4, 5]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK, \
            f"[UT-GD-003.1] Esperado: 200, Obtenido: {response.status_code}"
        
        body = response.json()
        assert body.get("success") is True, \
            f"[UT-GD-003.1] Expected success=True, got: {body.get('success')}"
        assert body.get("message") == "Dispositivo actualizado exitosamente", \
            f"[UT-GD-003.1] Mensaje incorrecto: {body.get('message')}"
        
        # Verificar cambios en BD
        updated_device = TelemetryDevices.objects.get(id_device=self.test_device.id_device)
        assert updated_device.name == "FMC 155", \
            f"[UT-GD-003.1] Nombre no se actualizó correctamente"
        assert updated_device.IMEI == 123456789012348, \
            f"[UT-GD-003.1] IMEI no se actualizó correctamente"
        
        # Verificar parámetros asociados
        param_count = TelemetryDeviceParameter.objects.filter(
            telemetry_device=updated_device
        ).count()
        assert param_count == 5, \
            f"[UT-GD-003.1] Debería tener 5 parámetros, tiene {param_count}"
    
    def test_ut_gd_003_2_sin_permiso_retorna_403(self):
        """
        UT-GD-003.2: Usuario sin permiso recibe HTTP 403
        
        Verifica que un usuario sin el permiso telemetry_device.update (114)
        no pueda actualizar el dispositivo.
        """
        # Arrange
        headers = _auth_header_for([999])  # Sin permiso 114
        data = {
            "name": "FMC 155",
            "IMEI": 123456789012348,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN, \
            f"[UT-GD-003.2] Esperado: 403, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "permisos" in body.get("message", "").lower() or \
               "no tiene permisos" in body.get("message", "").lower(), \
            f"[UT-GD-003.2] Mensaje incorrecto: {body.get('message')}"
    
    def test_ut_gd_003_3_sin_token_retorna_401(self):
        """
        UT-GD-003.3: Sin token de autenticación retorna HTTP 401
        
        Verifica que acceder al endpoint sin Authorization header retorna 401.
        """
        # Arrange
        data = {
            "name": "FMC 155",
            "IMEI": 123456789012348,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json'
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
            f"[UT-GD-003.3] Esperado: 401, Obtenido: {response.status_code}"
    
    def test_ut_gd_003_4_campo_name_faltante_retorna_400(self):
        """
        UT-GD-003.4: Campo name faltante retorna HTTP 400
        
        Verifica que enviar el request sin el campo 'name' retorna error
        de validación.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "IMEI": 123456789012348,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.4] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "name" in body, \
            f"[UT-GD-003.4] Debería indicar error en campo 'name'"
    
    def test_ut_gd_003_5_campo_imei_faltante_retorna_400(self):
        """
        UT-GD-003.5: Campo IMEI faltante retorna HTTP 400
        
        Verifica que enviar el request sin el campo 'IMEI' retorna error
        de validación.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC 155",
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.5] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "IMEI" in body, \
            f"[UT-GD-003.5] Debería indicar error en campo 'IMEI'"
    
    def test_ut_gd_003_6_campo_parameters_faltante_retorna_400(self):
        """
        UT-GD-003.6: Campo parameters faltante retorna HTTP 400
        
        Verifica que enviar el request sin el campo 'parameters' retorna error
        de validación.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC 155",
            "IMEI": 123456789012348
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.6] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "parameters" in body, \
            f"[UT-GD-003.6] Debería indicar error en campo 'parameters'"
    
    def test_ut_gd_003_7_nombre_duplicado_retorna_400(self):
        """
        UT-GD-003.7: Nombre duplicado retorna HTTP 400
        
        Verifica que intentar actualizar con un nombre que ya existe en
        otro dispositivo retorna error de validación.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Dispositivo Existente",  # Nombre existente
            "IMEI": 123456789012349,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.7] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "name" in body, \
            f"[UT-GD-003.7] Debería indicar error en campo 'name'"
        assert "existe" in str(body.get("name", [])).lower() or \
               "duplicado" in str(body.get("name", [])).lower(), \
            f"[UT-GD-003.7] Debería indicar duplicidad de nombre"
    
    def test_ut_gd_003_8_imei_duplicado_retorna_400(self):
        """
        UT-GD-003.8: IMEI duplicado retorna HTTP 400
        
        Verifica que intentar actualizar con un IMEI que ya existe en
        otro dispositivo retorna error de validación.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Actualizado",
            "IMEI": 999999999999999,  # IMEI existente
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.8] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "IMEI" in body, \
            f"[UT-GD-003.8] Debería indicar error en campo 'IMEI'"
        assert "existe" in str(body.get("IMEI", [])).lower() or \
               "duplicado" in str(body.get("IMEI", [])).lower(), \
            f"[UT-GD-003.8] Debería indicar duplicidad de IMEI"
    
    def test_ut_gd_003_9_imei_negativo_retorna_400(self):
        """
        UT-GD-003.9: IMEI negativo retorna HTTP 400
        
        Verifica que un IMEI con valor negativo sea rechazado.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Actualizado",
            "IMEI": -123456789012345,  # IMEI negativo
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.9] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "IMEI" in body, \
            f"[UT-GD-003.9] Debería indicar error en campo 'IMEI'"
        assert "negativo" in str(body.get("IMEI", [])).lower(), \
            f"[UT-GD-003.9] Debería indicar que IMEI no puede ser negativo"
    
    def test_ut_gd_003_10_parameters_vacios_retorna_400(self):
        """
        UT-GD-003.10: Lista de parámetros vacía retorna HTTP 400
        
        Verifica que enviar una lista vacía de parámetros retorna error.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Actualizado",
            "IMEI": 123456789012349,
            "parameters": []  # Lista vacía
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.10] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "parameters" in body, \
            f"[UT-GD-003.10] Debería indicar error en campo 'parameters'"
        assert "al menos un parámetro" in str(body.get("parameters", [])).lower() or \
               "required" in str(body.get("parameters", [])).lower(), \
            f"[UT-GD-003.10] Debería indicar que se requiere al menos un parámetro"
    
    def test_ut_gd_003_11_parameters_duplicados_retorna_400(self):
        """
        UT-GD-003.11: Parámetros duplicados en la lista retorna HTTP 400
        
        Verifica que una lista de parámetros con IDs duplicados sea rechazada.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Actualizado",
            "IMEI": 123456789012349,
            "parameters": [1, 2, 2, 3, 4]  # Con duplicados
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.11] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "parameters" in body, \
            f"[UT-GD-003.11] Debería indicar error en campo 'parameters'"
        assert "duplicados" in str(body.get("parameters", [])).lower(), \
            f"[UT-GD-003.11] Debería indicar que hay duplicados"
    
    def test_ut_gd_003_12_name_excede_longitud_retorna_400(self):
        """
        UT-GD-003.12: Nombre excediendo 50 caracteres retorna HTTP 400
        
        Verifica que un nombre con más de 50 caracteres sea rechazado.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        long_name = "Este es un nombre de dispositivo extremadamente largo que supera los cincuenta caracteres permitidos"
        data = {
            "name": long_name,
            "IMEI": 123456789012349,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.12] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "name" in body, \
            f"[UT-GD-003.12] Debería indicar error en campo 'name'"
    
    def test_ut_gd_003_13_dispositivo_inexistente_retorna_404(self):
        """
        UT-GD-003.13: Dispositivo inexistente retorna HTTP 404
        
        Verifica que intentar actualizar un ID que no existe retorna 404.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Actualizado",
            "IMEI": 123456789012349,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}99999/",  # ID inexistente
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND, \
            f"[UT-GD-003.13] Esperado: 404, Obtenido: {response.status_code}"
    
    def test_ut_gd_003_14_parameters_inexistentes_retorna_400(self):
        """
        UT-GD-003.14: IDs de parámetros inexistentes retorna HTTP 400
        
        Verifica que intentar asociar parámetros que no existen retorna error.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        data = {
            "name": "FMC Actualizado",
            "IMEI": 123456789012349,
            "parameters": [99, 100, 101]  # IDs inexistentes
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST, \
            f"[UT-GD-003.14] Esperado: 400, Obtenido: {response.status_code}"
        
        body = response.json()
        assert "parameters" in body, \
            f"[UT-GD-003.14] Debería indicar error en campo 'parameters'"
        assert "no existe" in str(body.get("parameters", [])).lower() or \
               "inválido" in str(body.get("parameters", [])).lower(), \
            f"[UT-GD-003.14] Debería indicar que los parámetros no existen"
    
    def test_ut_gd_003_15_registration_date_no_cambia(self):
        """
        UT-GD-003.15: La fecha de registro no cambia al actualizar
        
        Verifica que al actualizar un dispositivo, la fecha de registro
        original se mantiene sin cambios.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        original_registration_date = self.test_device.registration_date
        
        data = {
            "name": "FMC Con Nueva Fecha",
            "IMEI": 123456789012350,
            "parameters": [1, 2, 3, 4]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que registration_date no cambió
        updated_device = TelemetryDevices.objects.get(id_device=self.test_device.id_device)
        assert updated_device.registration_date == original_registration_date, \
            f"[UT-GD-003.15] La fecha de registro no debería cambiar"
    
    def test_ut_gd_003_16_modification_date_actualizada(self):
        """
        UT-GD-003.16: La fecha de modificación se actualiza correctamente
        
        Verifica que al actualizar un dispositivo, la fecha de modificación
        se actualiza al timestamp de la operación.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        original_modification_date = self.test_device.modification_date
        
        data = {
            "name": "FMC Modificado",
            "IMEI": 123456789012351,
            "parameters": [1, 2, 3]
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que modification_date se actualizó
        updated_device = TelemetryDevices.objects.get(id_device=self.test_device.id_device)
        assert updated_device.modification_date > original_modification_date, \
            f"[UT-GD-003.16] La fecha de modificación debería actualizarse"
    
    def test_ut_gd_003_17_parametros_anteriores_eliminados(self):
        """
        UT-GD-003.17: Los parámetros anteriores son eliminados y reemplazados
        
        Verifica que al actualizar con nuevos parámetros, los anteriores
        son eliminados y se crean los nuevos.
        """
        # Arrange
        headers = _auth_header_for([self.permission_id])
        
        # Asociar parámetros iniciales
        self._associate_parameters_to_device(self.test_device, [1, 2, 3])
        
        data = {
            "name": "FMC Actualizado",
            "IMEI": 123456789012352,
            "parameters": [4, 5, 6, 7]  # Nuevos parámetros
        }
        
        # Act
        response = self.client.put(
            f"{self.endpoint_base}{self.test_device.id_device}/",
            data,
            format='json',
            HTTP_AUTHORIZATION=headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verificar que los parámetros antiguos fueron eliminados
        old_params = TelemetryDeviceParameter.objects.filter(
            telemetry_device=self.test_device
        )
        
        # Verificar que solo existen los nuevos parámetros
        param_ids = list(old_params.values_list('parameter_id', flat=True))
        param_ids.sort()
        assert param_ids == [4, 5, 6, 7], \
            f"[UT-GD-003.17] Debería tener parámetros [4, 5, 6, 7], tiene {param_ids}"


# ============================================================================
# EJECUCIÓN DIRECTA
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

