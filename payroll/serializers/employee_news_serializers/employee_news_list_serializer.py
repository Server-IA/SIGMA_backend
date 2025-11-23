from rest_framework import serializers
import os
import requests
import logging
from typing import Dict, Optional, Any

from payroll.models import EmployeeNews

logger = logging.getLogger(__name__)


class EmployeeNewsListSerializer(serializers.ModelSerializer):
    """Serializer para listar novedades de empleados con información completa."""
    
    news_date = serializers.DateTimeField(read_only=True)
    author_name = serializers.SerializerMethodField()
    news_type_display = serializers.CharField(source='get_news_type_display', read_only=True)
    observation = serializers.CharField(read_only=True)
    employee_associated = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeNews
        fields = [
            'id_employee_new',
            'news_date',
            'author_name',
            'news_type',
            'news_type_display',
            'observation',
            'employee_associated',
            'origin',
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

    def get_author_name(self, obj: EmployeeNews) -> Optional[str]:
        """Obtiene el nombre completo del autor desde el servicio externo."""
        user_id = getattr(obj, 'id_responsible_user_id', None)
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

    def get_employee_associated(self, obj: EmployeeNews) -> Optional[str]:
        """
        Obtiene el empleado asociado en formato: 'documento - nombre completo'.
        Ejemplo: '1079172267 - Juan pablo de la Cruz'
        """
        employee = getattr(obj, 'id_employee', None)
        if not employee:
            return None

        user_id = getattr(employee, 'id_user_id', None)
        if not user_id:
            return None

        user_data = self._get_external_user(user_id)
        if user_data:
            # Obtener documento
            document_number = user_data.get('document_number')
            if not document_number:
                return None
            
            # Construir nombre completo
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

            full_name = ' '.join(name_parts) if name_parts else None
            
            if full_name:
                return f"{document_number} - {full_name}"
            else:
                return str(document_number)

        return None

    def get_origin(self, obj: EmployeeNews) -> str:
        """
        Determina el origen de la novedad.
        Si id_responsible_user no es null, entonces es 'Automática', sino 'Carga masiva'.
        """
        user_id = getattr(obj, 'id_responsible_user_id', None)
        return 'Automática' if user_id else 'Carga masiva'
