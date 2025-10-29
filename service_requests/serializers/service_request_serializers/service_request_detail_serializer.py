import logging
import os
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from rest_framework import serializers

from machinery.models.machinery import Machinery
from parameterization.models.units import Units
from service_requests.models.request_location import RequestLocation
from service_requests.models.request_machinery_user import RequestMachineryUser
from service_requests.models.service_request import ServiceRequest
from users.models.user import User

logger = logging.getLogger(__name__)

class RequestMachineryUserSerializer(serializers.ModelSerializer):
    machinery_name = serializers.CharField(source='machinery.name', read_only=True)
    serial_number = serializers.CharField(source='machinery.serial_number', read_only=True)
    machinery_image_path = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    id_machinery = serializers.IntegerField(source='machinery.id_machinery', read_only=True)
    id_user = serializers.IntegerField(source='user.id_user', read_only=True)
    soil_type_id = serializers.PrimaryKeyRelatedField(source='soil_type', read_only=True)
    soil_type_surface = serializers.SerializerMethodField()
    texture_id = serializers.PrimaryKeyRelatedField(source='texture', read_only=True)
    texture_texture = serializers.SerializerMethodField()
    implementation_id = serializers.PrimaryKeyRelatedField(source='implementation', read_only=True)
    implementation_name = serializers.SerializerMethodField()

    def get_soil_type_surface(self, obj):
        return obj.soil_type.surface if obj.soil_type else None

    def get_texture_texture(self, obj):
        return obj.texture.texture if obj.texture else None

    def get_implementation_name(self, obj):
        return obj.implementation.name if obj.implementation else None

    class Meta:
        model = RequestMachineryUser
        fields = [
            'id_request_machinery_user', 
            'request', 
            'machinery',
            'id_machinery',
            'machinery_name',
            'serial_number',
            'machinery_image_path',
            'user',
            'id_user',
            'user_name',
            'soil_type_id',
            'soil_type_surface',
            'texture_id',
            'texture_texture',
            'humidity_level',
            'implementation_id',
            'implementation_name',
            'depth',
            'slope',
            'work_duration'
        ]
        extra_kwargs = {
            'request': {'write_only': True},
            'machinery': {'write_only': True},
            'user': {'write_only': True},
            'soil_type': {'write_only': True},
            'texture': {'write_only': True},
            'implementation': {'write_only': True}
        }

    def get_machinery_image_path(self, obj):
        if obj.machinery and obj.machinery.image_path:
            return obj.machinery.image_path.url if hasattr(obj.machinery.image_path, 'url') else str(obj.machinery.image_path)
        return None

    def _get_external_user(self, user_id: int) -> Dict[str, Any]:
        """Obtiene la info básica del usuario desde el servicio externo.
        Retorna {} si no hay info o en caso de error.
        """
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

    def get_user_name(self, obj):
        if not obj.user:
            return None
            
        # Obtener información del usuario desde el servicio externo
        user_info = self._get_external_user(obj.user.id_user)
        if user_info:
            return f"{user_info.get('name', '')} {user_info.get('first_last_name', '')} {user_info.get('second_last_name', '')}".strip()
            
        return None


class RequestLocationSerializer(serializers.ModelSerializer):
    area_unit_id = serializers.PrimaryKeyRelatedField(
        source='area_unit',
        read_only=True
    )
    area_unit_name = serializers.CharField(source='area_unit.name', read_only=True)
    area_unit_symbol = serializers.CharField(source='area_unit.symbol', read_only=True)
    
    altitude_unit_id = serializers.PrimaryKeyRelatedField(
        source='altitude_unit',
        read_only=True
    )
    altitude_unit_name = serializers.CharField(source='altitude_unit.name', read_only=True)
    altitude_unit_symbol = serializers.CharField(source='altitude_unit.symbol', read_only=True)

    class Meta:
        model = RequestLocation
        fields = [
            'id_request_location', 'country', 'department', 'city_id', 'place_name',
            'latitude', 'longitude', 'area', 'area_unit_id', 'area_unit_name',
            'area_unit_symbol', 'altitude', 'altitude_unit_id', 'altitude_unit_name', 
            'altitude_unit_symbol'
        ]
        extra_kwargs = {
            'request': {'write_only': True},
            'area_unit': {'write_only': True},
            'altitude_unit': {'write_only': True}
        }


class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    # Customer fields
    customer_id = serializers.SerializerMethodField()
    customer_id_user = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_first_last_name = serializers.SerializerMethodField()
    customer_second_last_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    customer_legal_entity_name = serializers.SerializerMethodField()
    customer_document_type = serializers.SerializerMethodField()
    customer_document_number = serializers.SerializerMethodField()
    
    # Confirmation user fields
    confirmation_user_name = serializers.SerializerMethodField()
    completion_cancellation_user_name = serializers.SerializerMethodField()
    
    # Related fields
    request_status_id = serializers.PrimaryKeyRelatedField(
            source='request_status',
            read_only=True
        )
    request_status_name = serializers.CharField(source='request_status.name', read_only=True)
    payment_status_id = serializers.PrimaryKeyRelatedField(
            source='payment_status',
            read_only=True
        )
    payment_status_name = serializers.CharField(source='payment_status.name', read_only=True)
    currency_unit_amount_paid_name = serializers.CharField(source='currency_unit_amount_paid.name', read_only=True, allow_null=True)
    currency_unit_amount_paid_symbol = serializers.CharField(source='currency_unit_amount_paid.symbol', read_only=True, allow_null=True)
    currency_unit_amount_to_pay_name = serializers.CharField(source='currency_unit_amount_to_pay.name', read_only=True, allow_null=True)
    currency_unit_amount_to_pay_symbol = serializers.CharField(source='currency_unit_amount_to_pay.symbol', read_only=True, allow_null=True)
    currency_unit_amount_paid_id = serializers.PrimaryKeyRelatedField(
            source='currency_unit_amount_paid',
            read_only=True
        )
    currency_unit_amount_to_pay_id = serializers.PrimaryKeyRelatedField(
            source='currency_unit_amount_to_pay',
            read_only=True
        )  
    # Payment method fields
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True, allow_null=True)
    payment_method_code = serializers.CharField(source='payment_method.code', read_only=True, allow_null=True)  # Keeping for backward compatibility
    
    # Invoice field
    invoice_id = serializers.SerializerMethodField()
    
    # Nested serializers
    request_machinery_user = RequestMachineryUserSerializer(many=True, read_only=True, source='machinery_users')
    request_location = RequestLocationSerializer(read_only=True)
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id_request',
            # Customer info
            'customer', 'customer_id', 'customer_id_user', 'customer_legal_entity_name', 
            'customer_name', 'customer_first_last_name', 'customer_second_last_name',
            'customer_email', 'customer_phone', 'customer_document_type', 'customer_document_number',
            
            # Request details
            'request_detail', 'scheduled_start_date', 'scheduled_end_date',
            
            # Confirmation fields
            'confirmation_user', 'confirmation_user_name', 'confirmation_datetime',
            'completion_cancellation_observations', 'completion_cancellation_datetime',
            'completion_cancellation_user', 'completion_cancellation_user_name',
            
            # Status
            'request_status', 'request_status_id', 'request_status_name',
            
            # Machinery and location
            'request_machinery_user', 'request_location',
            
            # Payment info
            'amount_paid', 
            'currency_unit_amount_paid', 'currency_unit_amount_paid_id',
            'currency_unit_amount_paid_name', 'currency_unit_amount_paid_symbol', 
            'amount_to_pay', 
            'currency_unit_amount_to_pay', 'currency_unit_amount_to_pay_id',
            'currency_unit_amount_to_pay_name', 'currency_unit_amount_to_pay_symbol',
            'payment_status', 'payment_status_id', 'payment_status_name', 
            'payment_method_code', 'payment_method_name',
            
            # Invoice
            'invoice_id'
        ]
        extra_kwargs = {
            'customer': {'write_only': True},
            'confirmation_user': {'write_only': True},
            'completion_cancellation_user': {'write_only': True},
            'request_status': {'write_only': True},
            'payment_status': {'write_only': True},
            'currency_unit_amount_paid': {'write_only': True},
            'currency_unit_amount_to_pay': {'write_only': True},
            'payment_method': {'write_only': True}
        }

    def _get_external_user(self, user_id: int) -> Dict[str, Any]:
        """Obtiene la info básica del usuario desde el servicio externo.
        Retorna {} si no hay info o en caso de error.
        """
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

        # Note the different endpoint path here: /users/users/ instead of /users/
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
            # Note the different payload format here: {'ids': [user_id]} instead of {'user_ids': [user_id]}
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

    def get_customer_id(self, obj):
        return obj.customer.id_customer if obj.customer else None
        
    def get_customer_id_user(self, obj):
        return obj.customer.id_user_id if obj.customer else None

    def _get_customer_info(self, customer):
        """Get customer information, either from the customer model or user service."""
        if not customer:
            return {}
            
        # If customer has an id_user, fetch from user service
        if customer.id_user_id:
            user_info = self._get_external_user(customer.id_user_id)
            if user_info:
                return {
                    'id': customer.id_customer,
                    'id_user': customer.id_user_id,
                    'legal_entity_name': customer.legal_entity_name,
                    'name': user_info.get('name', ''),
                    'first_last_name': user_info.get('first_last_name', ''),
                    'second_last_name': user_info.get('second_last_name', ''),
                    'email': user_info.get('email', ''),
                    'phone': user_info.get('phone', ''),
                    'document_type': user_info.get('type_document_name'),
                    'document_number': user_info.get('document_number'),
                    'type_document_id': user_info.get('type_document')
                }
        
        # Fall back to customer model fields
        return {
            'id': customer.id_customer,
            'id_user': customer.id_user_id,
            'legal_entity_name': customer.legal_entity_name,
            'name': customer.name or '',
            'first_last_name': customer.first_last_name or '',
            'second_last_name': customer.second_last_name or '',
            'email': customer.email or '',
            'phone': customer.phone or '',
            'document_type': customer.type_document_id.name if customer.type_document_id else None,
            'document_number': customer.document_number,
            'type_document_id': customer.type_document_id_id
        }

    def get_customer_name(self, obj):
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('name')

    def get_customer_document_type(self, obj):
        if not obj.customer:
            return None
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('document_type')

    def get_customer_document_number(self, obj):
        if not obj.customer:
            return None
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('document_number')

    def get_customer_legal_entity_name(self, obj):
        if not obj.customer:
            return None
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('legal_entity_name')

    def get_area_unit_id(self, obj):
        return obj.request_location.area_unit_id if hasattr(obj, 'request_location') and obj.request_location else None

    def get_soil_type_id(self, obj):
        return obj.request_location.soil_type_id if hasattr(obj, 'request_location') and obj.request_location else None

    def get_altitude_unit_id(self, obj):
        return obj.request_location.altitude_unit_id if hasattr(obj, 'request_location') and obj.request_location else None

    def get_customer_first_last_name(self, obj):
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('first_last_name')

    def get_customer_second_last_name(self, obj):
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('second_last_name')

    def get_customer_email(self, obj):
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('email')

    def get_customer_phone(self, obj):
        customer_info = self._get_customer_info(obj.customer)
        return customer_info.get('phone')
        
    def get_customer_legal_entity_name(self, obj):
        return obj.customer.legal_entity_name if obj.customer else None

    def get_confirmation_user_name(self, obj):
        if not obj.confirmation_user:
            return None
        user_info = self._get_external_user(obj.confirmation_user.id_user)
        if user_info:
            return f"{user_info.get('name', '')} {user_info.get('first_last_name', '')} {user_info.get('second_last_name', '')}".strip()
        return None

    def get_completion_cancellation_user_name(self, obj):
        if not obj.completion_cancellation_user:
            return None
        user_info = self._get_external_user(obj.completion_cancellation_user.id_user)
        if user_info:
            return f"{user_info.get('name', '')} {user_info.get('first_last_name', '')} {user_info.get('second_last_name', '')}".strip()
        return None

    def get_invoice_id(self, obj):
        """
        Retorna el ID de la factura validada asociada a esta solicitud.
        Retorna None si no hay factura validada (status_id = 26).
        """
        try:
            # Buscar factura con estado VALIDADA (26)
            validated_invoice = obj.invoices.filter(status_id=26).first()
            return validated_invoice.id_invoice if validated_invoice else None
        except Exception:
            return None
