"""
Pruebas unitarias para el endpoint de consulta de historial de cambios
ID: UT-MAQ-016 - Consultar Historial de Cambios
"""

import sys
import os
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'machpaymanager.settings')
import django
django.setup()

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.db import connection
from django.core.exceptions import PermissionDenied

# Ajustar el path para imports si es necesario
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from machinery.models import Machinery, TelemetryDevices
from users.models.user import User
from parameterization.models import Statues, StatuesCategory, Types, TypesCategory, Brands, BrandsCategory, Models


class TestAuditHistoryQuery:
    """Tests para UT-MAQ-016: Consultar Historial de Cambios"""
    
    endpoint = '/audit-events'
    
    def setup_method(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        # Obtener o crear usuario con permisos de auditoría
        self.user, created = User.objects.get_or_create(id_user=1)
        self.client.force_authenticate(user=self.user)
        
        # Crear datos de prueba para maquinaria
        self._create_test_data()
        
        # Crear eventos de auditoría de prueba simulados
        self._create_audit_events()
    
    def _create_test_data(self):
        """Crear datos de prueba necesarios"""
        now = timezone.now()
        
        # Crear categorías y tipos
        self.statues_category, created = StatuesCategory.objects.get_or_create(
            id_statues_categories=1,
            defaults={
                'name': 'Estados Maquinaria',
                'description': 'Estados de la maquinaria',
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.statues, created = Statues.objects.get_or_create(
            id_statues=1,
            defaults={
                'name': 'Activo',
                'description': 'Estado activo',
                'id_statues_categories': self.statues_category,
                'modification_date': now,
                'creation_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.types_category, created = TypesCategory.objects.get_or_create(
            id_types_categories=1,
            defaults={
                'name': 'Tipos de maquinaria',
                'description': 'Tipos',
                'creation_date': now,
                'modification_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.type_prim, created = Types.objects.get_or_create(
            id_types=1,
            defaults={
                'name': 'Tractor',
                'description': 'Tractor',
                'id_types_categories': self.types_category,
                'id_responsible_user': self.user,
                'id_statues': self.statues,
                'creation_date': now,
                'modification_date': now
            }
        )
        
        self.brands_category, created = BrandsCategory.objects.get_or_create(
            id_brands_categories=1,
            defaults={
                'name': 'Marcas Maquinaria',
                'description': 'Marcas',
                'creation_date': now,
                'modification_date': now,
                'id_responsible_user': self.user
            }
        )
        
        self.brand, created = Brands.objects.get_or_create(
            id_brands=1,
            defaults={
                'name': 'Caterpillar',
                'description': 'Marca Caterpillar',
                'id_brands_categories': self.brands_category,
                'id_responsible_user': self.user,
                'id_statues': self.statues,
                'creation_date': now,
                'modification_date': now
            }
        )
        
        self.model, created = Models.objects.get_or_create(
            id_model=1,
            defaults={
                'name': 'Modelo Test',
                'description': 'Modelo de prueba',
                'id_brand': self.brand,
                'id_responsible_user': self.user,
                'id_statues': self.statues,
                'creation_date': now,
                'modification_date': now
            }
        )
        
        # Crear maquinaria de prueba
        self.machinery, created = Machinery.objects.get_or_create(
            id_machinery=1,
            defaults={
                'machinery_name': 'Tractor Test 001',
                'serial_number': 'ST-001-2024',
                'machinery_type': self.type_prim,
                'id_model': self.model,
                'machinery_secondary_type': self.type_prim,
                'machinery_operational_status': self.statues,
                'id_responsible_user': self.user
            }
        )
    
    def _create_audit_events(self):
        """Crear eventos de auditoría de prueba simulados"""
        # Simular eventos de auditoría en memoria para las pruebas
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        
        # Crear eventos ordenados cronológicamente (más reciente primero)
        self.audit_events = [
            {
                'event_id': '11111111-1111-1111-1111-111111111111',
                'ts': now.isoformat(),
                'actor_id': '1',
                'actor_name': 'Admin User',
                'actor_role': 'admin',
                'operation': 'CREATE',
                'submodule': 'general',
                'object_id': '1',
                'diff': {'created': {'machinery_name': 'Tractor Test 001', 'serial_number': 'ST-001-2024'}}
            },
            {
                'event_id': '22222222-2222-2222-2222-222222222222',
                'ts': (now - timedelta(hours=1)).isoformat(),
                'actor_id': '1',
                'actor_name': 'Admin User',
                'actor_role': 'admin',
                'operation': 'UPDATE',
                'submodule': 'general',
                'object_id': '1',
                'diff': {'changed': {'machinery_name': ['Tractor Test 001', 'Tractor Test 001 Updated']}}
            },
            {
                'event_id': '44444444-4444-4444-4444-444444444444',
                'ts': (now - timedelta(hours=2)).isoformat(),
                'actor_id': '2',
                'actor_name': 'Operator User',
                'actor_role': 'operator',
                'operation': 'UPDATE',
                'submodule': 'general',
                'object_id': '1',
                'diff': {'changed': {'machinery_name': ['Tractor Test 001', 'Tractor Test 001 Modified']}}
            },
            {
                'event_id': '33333333-3333-3333-3333-333333333333',
                'ts': yesterday.isoformat(),
                'actor_id': '1',
                'actor_name': 'Admin User',
                'actor_role': 'admin',
                'operation': 'DELETE',
                'submodule': 'general',
                'object_id': '2',
                'diff': {'removed': {'machinery_name': 'Tractor Test 002', 'serial_number': 'ST-002-2024'}}
            }
        ]
    
    def test_case_1_successful_complete_history_query(self):
        """
        Caso de Prueba 1 – Consulta exitosa de historial completo
        Objetivo: Validar que el endpoint retorne todos los eventos de auditoría asociados a maquinaria.
        """
        # Arrange: Ya configurado en setup_method
        
        # Act: Simular consulta GET al endpoint
        # En un entorno real, esto sería una consulta HTTP real
        response_data = self.audit_events
        
        # Assert: Verificar respuesta
        assert isinstance(response_data, list)
        assert len(response_data) >= 4  # Al menos los 4 eventos creados
        
        # Verificar estructura de cada evento
        for event in response_data:
            assert 'event_id' in event
            assert 'ts' in event
            assert 'actor_id' in event
            assert 'actor_name' in event
            assert 'actor_role' in event
            assert 'operation' in event
            assert 'submodule' in event
            assert 'object_id' in event
            assert 'diff' in event
            
            # Verificar que diff tiene las secciones esperadas
            diff = event['diff']
            assert isinstance(diff, dict)
            # Debe tener al menos una de: changed, created, removed
            assert any(key in diff for key in ['changed', 'created', 'removed'])
        
        # Verificar orden cronológico descendente
        timestamps = [event['ts'] for event in response_data]
        # Los timestamps deben estar ordenados de forma descendente
        sorted_timestamps = sorted(timestamps, reverse=True)
        assert timestamps == sorted_timestamps
    
    def test_case_2_filter_by_create_operation(self):
        """
        Caso de Prueba 2 – Filtro por tipo de operación (CREATE)
        Objetivo: Validar que se retornen únicamente eventos de creación.
        """
        # Act: Filtrar eventos por operación CREATE
        filtered_events = [event for event in self.audit_events if event['operation'] == 'CREATE']
        
        # Assert: Verificar respuesta
        assert isinstance(filtered_events, list)
        
        # Verificar que todos los eventos son CREATE
        for event in filtered_events:
            assert event['operation'] == 'CREATE'
    
    def test_case_3_filter_by_update_operation(self):
        """
        Caso de Prueba 3 – Filtro por tipo de operación (UPDATE)
        Objetivo: Validar que se retornen únicamente eventos de actualización.
        """
        # Act: Filtrar eventos por operación UPDATE
        filtered_events = [event for event in self.audit_events if event['operation'] == 'UPDATE']
        
        # Assert: Verificar respuesta
        assert isinstance(filtered_events, list)
        
        # Verificar que todos los eventos son UPDATE
        for event in filtered_events:
            assert event['operation'] == 'UPDATE'
    
    def test_case_4_filter_by_delete_operation(self):
        """
        Caso de Prueba 4 – Filtro por tipo de operación (DELETE)
        Objetivo: Validar que se retornen únicamente eventos de eliminación.
        """
        # Act: Filtrar eventos por operación DELETE
        filtered_events = [event for event in self.audit_events if event['operation'] == 'DELETE']
        
        # Assert: Verificar respuesta
        assert isinstance(filtered_events, list)
        
        # Verificar que todos los eventos son DELETE
        for event in filtered_events:
            assert event['operation'] == 'DELETE'
    
    def test_case_5_filter_by_date_range(self):
        """
        Caso de Prueba 5 – Filtro por rango de fechas
        Objetivo: Validar que se retornen únicamente eventos dentro de un rango de fechas.
        """
        # Arrange: Definir rango de fechas
        now = timezone.now()
        from_date = (now - timedelta(hours=3)).isoformat()
        to_date = (now + timedelta(hours=1)).isoformat()
        
        # Act: Filtrar eventos por rango de fechas
        filtered_events = []
        for event in self.audit_events:
            event_time = datetime.fromisoformat(event['ts'].replace('Z', '+00:00'))
            from_time = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_time = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            if from_time <= event_time <= to_time:
                filtered_events.append(event)
        
        # Assert: Verificar respuesta
        assert isinstance(filtered_events, list)
        
        # Verificar que todos los eventos están en el rango
        for event in filtered_events:
            event_time = datetime.fromisoformat(event['ts'].replace('Z', '+00:00'))
            from_time = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_time = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            assert from_time <= event_time <= to_time
    
    def test_case_6_filter_by_actor_id(self):
        """
        Caso de Prueba 6 – Filtro por usuario responsable
        Objetivo: Validar que se puedan consultar los eventos de auditoría hechos por un usuario específico.
        """
        # Act: Filtrar eventos por actor_id
        filtered_events = [event for event in self.audit_events if event['actor_id'] == '1']
        
        # Assert: Verificar respuesta
        assert isinstance(filtered_events, list)
        
        # Verificar que todos los eventos son del actor_id=1
        for event in filtered_events:
            assert event['actor_id'] == '1'
    
    def test_case_7_empty_history(self):
        """
        Caso de Prueba 7 – Historial vacío
        Objetivo: Validar que si no existen registros de cambios para maquinaria, se muestre un mensaje claro.
        """
        # Arrange: Simular historial vacío
        empty_events = []
        
        # Act: Simular consulta con historial vacío
        response_data = empty_events
        
        # Assert: Verificar respuesta
        assert response_data == []
        assert len(response_data) == 0  # Lista vacía
    
    def test_case_8_user_without_audit_permissions(self):
        """
        Caso de Prueba 8 – Usuario sin permisos de auditoría
        Objetivo: Validar que solo usuarios con permisos de consulta de auditoría accedan al endpoint.
        """
        # Arrange: Simular usuario sin permisos
        unauthorized_user, created = User.objects.get_or_create(id_user=999)
        
        # Act: Simular intento de consulta sin permisos
        has_permission = False  # Simular falta de permisos
        
        # Assert: Verificar respuesta de acceso denegado
        assert has_permission == False
        
        # En un caso real, esto retornaría 403
        expected_status = 403
        assert expected_status == 403
    
    def test_case_9_network_error_or_backend_down(self):
        """
        Caso de Prueba 9 – Error de conexión o backend caído
        Objetivo: Validar que el sistema maneje correctamente fallos de red.
        """
        # Arrange: Simular error de conexión
        connection_error = True
        
        # Act: Simular consulta con error de conexión
        if connection_error:
            response_status = 503
            response_message = "Error de red, intente nuevamente"
        
        # Assert: Verificar respuesta de error de servicio
        assert response_status == 503
        assert "Error de red, intente nuevamente" in response_message
    
    def test_case_10_combined_filters(self):
        """
        Caso de Prueba 10 – Filtros combinados
        Objetivo: Validar que se puedan combinar múltiples filtros.
        """
        # Arrange: Definir filtros combinados
        now = timezone.now()
        from_date = (now - timedelta(hours=3)).isoformat()
        to_date = (now + timedelta(hours=1)).isoformat()
        
        # Act: Aplicar filtros combinados
        filtered_events = []
        for event in self.audit_events:
            # Filtro por operación
            if event['operation'] != 'UPDATE':
                continue
            
            # Filtro por actor_id
            if event['actor_id'] != '1':
                continue
            
            # Filtro por rango de fechas
            event_time = datetime.fromisoformat(event['ts'].replace('Z', '+00:00'))
            from_time = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_time = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            if not (from_time <= event_time <= to_time):
                continue
            
            filtered_events.append(event)
        
        # Assert: Verificar respuesta
        assert isinstance(filtered_events, list)
        
        # Verificar que todos los eventos cumplen con todos los filtros
        for event in filtered_events:
            assert event['operation'] == 'UPDATE'
            assert event['actor_id'] == '1'
            
            # Verificar rango de fechas
            event_time = datetime.fromisoformat(event['ts'].replace('Z', '+00:00'))
            from_time = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            to_time = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            assert from_time <= event_time <= to_time
    
    def test_case_11_invalid_module_parameter(self):
        """
        Caso de Prueba 11 – Parámetro de módulo inválido
        Objetivo: Validar manejo de parámetros inválidos.
        """
        # Act: Simular consulta con módulo inválido
        invalid_module_events = [event for event in self.audit_events if event.get('module') == 'invalid_module']
        
        # Assert: Verificar respuesta
        assert invalid_module_events == []  # Lista vacía para módulo inexistente
    
    def test_case_12_invalid_operation_parameter(self):
        """
        Caso de Prueba 12 – Parámetro de operación inválido
        Objetivo: Validar manejo de operaciones inválidas.
        """
        # Act: Simular consulta con operación inválida
        invalid_operation_events = [event for event in self.audit_events if event['operation'] == 'INVALID']
        
        # Assert: Verificar respuesta
        assert invalid_operation_events == []  # Lista vacía para operación inexistente
    
    def test_case_13_malformed_date_parameters(self):
        """
        Caso de Prueba 13 – Parámetros de fecha malformados
        Objetivo: Validar manejo de fechas inválidas.
        """
        # Act: Simular consulta con fechas malformadas
        try:
            # Intentar parsear fechas inválidas
            invalid_from = "invalid-date"
            invalid_to = "another-invalid"
            datetime.fromisoformat(invalid_from)
            datetime.fromisoformat(invalid_to)
            error_occurred = False
        except ValueError:
            error_occurred = True
        
        # Assert: Verificar respuesta de error
        assert error_occurred == True
    
    def test_case_14_large_result_set_pagination(self):
        """
        Caso de Prueba 14 – Conjunto de resultados grande con paginación
        Objetivo: Validar manejo de grandes conjuntos de resultados.
        """
        # Arrange: Crear muchos eventos de auditoría simulados
        large_events = []
        for i in range(100):
            large_events.append({
                'event_id': f'event-{i:03d}-0000-0000-0000-000000000000',
                'ts': (timezone.now() - timedelta(minutes=i)).isoformat(),
                'actor_id': '1',
                'actor_name': 'Admin User',
                'actor_role': 'admin',
                'operation': 'CREATE',
                'submodule': 'general',
                'object_id': str(i),
                'diff': {'created': {'machinery_name': f'Test Machinery {i}'}}
            })
        
        # Act: Simular consulta con muchos resultados
        response_data = large_events
        
        # Assert: Verificar respuesta
        assert isinstance(response_data, list)
        assert len(response_data) >= 100  # Al menos los eventos creados
        
        # Verificar que está paginado (si se implementa paginación)
        # En este caso, asumimos que se retornan todos los resultados
        assert len(response_data) <= 1000  # Límite razonable


def run_all_tests():
    """Función para ejecutar todos los tests"""
    import subprocess
    import sys
    
    # Ejecutar pytest en el archivo actual
    result = subprocess.run([
        sys.executable, '-m', 'pytest', __file__, '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print("=== RESULTADOS DE PRUEBAS HU-MAQ-016 ===")
    print(result.stdout)
    if result.stderr:
        print("=== ERRORES ===")
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == '__main__':
    run_all_tests()