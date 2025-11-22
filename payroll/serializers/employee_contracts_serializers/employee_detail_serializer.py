import logging
import os
from typing import Any, Dict, Optional

import requests
from rest_framework import serializers

from payroll.models import Employee, EmployeeNews

logger = logging.getLogger(__name__)


class EmployeeNewsSerializer(serializers.ModelSerializer):
    """Serializer para el historial de novedades del empleado."""
    
    date = serializers.DateTimeField(source='news_date', read_only=True)
    responsible_user_name = serializers.SerializerMethodField()
    description = serializers.CharField(source='observation', read_only=True)
    action = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeNews
        fields = [
            'date',
            'responsible_user_name',
            'description',
            'action',
        ]

    def get_action(self, obj: EmployeeNews) -> str:
        """Obtiene el nombre para mostrar del tipo de noticia."""
        return obj.get_news_type_display()

    def get_responsible_user_name(self, obj: EmployeeNews) -> Optional[str]:
        """Obtiene el nombre del usuario responsable desde el servicio externo."""
        responsible_user = getattr(obj, 'id_responsible_user', None)
        if not responsible_user:
            return None

        user_id = getattr(responsible_user, 'id_user', None) if hasattr(responsible_user, 'id_user') else None
        if not user_id:
            return None

        # Obtener datos del usuario desde el cache compartido o servicio externo
        # El cache se comparte desde el serializer padre a través del contexto
        user_data = self._get_external_user(user_id)
        if user_data:
            name_parts = []
            name = user_data.get('name', '').strip()
            first_last_name = user_data.get('first_last_name', '').strip()
            second_last_name = user_data.get('second_last_name', '').strip()

            if name:
                name_parts.append(name)
            if first_last_name:
                name_parts.append(first_last_name)
            if second_last_name:
                name_parts.append(second_last_name)

            return ' '.join(name_parts) if name_parts else None

        return None

    def _get_external_user(self, user_id: int) -> Dict[str, Any]:
        """Obtiene información del usuario desde el servicio externo o cache."""
        if not user_id:
            return {}

        # Verificar cache compartido desde el contexto (pasado por el serializer padre)
        context = self.context if isinstance(self.context, dict) else {}
        users_data = context.get('users_data', {})
        if user_id in users_data:
            return users_data[user_id]

        # Si no está en cache, intentar obtenerlo
        # Inicializar cache si no existe
        if not hasattr(self, '_ext_users_cache'):
            self._ext_users_cache = {}
        
        if user_id in self._ext_users_cache:
            return self._ext_users_cache[user_id]

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            logger.warning('AUTH_SERVICE_URL no configurado')
            return {}

        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers = {'Content-Type': 'application/json'}

        # Obtener header de autorización del request
        request = context.get('request')
        if request is not None:
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                request.headers.get('Authorization') if hasattr(request, 'headers') else None
            )
            if auth_header:
                headers['Authorization'] = auth_header

        try:
            resp = requests.post(url, json={'ids': [user_id]}, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.content:
                payload = resp.json() or {}
                data = payload.get('data') or []
                if isinstance(data, list):
                    for u in data:
                        try:
                            if u and str(u.get('id')) == str(user_id):
                                self._ext_users_cache[user_id] = u
                                return u
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f'Error consultando servicio externo de usuarios: {str(e)}')

        return {}


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Serializer para el detalle completo del empleado."""
    
    # Información Personal
    personal_info = serializers.SerializerMethodField()
    
    # Información del Contrato
    contract_info = serializers.SerializerMethodField()
    
    # Historial de Novedades
    news_history = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'personal_info',
            'contract_info',
            'news_history',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache para datos de usuarios externos
        if not hasattr(self, '_ext_users_cache'):
            self._ext_users_cache = {}
        # Si se proporcionan usuarios en batch desde el contexto, usarlos
        context = kwargs.get('context', {})
        if isinstance(context, dict) and 'users_data' in context:
            self._ext_users_cache.update(context['users_data'])

    def _get_external_user(self, user_id: Optional[int]) -> Dict[str, Any]:
        """
        Obtiene información del usuario desde el servicio externo.
        
        Args:
            user_id: ID del usuario a consultar
            
        Returns:
            Diccionario con datos del usuario o diccionario vacío si no se encuentra
        """
        if not user_id:
            return {}

        # Verificar cache
        if user_id in self._ext_users_cache:
            return self._ext_users_cache[user_id]

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            logger.warning('AUTH_SERVICE_URL no configurado')
            return {}

        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers = {'Content-Type': 'application/json'}

        # Obtener header de autorización del request
        request = self.context.get('request') if isinstance(self.context, dict) else None
        if request is not None:
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                request.headers.get('Authorization') if hasattr(request, 'headers') else None
            )
            if auth_header:
                headers['Authorization'] = auth_header

        try:
            resp = requests.post(url, json={'ids': [user_id]}, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.content:
                payload = resp.json() or {}
                data = payload.get('data') or []
                if isinstance(data, list):
                    for u in data:
                        try:
                            if u and str(u.get('id')) == str(user_id):
                                self._ext_users_cache[user_id] = u
                                return u
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f'Error consultando servicio externo de usuarios: {str(e)}')

        return {}

    def _get_user_by_document(self, document_number: str) -> Dict[str, Any]:
        """Obtiene información detallada del usuario por documento."""
        if not document_number:
            return {}

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            return {}

        url = f"{base_url}/users/users/by-document/{document_number}"
        headers = {'Content-Type': 'application/json'}

        # Obtener header de autorización del request
        context = self.context if isinstance(self.context, dict) else {}
        request = context.get('request')
        if request is not None:
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                request.headers.get('Authorization') if hasattr(request, 'headers') else None
            )
            if auth_header:
                headers['Authorization'] = auth_header

        try:
            logger.info(f"Consultando detalle de usuario por documento: {url}")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200 and resp.content:
                data = resp.json() or {}
                logger.info(f"Respuesta servicio externo (by-document): {data}")
                return data
            else:
                logger.warning(f"Error consultando por documento {document_number}: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f'Error consultando servicio externo de usuarios por documento: {str(e)}')

        return {}

    def get_personal_info(self, obj: Employee) -> Dict[str, Any]:
        """Obtiene la información personal del empleado desde el servicio externo."""
        user_id = getattr(obj, 'id_user_id', None)
        
        # 1. Obtener datos básicos (posiblemente de caché)
        basic_data = self._get_external_user(user_id) if user_id else {}
        logger.info(f"Datos básicos usuario {user_id}: {basic_data}")
        
        # 2. Intentar obtener datos detallados si tenemos documento
        user_data = basic_data.copy() if basic_data else {}
        document_number = basic_data.get('document_number')
        
        if document_number:
            # Intentar obtener detalle completo
            detailed_data = self._get_user_by_document(str(document_number))
            # Si obtenemos datos, intentar usarlos
            # La respuesta del endpoint by-document podría venir envuelta en "data" o ser directa
            # Verificamos ambas estructuras
            actual_data = detailed_data.get('data', detailed_data) if isinstance(detailed_data, dict) else detailed_data
            
            if actual_data and isinstance(actual_data, dict):
                 # Verificar si es el mismo usuario por ID o documento
                 ext_id = str(actual_data.get('id', ''))
                 ext_doc = str(actual_data.get('document_number', ''))
                 
                 if (user_id and ext_id == str(user_id)) or (str(document_number) == ext_doc):
                     logger.info(f"Actualizando con datos detallados para usuario {user_id}")
                     user_data.update(actual_data)
                     # Actualizar caché con los datos detallados
                     if user_id:
                         self._ext_users_cache[user_id] = user_data

        logger.info(f"Datos finales usuario {user_id}: {user_data}")

        # Construir nombre completo
        name_parts = []
        name = user_data.get('name', '').strip() if user_data else None
        first_last_name = user_data.get('first_last_name', '').strip() if user_data else None
        second_last_name = user_data.get('second_last_name', '').strip() if user_data else None

        if name:
            name_parts.append(name)
        if first_last_name:
            name_parts.append(first_last_name)
        if second_last_name:
            name_parts.append(second_last_name)

        full_name = ' '.join(name_parts) if name_parts else None

        return {
            'id_user': getattr(obj, 'id_user_id', None),
            'full_name': full_name,
            'document_type': user_data.get('type_document_name') if user_data else None,
            'document_number': str(user_data.get('document_number')) if user_data and user_data.get('document_number') else None,
            'gender': user_data.get('gender_name') if user_data else None,  # Nombre del género
            'gender_id': user_data.get('gender_id') or user_data.get('gender') if user_data else None,  # ID del género
            'birth_date': user_data.get('birthday') if user_data else None,  # Corregido: usar birthday en lugar de birth_date
            'email': getattr(obj, 'email', None),
            'phone': user_data.get('phone') if user_data else None,
            'country': user_data.get('country') if user_data else None,
            'state': user_data.get('department') if user_data else None,  # Corregido: usar department en lugar de state
            'city': user_data.get('city') if user_data else None,  # Nota: viene como ID numérico del servicio externo
            'address': user_data.get('address') if user_data else None,
        }

    def get_contract_info(self, obj: Employee) -> Dict[str, Any]:
        """Obtiene la información del contrato del empleado."""
        charge = getattr(obj, 'id_employee_charge', None)
        department = getattr(charge, 'id_employee_department', None) if charge else None
        status = getattr(obj, 'employee_status', None)

        # Obtener último contrato del empleado
        contract_code = None
        contracts = getattr(obj, 'employee_contracts', None)
        if contracts:
            # Obtener el contrato más reciente ordenado por creation_date
            latest_contract = contracts.order_by('-creation_date').first()
            if latest_contract:
                contract_code = getattr(latest_contract, 'contract_code', None)

        return {
            'status_id': getattr(status, 'id_statues', None) if status else None,
            'status_name': getattr(status, 'name', None) if status else None,
            'charge_id': getattr(charge, 'id_employee_charge', None) if charge else None,
            'charge_name': getattr(charge, 'name', None) if charge else None,
            'department_id': getattr(department, 'id_employee_department', None) if department else None,
            'department_name': getattr(department, 'name', None) if department else None,
            'contract_code': contract_code,
        }

    def get_news_history(self, obj: Employee) -> list:
        """Obtiene el historial de novedades del empleado."""
        news_queryset = getattr(obj, 'employeenews_set', None)
        if not news_queryset:
            return []

        # Obtener todas las novedades ordenadas por fecha descendente
        news_list = news_queryset.select_related('id_responsible_user').order_by('-news_date').all()
        
        # Serializar las novedades
        serializer = EmployeeNewsSerializer(news_list, many=True, context=self.context)
        return serializer.data

