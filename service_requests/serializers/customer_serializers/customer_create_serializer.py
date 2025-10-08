import os
import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from service_requests.models.customer import Customer
from parameterization.models import Types, TypesCategory
from django.utils import timezone
import requests
from users.models.user import User

logger = logging.getLogger(__name__)

class CustomerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de clientes.
    """
    class Meta:
        model = Customer
        fields = [
            'id_user',
            'document_number',
            'type_document_id',
            'person_type',
            'name',
            'first_last_name',
            'second_last_name',
            'email',
            'phone',
            'address'
        ]
        extra_kwargs = {
            'type_document_id': {'required': False},
            'person_type': {'required': True},
            'name': {'required': False},
            'first_last_name': {'required': False},
            'second_last_name': {'required': False},
            'email': {'required': False},
            'phone': {'required': False},
            'address': {'required': False},
        }

    def validate_id_user(self, value):
        """
        Validar que el id_user sea único.
        """
        if value and Customer.objects.filter(id_user=value).exists():
            raise serializers.ValidationError("Ya existe un cliente con este usuario.")
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
            
            if Customer.objects.filter(document_number=value).exists():
                raise serializers.ValidationError("Ya existe un cliente con este número de documento.")
        
        return value

    def validate_person_type(self, value):
        """
        Validar que el tipo de persona pertenezca a la categoría con id_types_categories = 14.
        """
        try:
            category = TypesCategory.objects.get(id_types_categories=14)
            category_name = category.name
        except TypesCategory.DoesNotExist:
            raise serializers.ValidationError("La categoría de tipos de persona no está configurada correctamente.")
        
        if value.id_types_categories_id != 14:
            raise serializers.ValidationError(
                f"El tipo de persona debe pertenecer a la categoría '{category_name}'."
            )
        return value

    def validate(self, data):
        """
        Validaciones personalizadas.
        """
        request = self.context.get('request')
        id_user = data.get('id_user')
        document_number = data.get('document_number')
        
        # Si se proporciona id_user, no validar ni usar document_number
        if id_user is not None:
            # Eliminar document_number si está presente para que no se guarde
            if 'document_number' in data:
                del data['document_number']
            return data
            
        # Si no se proporciona id_user, validar que se haya proporcionado el document_number
        if not document_number:
            raise serializers.ValidationError({
                'document_number': 'Se requiere el número de documento cuando no se proporciona un id_user.'
            })
        
        # 2. Si no hay id_user, validar el documento en servicio externo
        document_number = data.get('document_number')
        if document_number:
            try:
                # Obtener el token del usuario autenticado
                request = self.context.get('request')
                if request and hasattr(request, 'user'):
                    auth_header = request.META.get('HTTP_AUTHORIZATION')
                    if not auth_header and hasattr(request, 'headers'):
                        auth_header = request.headers.get('Authorization')
                    
                    headers = {}
                    if auth_header:
                        headers['Authorization'] = auth_header
                    
                    try:
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
                                # Obtener la instancia de User usando el ID del servicio externo
                                from users.models.user import User
                                try:
                                    user_instance = User.objects.get(id_user=user_data['id'])
                                    # Si encontramos el usuario en el servicio externo
                                    # Mantenemos solo id_user y person_type
                                    return {
                                        'id_user': user_instance,
                                        'person_type': data.get('person_type')  # Mantener el person_type del request
                                    }
                                except User.DoesNotExist:
                                    logger.warning(f"Usuario con id {user_data['id']} no encontrado en la base de datos local")
                                    # Si el usuario no existe localmente, continuamos con el flujo normal
                                    return data
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"Error al verificar documento en servicio externo: {str(e)}")
                        # Si hay error en la conexión, continuamos con el flujo normal
                        pass
                
            except Exception as e:
                logger.error(f"Error inesperado al validar documento: {str(e)}")
                # Si hay error inesperado, continuamos con el flujo normal
                pass
        
        # 3. Si llegamos aquí, devolvemos los datos originales
        return data

    def create(self, validated_data):
        """
        Crea un nuevo cliente con los datos validados.
        """
        from users.models.user import User  # Importar aquí para evitar importaciones circulares
        
        # Obtener el usuario autenticado
        request = self.context['request']
        user = request.user
        
        # Obtener la instancia real de User de la base de datos
        try:
            if hasattr(user, 'id_user'):
                db_user = User.objects.get(id_user=user.id_user)
            else:
                db_user = User.objects.get(pk=user.id)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'user': 'El usuario autenticado no existe en la base de datos.'
            })
        
        # Determinar qué campos vamos a guardar basado en los datos validados
        if 'id_user' in validated_data:
            # Caso 1: Se proporcionó id_user, solo guardamos id_user y person_type
            customer_data = {
                'id_user': validated_data['id_user'],
                'person_type': validated_data.get('person_type'),
                'customer_statues_id': 1,  # Estado activo por defecto
                'id_responsible_user': db_user  # Usuario responsable
            }
            
            # Si se proporcionó document_number, también lo guardamos
            if 'document_number' in validated_data:
                customer_data['document_number'] = validated_data['document_number']
        else:
            # Si no se proporcionó id_user, usamos todos los datos validados
            customer_data = validated_data.copy()
            customer_data.update({
                'customer_statues_id': 1,  # Estado activo por defecto
                'id_responsible_user': db_user  # Usuario responsable
            })
        
        # Crear el cliente
        return Customer.objects.create(**customer_data)
