import logging
import os
from typing import Any, Dict, Optional

import requests
from rest_framework import serializers
from payroll.models import EmployeeContract


logger = logging.getLogger(__name__)


class EmployeeContractHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para listar el historial de contratos de un empleado.
    Solo muestra la última versión de cada contract_code.
    """
    
    contract_status_name = serializers.CharField(source='contract_status.name', read_only=True)
    responsible_user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeContract
        fields = [
            'contract_code',
            'start_date',
            'end_date',
            'creation_date',
            'id_responsible_user',
            'responsible_user_name',
            'contract_status',
            'contract_status_name',
        ]
        read_only_fields = ['contract_code', 'start_date', 'end_date', 'creation_date', 
                          'id_responsible_user', 'contract_status']
    
    def _get_external_user(self, obj: EmployeeContract) -> Dict[str, Any]:
        """
        Obtiene la info básica del usuario responsable desde el servicio externo.
        Retorna {} si no hay info o en caso de error.
        """
        user_id = getattr(obj, 'id_responsible_user_id', None)
        if not user_id:
            return {}

        # Usar un diccionario de caché por user_id para manejar múltiples usuarios
        cache_key = f'_ext_user_cache_{user_id}'
        cached = getattr(self, cache_key, None)
        if cached is not None:
            return cached

        # Inicializar el caché si no existe
        if not hasattr(self, '_ext_users_cache'):
            self._ext_users_cache = {}

        # Verificar si ya tenemos este usuario en caché
        if user_id in self._ext_users_cache:
            return self._ext_users_cache[user_id]

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            logger.warning('AUTH_SERVICE_URL no configurado')
            return {}

        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers: Dict[str, str] = {}
        request = self.context.get('request') if isinstance(self.context, dict) else None
        if request is not None:
            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                request.headers.get('Authorization') if hasattr(request, 'headers') else None
            )
            if auth_header:
                headers['Authorization'] = auth_header

        try:
            resp = requests.post(url, json={'ids': [user_id]}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning('External user service returned %s', resp.status_code)
                return {}
                
            payload = resp.json() if resp.content else {}
            data = (payload or {}).get('data') or []
            if not isinstance(data, list):
                return {}
                
            # Buscar el usuario con el id solicitado
            for u in data:
                try:
                    if u and str(u.get('id')) == str(user_id):
                        # Guardar en caché para este user_id
                        self._ext_users_cache[user_id] = u
                        return u
                except Exception as e:
                    logger.error(f'Error procesando usuario {user_id}: {str(e)}')
                    continue
                    
            return {}
            
        except Exception as e:
            logger.error('Error consultando servicio externo de usuarios: %s', str(e))
            return {}

    def get_responsible_user_name(self, obj: EmployeeContract) -> Optional[str]:
        """
        Obtiene el nombre completo del usuario responsable concatenando:
        name + first_last_name + second_last_name
        """
        user_data = self._get_external_user(obj)
        
        if not user_data:
            return None
        
        name_parts = []
        
        # Agregar name si existe
        name = user_data.get('name')
        if name:
            name_parts.append(str(name).strip())
        
        # Agregar first_last_name si existe
        first_last_name = user_data.get('first_last_name')
        if first_last_name:
            name_parts.append(str(first_last_name).strip())
        
        # Agregar second_last_name si existe
        second_last_name = user_data.get('second_last_name')
        if second_last_name:
            name_parts.append(str(second_last_name).strip())
        
        # Unir todas las partes con espacios
        full_name = ' '.join(name_parts) if name_parts else None
        
        return full_name
    
    def to_representation(self, instance):
        """
        Formatea las fechas correctamente.
        """
        representation = super().to_representation(instance)
        
        # Formatear fechas
        date_fields = ['start_date', 'end_date']
        for field in date_fields:
            if representation.get(field):
                representation[field] = representation[field].split('T')[0] if 'T' in str(representation[field]) else str(representation[field])
        
        # Formatear creation_date (DateTimeField)
        if representation.get('creation_date'):
            creation_date = representation['creation_date']
            if 'T' in str(creation_date):
                representation['creation_date'] = creation_date.split('T')[0]
        
        return representation

