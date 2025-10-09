import logging
import os
from typing import Any, Dict, Optional

import requests
from rest_framework import serializers
from service_requests.models.customer import Customer


class CustomerDetailSerializer(serializers.ModelSerializer):
    """Detalle de cliente en el orden solicitado, incluyendo IDs (según modelo) y nombres de FKs."""

    # Campos que pueden ser sobreescritos por datos externos de usuario
    name = serializers.SerializerMethodField()
    first_last_name = serializers.SerializerMethodField()
    second_last_name = serializers.SerializerMethodField()
    document_number = serializers.SerializerMethodField()
    type_document_id = serializers.SerializerMethodField()
    type_document_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    # Nombres de FKs propios del cliente (no vienen del usuario externo)
    person_type_name = serializers.CharField(source='person_type.name', read_only=True)
    customer_statues_name = serializers.CharField(source='customer_statues.name', read_only=True)

    _logger = logging.getLogger(__name__)

    def _get_external_user(self, obj: Customer) -> Dict[str, Any]:
        """Obtiene la info básica del usuario desde el servicio externo.
        Retorna {} si no hay info o en caso de error.
        """
        # Cache por instancia de serializer para evitar múltiples llamadas
        cache_key = '_ext_user_cache'
        cached = getattr(self, cache_key, None)
        if cached is not None:
            return cached

        user_id = getattr(obj, 'id_user_id', None)
        if not user_id:
            setattr(self, cache_key, {})
            return {}

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            self._logger.warning('AUTH_SERVICE_URL no configurado')
            setattr(self, cache_key, {})
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
                self._logger.warning('External user service returned %s', resp.status_code)
                setattr(self, cache_key, {})
                return {}
            payload = resp.json() if resp.content else {}
            data = (payload or {}).get('data') or []
            if not isinstance(data, list):
                setattr(self, cache_key, {})
                return {}
            # Buscar el usuario con el id solicitado
            for u in data:
                try:
                    if str(u.get('id')) == str(user_id):
                        setattr(self, cache_key, u)
                        return u
                except Exception:
                    continue
            setattr(self, cache_key, {})
            return {}
        except Exception as e:
            self._logger.error('Error consultando servicio externo de usuarios: %s', str(e))
            setattr(self, cache_key, {})
            return {}

    def _ext(self, obj: Customer, key: str) -> Optional[Any]:
        data = self._get_external_user(obj)
        return data.get(key) if isinstance(data, dict) else None

    # Preferir datos del usuario externo cuando existan; si no, devolver del modelo Customer
    def get_name(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'name') or obj.name

    def get_first_last_name(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'first_last_name') or obj.first_last_name

    def get_second_last_name(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'second_last_name') or obj.second_last_name

    def get_document_number(self, obj: Customer) -> Optional[Any]:
        return self._ext(obj, 'document_number') or obj.document_number

    def get_type_document_id(self, obj: Customer) -> Optional[Any]:
        # del usuario externo viene como 'type_document' (id). Si no hay, devolver el FK del cliente
        return self._ext(obj, 'type_document') or getattr(obj, 'type_document_id_id', None)

    def get_type_document_name(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'type_document_name') or (obj.type_document_id.name if obj.type_document_id else None)

    def get_email(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'email') or obj.email

    def get_phone(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'phone') or obj.phone

    def get_address(self, obj: Customer) -> Optional[str]:
        return self._ext(obj, 'address') or obj.address

    class Meta:
        model = Customer
        fields = [
            # Orden solicitado (con IDs y nombres para FKs)
            'id_customer',
            'id_user',
            'document_number',
            'type_document_id',
            'type_document_name',
            'check_digit',
            'person_type_id',
            'person_type_name',
            'legal_entity_name',
            'name',
            'first_last_name',
            'second_last_name',
            'email',
            'phone',
            'address',
            'id_municipality',
            'tax_regime',
            'customer_statues_id',
            'customer_statues_name',
        ]

