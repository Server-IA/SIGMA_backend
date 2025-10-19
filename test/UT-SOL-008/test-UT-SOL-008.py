"""
Pruebas unitarias para finalización de solicitudes de servicio
ID: UT-SOL-008

Historia de Usuario: Como usuario autorizado, quiero finalizar una solicitud de servicio
que está en estado "En proceso" proporcionando observaciones de finalización.

Endpoint bajo prueba:
- POST /service_requests/{id_request}/complete/ - Finalizar solicitud de servicio

Permisos requeridos:
- 152: request.complete_request - Finalizar solicitud
"""

import pytest
import json
from datetime import datetime, timedelta, date
from unittest.mock import patch, MagicMock
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from service_requests.models import (
    ServiceRequest,
    Customer,
    PersonType,
    TaxRegime,
    DocumentType
)
from users.models import User
from parameterization.models import (
    Statues,
    StatuesCategory
)


@pytest.mark.django_db
class TestServiceRequestCompleteEndpoint:
    """Pruebas para el endpoint de finalización de solicitudes"""
    
    endpoint_base = "/service_requests/"
    
    def setup_method(self):
        """Configuración inicial para cada prueba"""
        self.client = APIClient()
        self.now = timezone.now()
        
        # Crear usuario responsable
        self.responsible_user = self._ensure_user(1)
        
        # Tokens con y sin permisos
        self.token_with_permission = self._token_with_permissions([152])
        self.token_without_permission = self._token_with_permissions([999])
        
        # Inicializar parametrización base
        self._bootstrap_parametrization()
        
        # Crear cliente de prueba
        self.customer = self._create_test_customer()
        
        # Limpiar solicitudes previas
        ServiceRequest.objects.all().delete()
    
    # ==================== HELPERS ====================
    
    def _ensure_user(self, user_id: int) -> User:
        """Crea o recupera un usuario para pruebas"""
        user = User.objects.create(id_user=user_id)
        user.id = user.id_user
        user.is_authenticated = True
        return user
    
    def _token_with_permissions(self, permission_ids):
        """Genera payload de token con permisos específicos"""
        perms = [{"id": perm_id} for perm_id in permission_ids]
        return {
            "roles": [{"permisos": perms, "permissions": perms}],
            "permisos": perms,
            "permissions": perms,
        }
    
    def _bootstrap_parametrization(self):
        """Inicializa datos de parametrización necesarios"""
        # Categoría de estados
        self.statues_category = StatuesCategory.objects.create(
            id_statues_categories=1,
            name="Estados generales",
            description="Estados del sistema",
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estados necesarios para las pruebas
        self.status_in_process = Statues.objects.create(
            id_statues=21,
            name="En proceso",
            description="Solicitud en proceso",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.status_finalized = Statues.objects.create(
            id_statues=22,
            name="Finalizada",
            description="Solicitud finalizada",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.status_cancelled = Statues.objects.create(
            id_statues=23,
            name="Cancelada",
            description="Solicitud cancelada",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        self.status_pending = Statues.objects.create(
            id_statues=20,
            name="Pendiente",
            description="Solicitud pendiente",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
        
        # Estado "Disponible" para maquinaria (ID 4)
        self.status_available = Statues.objects.create(
            id_statues=4,
            name="Disponible",
            description="Maquinaria disponible",
            id_statues_categories=self.statues_category,
            creation_date=self.now,
            modification_date=self.now,
            id_responsible_user=self.responsible_user,
        )
    
    def _create_test_customer(self, document_number=1079172265):
        """Crea un cliente de prueba"""
        # Tipo de persona
        person_type, _ = PersonType.objects.get_or_create(
            id_person_type=1,
            defaults={"name": "Natural"}
        )
        
        # Régimen tributario
        tax_regime, _ = TaxRegime.objects.get_or_create(
            id_tax_regime=1,
            defaults={"code": "SIMP", "name": "Simplificado"}
        )
        
        # Tipo de documento
        document_type, _ = DocumentType.objects.get_or_create(
            id_document_type=1,
            defaults={"name": "Cédula de Ciudadanía"}
        )
        
        customer, _ = Customer.objects.get_or_create(
            document_number=document_number,
            defaults={
                "type_document_id": document_type,
                "person_type": person_type,
                "legal_entity_name": "Juan Camilo Sarmiento Cardozo",
                "name": "Juan camilo",
                "first_last_name": "Sarmiento",
                "second_last_name": "Cardozo",
                "email": "juanandresveru@gmail.com",
                "phone": "3001234567",
                "address": "Calle 123",
                "id_municipality": 1,
                "tax_regime": tax_regime,
                "customer_statues": self.status_in_process,
                "creation_date": self.now,
                "modification_date": self.now,
                "id_responsible_user": self.responsible_user,
            }
        )
        return customer
    
    def _create_service_request(self, request_id, status, customer=None):
        """Crea una solicitud de servicio con el estado especificado"""
        if customer is None:
            customer = self.customer
            
        future_date = (timezone.now() + timedelta(days=1)).date()
        
        service_request = ServiceRequest.objects.create(
            id_request=request_id,
            customer=customer,
            request_detail="Servicio de prueba",
            scheduled_start_date=future_date,
            scheduled_end_date=future_date,
            request_status=status,
            id_responsible_user=self.responsible_user
        )
        return service_request
    
    def _get_valid_payload(self):
        """Retorna un payload válido para finalizar solicitud"""
        return {
            "completion_cancellation_observations": "Trabajo completado exitosamente según lo programado."
        }
    
    # ==================== PRUEBAS ====================
    
    @patch('service_requests.api.service_request_viewset.requests.post')
    @patch('service_requests.api.service_request_viewset.AuditClient')
    def test_ut_sol_008_1_successful_completion(self, mock_audit, mock_requests_post):
        """
        UT-SOL-008.1: 201 Created – Finalización exitosa (camino feliz)
        
        Verificar que el endpoint finaliza correctamente una solicitud en estado "En proceso" 
        cuando el usuario tiene permisos válidos y envía observaciones dentro del límite permitido.
        """
        # Arrange
        mock_requests_post.return_value = MagicMock(status_code=200)
        mock_audit.return_value.create = MagicMock()
        
        # Crear solicitud en estado "En proceso"
        service_request = self._create_service_request("SOL-2025-0020", self.status_in_process)
        
        payload = self._get_valid_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        assert response.data['success'] is True
        assert response.data['message'] == f"Solicitud finalizada exitosamente. Código: {service_request.id_request}."
        assert response.data['id_request'] == service_request.id_request
        
        # Verificar en base de datos
        service_request.refresh_from_db()
        assert service_request.request_status.id_statues == 22  # Estado "Finalizada"
        assert service_request.completion_cancellation_observations == payload['completion_cancellation_observations']
        assert service_request.completion_cancellation_datetime is not None
        assert service_request.completion_cancellation_user == self.responsible_user
        
        print(f"✅ UT-SOL-008.1: APROBADO - Solicitud finalizada exitosamente: {service_request.id_request}")
    
    def test_ut_sol_008_2_forbidden_no_permission(self):
        """
        UT-SOL-008.2: 403 Forbidden – Usuario sin permiso para finalizar
        
        Verifica que el endpoint deniega la finalización si el usuario no posee el permiso id=152.
        """
        # Arrange
        service_request = self._create_service_request("SOL-2025-0020", self.status_in_process)
        
        payload = self._get_valid_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_without_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 403
        assert response.data['message'] == "No tiene permisos para finalizar solicitudes"
        
        print(f"✅ UT-SOL-008.2: APROBADO - Usuario sin permisos rechazado correctamente")
    
    def test_ut_sol_008_3_unauthorized_no_auth(self):
        """
        UT-SOL-008.3: 401 Unauthorized – Usuario no autenticado
        
        Valida que el endpoint rechaza la solicitud si no hay autenticación.
        """
        # Arrange
        service_request = self._create_service_request("SOL-2025-0020", self.status_in_process)
        
        payload = self._get_valid_payload()
        
        # Act - Sin autenticación
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 401
        # El mensaje puede estar en 'detail' o 'message'
        assert 'detail' in response.data or 'message' in response.data
        
        print(f"✅ UT-SOL-008.3: APROBADO - Usuario no autenticado rechazado")
    
    def test_ut_sol_008_4_not_found_request_not_exists(self):
        """
        UT-SOL-008.4: 404 Not Found – Solicitud inexistente
        
        Valida que el endpoint retorna 404 si el id_request no existe.
        """
        # Arrange
        payload = self._get_valid_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}SOL-2025-0999/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 404
        # Verificar que contiene información de error 404
        assert 'detail' in response.data
        
        print(f"✅ UT-SOL-008.4: APROBADO - Solicitud inexistente rechazada")
    
    def test_ut_sol_008_5_empty_observations(self):
        """
        UT-SOL-008.5: 400 Bad Request – Campo vacío o nulo
        
        Verifica que el campo completion_cancellation_observations no puede ser nulo o vacío.
        """
        # Arrange
        service_request = self._create_service_request("SOL-2025-0020", self.status_in_process)
        
        payload = {
            "completion_cancellation_observations": ""
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['message'] == "Error en la validación de datos"
        assert 'completion_cancellation_observations' in response.data['errors']
        # Verificar que el error contiene información sobre campo en blanco
        error_text = str(response.data['errors']['completion_cancellation_observations'])
        assert "blank" in error_text or "en blanco" in error_text
        
        print(f"✅ UT-SOL-008.5: APROBADO - Campo vacío rechazado")
    
    def test_ut_sol_008_6_max_length_exceeded(self):
        """
        UT-SOL-008.6: 400 Bad Request – Excede longitud máxima
        
        Valida que el campo completion_cancellation_observations no supere 500 caracteres.
        """
        # Arrange
        service_request = self._create_service_request("SOL-2025-0020", self.status_in_process)
        
        # Crear string de 501 caracteres
        long_observations = "A" * 501
        
        payload = {
            "completion_cancellation_observations": long_observations
        }
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['message'] == "Error en la validación de datos"
        assert 'completion_cancellation_observations' in response.data['errors']
        # Verificar que el error contiene información sobre longitud máxima
        error_text = str(response.data['errors']['completion_cancellation_observations'])
        assert "500 characters" in error_text or "más de 500 caracteres" in error_text
        
        print(f"✅ UT-SOL-008.6: APROBADO - Longitud máxima excedida rechazada")
    
    def test_ut_sol_008_7_cancelled_request(self):
        """
        UT-SOL-008.7: 400 Bad Request – Solicitud en estado no permitido (Cancelada)
        
        Valida que el endpoint no permite finalizar solicitudes canceladas.
        """
        # Arrange
        service_request = self._create_service_request("SOL-2025-0015", self.status_cancelled)
        
        payload = self._get_valid_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['message'] == "Error en la validación de datos"
        assert 'non_field_errors' in response.data['errors']
        assert "No se puede finalizar una solicitud que está cancelada." in str(response.data['errors']['non_field_errors'])
        
        print(f"✅ UT-SOL-008.7: APROBADO - Solicitud cancelada rechazada")
    
    def test_ut_sol_008_8_not_in_process_status(self):
        """
        UT-SOL-008.8: 400 Bad Request – Solicitud no está en proceso
        
        Valida que solo pueden finalizarse solicitudes en estado "En proceso".
        """
        # Arrange
        service_request = self._create_service_request("SOL-2025-0018", self.status_pending)
        
        payload = self._get_valid_payload()
        
        self.client.force_authenticate(user=self.responsible_user)
        self.client.handler._force_token = self.token_with_permission
        
        # Act
        response = self.client.post(
            f"{self.endpoint_base}{service_request.id_request}/complete/",
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 400
        assert response.data['success'] is False
        assert response.data['message'] == "Error en la validación de datos"
        assert 'non_field_errors' in response.data['errors']
        assert "Solo se pueden finalizar solicitudes que están en proceso (estado aceptado)." in str(response.data['errors']['non_field_errors'])
        
        print(f"✅ UT-SOL-008.8: APROBADO - Estado no permitido rechazado")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
