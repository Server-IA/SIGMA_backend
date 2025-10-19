# Test HU-CLI-004 - Actualizar Cliente
import pytest
import os
import django
from django.test import TestCase
from django.utils import timezone
from datetime import datetime

# Configurar Django antes de importar modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

# Mock para audit_sdk
import sys
from unittest.mock import Mock

# Crear módulo audit_sdk simulado
mock_audit = Mock()
mock_audit_client = Mock()
mock_audit_client.update = Mock()
mock_audit_client.delete = Mock()
mock_audit.AuditClient = Mock(return_value=mock_audit_client)
sys.modules['audit_sdk'] = mock_audit

django.setup()

@pytest.mark.django_db
class CustomerUpdateTestCase(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        from users.models.user import User
        from service_requests.models.customer import Customer
        from service_requests.models.document_type import DocumentType
        from service_requests.models.person_type import PersonType
        from parameterization.models.statues_category import StatuesCategory
        from parameterization.models.statues import Statues

        # Crear usuarios con y sin permisos
        self.user_with_permission = User.objects.create(id_user=201)
        self.user_without_permission = User.objects.create(id_user=202)
        
        # Crear usuario responsable
        self.responsible_user = User.objects.create(id_user=203)
        
        # Crear usuarios para asociaciones
        self.unassociated_user = User.objects.create(id_user=204)
        self.associated_user = User.objects.create(id_user=205)

        # Crear categoría de estados
        statues_category = StatuesCategory.objects.create(
            name="Estados Cliente CLI-004",
            description="Categoría de estados de cliente",
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.responsible_user
        )

        # Crear estados
        self.status_active = Statues.objects.create(
            id_statues=1,
            name="Activo",
            description="Cliente activo",
            id_statues_categories=statues_category,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.responsible_user
        )

        # Crear tipos de documento
        self.document_type = DocumentType.objects.create(
            id_document_type=1,
            name="Cédula de Ciudadanía"
        )

        # Crear tipos de persona
        self.person_type_natural = PersonType.objects.create(
            id_person_type=1,
            name="Persona Natural"
        )

        # Crear cliente base para actualizar
        self.customer_to_update = Customer.objects.create(
            id_customer=1,
            document_number=12345678,
            type_document_id=self.document_type,
            check_digit=5,
            person_type=self.person_type_natural,
            legal_entity_name="Juan Pérez Original",
            name="Juan",
            first_last_name="Pérez",
            second_last_name="Original",
            email="juan.original@example.com",
            phone="3009876543",
            address="Calle Original #123",
            id_municipality=1001,
            tax_regime=1,
            customer_statues=self.status_active,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.responsible_user
        )

        # Crear cliente con documento duplicado para test de duplicados
        self.existing_customer = Customer.objects.create(
            id_customer=2,
            document_number=99999999,
            type_document_id=self.document_type,
            check_digit=9,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Existente",
            name="Cliente",
            first_last_name="Existente",
            second_last_name="Test",
            email="existente@example.com",
            phone="3001111111",
            address="Calle Existente #456",
            id_municipality=1001,
            tax_regime=1,
            customer_statues=self.status_active,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.responsible_user
        )

        # Crear cliente asociado a usuario para test de asociación
        self.associated_customer = Customer.objects.create(
            id_customer=3,
            id_user=self.associated_user,
            document_number=11111111,
            type_document_id=self.document_type,
            check_digit=1,
            person_type=self.person_type_natural,
            legal_entity_name="Cliente Asociado",
            name="Cliente",
            first_last_name="Asociado",
            second_last_name="Usuario",
            email="asociado@example.com",
            phone="3002222222",
            address="Calle Asociado #789",
            id_municipality=1001,
            tax_regime=1,
            customer_statues=self.status_active,
            creation_date=timezone.now(),
            modification_date=timezone.now(),
            id_responsible_user=self.responsible_user
        )

        self.client = APIClient()
        self.url = f'/customers/{self.customer_to_update.id_customer}/update_customer/'

    def _force_auth_with_permission(self, user, permission_id=136):
        """Simula JWT y permiso 136 para customers.update"""
        # Autenticar usuario
        self.client.force_authenticate(user=user)
        
        # Mock directo de check_permission para simular que el usuario tiene el permiso
        from unittest.mock import patch
        from service_requests.api.customer_viewset import CustomerViewSet
        
        # Simular que check_permission siempre devuelve True para este usuario/permiso
        def mock_check_permission(viewset_self, request, required_permission_id):
            return required_permission_id == permission_id
        
        # Aplicar el patch
        self._permission_patch = patch.object(
            CustomerViewSet, 
            'check_permission', 
            mock_check_permission
        )
        self._permission_patch.start()

    def tearDown(self):
        """Limpiar mocks después de cada test"""
        if hasattr(self, '_permission_patch'):
            self._permission_patch.stop()

    # TEST CASOS HU-CLI-004

    def test_update_success_200(self):
        """Actualización exitosa de cliente"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        data = {
            "document_number": "87654321",
            "type_document_id": self.document_type.id_document_type,
            "person_type": self.person_type_natural.id_person_type,
            "legal_entity_name": "Juan Pérez Actualizado",
            "first_last_name": "Pérez",
            "email": "juan.actualizado@example.com",
            "phone": "3001234567",
            "address": "Calle 123 #45-67 Actualizada",
            "id_municipality": 1001,
            "tax_regime": 2
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('success'))
        self.assertIn("Cliente actualizado correctamente", response.data.get('message'))
        self.assertIn("data", response.data)

    def test_update_duplicate_document_400(self):
        """No permite actualizar con documento duplicado"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        data = {
            "document_number": "99999999",  # Documento del existing_customer
            "legal_entity_name": "Juan Pérez Actualizado"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        self.assertIn("errors", response.data)

    def test_update_user_already_associated_400(self):
        """No permite actualizar con documento de usuario ya asociado a otro cliente"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        data = {
            "document_number": "11111111",  # Documento del associated_user
            "legal_entity_name": "Juan Pérez Actualizado"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        self.assertIn("errors", response.data)

    def test_update_no_permission_403(self):
        """No permite actualizar sin permiso 136"""
        self.client.force_authenticate(user=self.user_without_permission)
        data = {
            "legal_entity_name": "Juan Pérez Actualizado"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.data.get('success'))
        self.assertIn("No tiene permisos para actualizar clientes", response.data.get('message'))

    def test_update_not_found_404(self):
        """No permite actualizar cliente inexistente"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        nonexistent_url = "/customers/99999/update_customer/"
        data = {
            "legal_entity_name": "Cliente Inexistente"
        }
        response = self.client.patch(nonexistent_url, data, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data.get('success'))
        self.assertIn("Cliente no encontrado", response.data.get('message'))

    def test_update_invalid_data_400(self):
        """No permite actualizar con datos inválidos"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        data = {
            "legal_entity_name": "",  # Campo requerido vacío
            "email": "email-invalido",  # Email con formato inválido
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        self.assertIn("errors", response.data)

    def test_update_user_association_200(self):
        """Asocia manualmente cliente con usuario no asociado"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        
        data = {
            "id_user": self.unassociated_user.id_user,  # Asociación manual
            "document_number": "87654321",
            "legal_entity_name": "Juan Pérez Con Asociación"
        }
        response = self.client.patch(self.url, data, format='json')
            
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('success'))
        self.assertIn("Cliente actualizado correctamente", response.data.get('message'))
        
        # Verificar que se asoció el usuario
        from service_requests.models.customer import Customer
        updated_customer = Customer.objects.get(id_customer=self.customer_to_update.id_customer)
        self.assertEqual(updated_customer.id_user, self.unassociated_user)

    def test_update_max_length_validations_400(self):
        """Valida que no se permitan campos que excedan los 100 caracteres"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        
        # Test con nombre muy largo (>100 caracteres)
        data = {
            "name": "A" * 101,  # 101 caracteres
            "legal_entity_name": "Test Entity"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        self.assertIn('name', response.data.get('errors', {}))
        
        # Test con email muy largo (>100 caracteres)
        data = {
            "email": "a" * 95 + "@email.com",  # 105 caracteres total
            "legal_entity_name": "Test Entity"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        self.assertIn('email', response.data.get('errors', {}))
        
        # Test con teléfono muy largo (>100 caracteres)
        data = {
            "phone": "1" * 101,  # 101 caracteres
            "legal_entity_name": "Test Entity"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        self.assertIn('phone', response.data.get('errors', {}))

    def test_document_number_validations_400(self):
        """Valida las reglas de negocio del número de documento"""
        self._force_auth_with_permission(self.user_with_permission, 137)
        
        # Test documento negativo
        data = {
            "document_number": "-123456789",
            "legal_entity_name": "Test Entity"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        
        # Test documento con más de 10 dígitos
        data = {
            "document_number": "12345678901",  # 11 dígitos
            "legal_entity_name": "Test Entity"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
        
        # Test documento no numérico
        data = {
            "document_number": "12345abc89",
            "legal_entity_name": "Test Entity"
        }
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get('success'))
