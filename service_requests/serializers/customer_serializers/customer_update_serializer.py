import os
import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from service_requests.models.customer import Customer
from django.utils import timezone
import requests
from users.models.user import User

logger = logging.getLogger(__name__)

class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para la actualización de clientes.
    """
    class Meta:
        model = Customer
        fields = [
            'id_user',
            'document_number',
            'type_document_id',
            'check_digit',
            'person_type',
            'legal_entity_name',
            'name',
            'first_last_name',
            'second_last_name',
            'email',
            'phone',
            'address',
            'id_municipality',
            'tax_regime'
        ]
        extra_kwargs = {
            'type_document_id': {'required': False},
            'check_digit': {'required': False},
            'person_type': {'required': False},
            'legal_entity_name': {'required': False},
            'name': {'required': False},
            'first_last_name': {'required': False},
            'second_last_name': {'required': False},
            'email': {'required': False},
            'phone': {'required': False},
            'address': {'required': False},
            'id_municipality': {'required': False},
            'tax_regime': {'required': False}
        }

    def validate_id_user(self, value):
        """
        Validar que el id_user sea único.
        """
        if value and Customer.objects.filter(id_user=value).exclude(id_customer=self.instance.id_customer).exists():
            raise serializers.ValidationError("Ya existe otro cliente con este usuario.")
        return value

    def validate_document_number(self, value):
        """
        Validar que el document_number sea único, solo contenga números positivos
        y no exceda los 10 dígitos.
        """
        if value is not None:
            str_value = str(value)
            if not str_value.isdigit():
                raise serializers.ValidationError("El número de documento solo puede contener dígitos.")
            
            if int(value) < 0:
                raise serializers.ValidationError("El número de documento no puede ser negativo.")
            
            if len(str_value) > 10:
                raise serializers.ValidationError("El número de documento no puede tener más de 10 dígitos.")
            
            if Customer.objects.filter(document_number=value).exclude(id_customer=self.instance.id_customer).exists():
                raise serializers.ValidationError("Ya existe otro cliente con este número de documento.")
        
        return value

    def validate(self, data):
        """
        Validaciones personalizadas para la actualización.
        """
        request = self.context.get('request')
        id_user = data.get('id_user')
        document_number = data.get('document_number')
        instance = self.instance
        
        # Si se proporciona id_user (y no es null), validar que no esté asociado a otro cliente
        if id_user is not None and id_user != 'null':
            from users.models.user import User
            try:
                # Obtener la instancia de User
                if isinstance(id_user, User):
                    user_instance = id_user
                else:
                    user_instance = User.objects.get(id_user=id_user)
                
                # Limpiar campos de identificación
                data['document_number'] = None
                data['type_document_id'] = None
                data['name'] = None
                data['first_last_name'] = None
                data['second_last_name'] = None
                data['email'] = None
                data['phone'] = None
                data['address'] = None
                
                # Asignar la instancia de User
                data['id_user'] = user_instance
                
                return data
                
            except (User.DoesNotExist, AttributeError):
                raise serializers.ValidationError({
                    'id_user': 'El usuario especificado no existe.'
                })
        
        # Si no se proporciona id_user (o es null) y se proporciona document_number
        elif document_number is not None and (id_user is None or id_user == 'null'):
            # Si el documento es diferente al actual, validar en el servicio externo
            if str(document_number) != str(instance.document_number or ''):
                try:
                    # Obtener el token del usuario autenticado
                    if request and hasattr(request, 'user'):
                        auth_header = request.META.get('HTTP_AUTHORIZATION')
                        if not auth_header and hasattr(request, 'headers'):
                            auth_header = request.headers.get('Authorization')
                        
                        headers = {}
                        if auth_header:
                            headers['Authorization'] = auth_header
                        
                        # Obtener la URL del servicio externo de las variables de entorno
                        base_url = os.getenv('AUTH_SERVICE_URL')
                        if not base_url:
                            logger.warning("AUTH_SERVICE_URL no está configurado. No se puede verificar el documento.")
                            return data
                            
                        # Construir la URL completa
                        url = f"{base_url}users/users/by-document/{document_number}"
                        response = requests.get(url, headers=headers, timeout=5)
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            # Verificar si la respuesta tiene el formato esperado
                            if response_data.get('success') and 'data' in response_data and response_data['data']:
                                user_data = response_data['data']
                                # Verificar si el usuario ya está asociado a otro cliente
                                if Customer.objects.filter(id_user=user_data['id']).exclude(id_customer=instance.id_customer).exists():
                                    raise serializers.ValidationError({
                                        'document_number': 'El usuario asociado a este documento ya está registrado en otro cliente.'
                                    })
                                
                                # Obtener la instancia de User
                                from users.models.user import User
                                try:
                                    user_instance = User.objects.get(id_user=user_data['id'])
                                    # Asignar la instancia de User
                                    data['id_user'] = user_instance
                                    # Limpiar campos de identificación
                                    data['document_number'] = None
                                    data['type_document_id'] = None
                                    data['name'] = None
                                    data['first_last_name'] = None
                                    data['second_last_name'] = None
                                    data['email'] = None
                                    data['phone'] = None
                                    data['address'] = None
                                    return data
                                except User.DoesNotExist:
                                    logger.warning(f"Usuario con id {user_data['id']} no encontrado en la base de datos local")
                                    # Si el usuario no existe localmente, continuar con la validación normal
                            
                            # Si no se encontró el documento en el servicio externo, continuar con la actualización normal
                            logger.info(f"Documento {document_number} no encontrado en el servicio externo")
                            
                        elif response.status_code == 404:
                            # Si el servicio externo devuelve 404, el documento no existe
                            logger.info(f"Documento {document_number} no encontrado en el servicio externo (404)")
                            # Continuar con la actualización normal
                            
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error al verificar documento en servicio externo: {str(e)}")
                    # Si hay error en la conexión, continuar con la validación normal
                
                # Si llegamos aquí, el documento no se encontró en el servicio externo o hubo un error
                # Verificar que el documento no esté en uso por otro cliente
                if Customer.objects.filter(document_number=document_number).exclude(id_customer=instance.id_customer).exists():
                    raise serializers.ValidationError({
                        'document_number': 'Este número de documento ya está en uso por otro cliente.'
                    })
        
        # Verificar que el email no esté en uso por otro cliente
        email = data.get('email')
        if email and email != instance.email:
            if Customer.objects.filter(email=email).exclude(id_customer=instance.id_customer).exists():
                raise serializers.ValidationError({
                    'email': 'Este correo electrónico ya está en uso por otro cliente.'
                })
        
        return data

    def update(self, instance, validated_data):
        """
        Actualiza un cliente con los datos validados.
        """
        # Actualizar los campos proporcionados
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Guardar los cambios
        instance.save()
        
        return instance
