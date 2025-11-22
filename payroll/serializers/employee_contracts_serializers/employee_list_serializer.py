from rest_framework import serializers
import os
import requests
import logging
from typing import Dict, Optional, Any

from payroll.models import Employee

logger = logging.getLogger(__name__)


class EmployeeListSerializer(serializers.ModelSerializer):
    """Serializer para listar empleados con información básica."""
    
    document_number = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    charge_name = serializers.SerializerMethodField()
    charge_id = serializers.IntegerField(source='id_employee_charge.id_employee_charge', read_only=True)
    status_id = serializers.IntegerField(source='employee_status.id_statues', read_only=True)
    status_name = serializers.CharField(source='employee_status.name', read_only=True)
    id_user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id_employee',
            'id_user',
            'document_number',
            'full_name',
            'charge_name',
            'charge_id',
            'status_id',
            'status_name',
            'email',
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

    def get_document_number(self, obj: Employee) -> Optional[str]:
        """Obtiene el número de documento del usuario desde el servicio externo."""
        user_id = getattr(obj, 'id_user_id', None)
        if not user_id:
            return None

        user_data = self._get_external_user(user_id)
        if user_data:
            document_number = user_data.get('document_number')
            return str(document_number) if document_number else None

        return None

    def get_full_name(self, obj: Employee) -> Optional[str]:
        """Obtiene el nombre completo del usuario desde el servicio externo."""
        user_id = getattr(obj, 'id_user_id', None)
        if not user_id:
            return None

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

    def get_charge_name(self, obj: Employee) -> Optional[str]:
        """Obtiene el nombre del cargo del empleado."""
        charge = getattr(obj, 'id_employee_charge', None)
        return getattr(charge, 'name', None) if charge else None

