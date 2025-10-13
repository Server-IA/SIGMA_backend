"""
Serializer para la actualización de clientes.
"""
import logging
import os
from typing import Any, Dict, Optional

import requests
from rest_framework import serializers
from service_requests.models.customer import Customer
from service_requests.models.document_type import DocumentType
from service_requests.models.person_type import PersonType
from parameterization.models import Statues


logger = logging.getLogger(__name__)


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar clientes con validaciones específicas del negocio.
    """

    class Meta:
        model = Customer
        fields = [
            'name',
            'first_last_name',
            'second_last_name',
            'document_number',
            'type_document_id',
            'check_digit',
            'person_type',
            'legal_entity_name',
            'email',
            'phone',
            'address',
            'id_municipality',
            'tax_regime',
            'id_user'
        ]

    def validate_document_number(self, value):
        """Valida que el número de documento sea único y cumpla las reglas de negocio."""
        if not value:
            raise serializers.ValidationError("El número de documento es requerido.")
        
        # Validar que sea numérico y no negativo
        try:
            doc_num = int(str(value))
            if doc_num < 0:
                raise serializers.ValidationError("El número de documento no puede ser negativo.")
        except ValueError:
            raise serializers.ValidationError("El número de documento debe ser numérico.")
        
        # Validar longitud máxima (10 dígitos)
        if len(str(value)) > 10:
            raise serializers.ValidationError("El número de documento no puede superar los 10 dígitos.")
        
        # Obtener la instancia actual (si se está actualizando)
        instance = getattr(self, 'instance', None)
        
        # Verificar si ya existe un cliente con el mismo documento
        queryset = Customer.objects.filter(document_number=value)
        
        # Si estamos actualizando, excluir la instancia actual
        if instance:
            queryset = queryset.exclude(id_customer=instance.id_customer)
            
        if queryset.exists():
            raise serializers.ValidationError(
                "Ya existe un cliente con este número de documento."
            )
        
        return value

    def validate_type_document_id(self, value):
        """Valida que el tipo de documento exista."""
        if value is None:
            return value
            
        # Si es una instancia de DocumentType, obtener su ID
        if hasattr(value, 'id_document_type'):
            value_id = value.id_document_type
        else:
            value_id = value
            
        try:
            DocumentType.objects.get(id_document_type=value_id)
        except DocumentType.DoesNotExist:
            raise serializers.ValidationError("El tipo de documento no existe.")
        return value

    def validate_person_type(self, value):
        """Valida que el tipo de persona exista."""
        if value is None:
            return value
            
        # Si es una instancia de PersonType, obtener su ID
        if hasattr(value, 'id_person_type'):
            value_id = value.id_person_type
        else:
            value_id = value
            
        try:
            PersonType.objects.get(id_person_type=value_id)
        except PersonType.DoesNotExist:
            raise serializers.ValidationError("El tipo de persona no existe.")
        return value

    def validate_email(self, value):
        """Valida el formato del email y unicidad."""
        if not value:
            raise serializers.ValidationError("El email es requerido.")
        
        # Obtener la instancia actual (si se está actualizando)
        instance = getattr(self, 'instance', None)
        
        # Verificar unicidad del email
        queryset = Customer.objects.filter(email=value)
        
        # Si estamos actualizando, excluir la instancia actual
        if instance:
            queryset = queryset.exclude(id_customer=instance.id_customer)
            
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un cliente con este email.")
        
        return value

    def validate_id_user(self, value):
        """Valida el usuario asociado si se proporciona."""
        if value:
            # Verificar que no esté ya asociado a otro cliente
            instance = getattr(self, 'instance', None)
            
            queryset = Customer.objects.filter(id_user=value)
            
            # Si estamos actualizando, excluir la instancia actual
            if instance:
                queryset = queryset.exclude(id_customer=instance.id_customer)
                
            if queryset.exists():
                raise serializers.ValidationError(
                    "El usuario ya está asociado a otro cliente."
                )
        
        return value

    def validate_name(self, value):
        """Valida la longitud máxima del nombre."""
        if value and len(value) > 100:
            raise serializers.ValidationError("El nombre no puede exceder los 100 caracteres.")
        return value

    def validate_first_last_name(self, value):
        """Valida la longitud máxima del primer apellido."""
        if value and len(value) > 100:
            raise serializers.ValidationError("El primer apellido no puede exceder los 100 caracteres.")
        return value

    def validate_second_last_name(self, value):
        """Valida la longitud máxima del segundo apellido."""
        if value and len(value) > 100:
            raise serializers.ValidationError("El segundo apellido no puede exceder los 100 caracteres.")
        return value

    def validate_phone(self, value):
        """Valida la longitud máxima del teléfono."""
        if value and len(value) > 100:
            raise serializers.ValidationError("El teléfono no puede exceder los 100 caracteres.")
        return value

    def validate_address(self, value):
        """Valida la longitud máxima de la dirección."""
        if value and len(value) > 100:
            raise serializers.ValidationError("La dirección no puede exceder los 100 caracteres.")
        return value

    def validate(self, attrs):
        """Validaciones a nivel de objeto."""
        # Validar combinación documento-tipo única
        document_number = attrs.get('document_number')
        document_type = attrs.get('id_document_type')
        
        if document_number and document_type:
            instance = getattr(self, 'instance', None)
            
            queryset = Customer.objects.filter(
                document_number=document_number,
                id_document_type=document_type
            )
            
            # Si estamos actualizando, excluir la instancia actual
            if instance:
                queryset = queryset.exclude(id_customer=instance.id_customer)
                
            if queryset.exists():
                raise serializers.ValidationError({
                    'document_number': 'Ya existe un cliente con este número y tipo de documento.'
                })

        return attrs

    def update(self, instance, validated_data):
        """Actualiza la instancia del cliente."""
        # Actualizar todos los campos proporcionados
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance