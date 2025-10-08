from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from service_requests.models.customer import Customer
from parameterization.models import Types, TypesCategory
from django.utils import timezone

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
        Validar que el tipo de persona pertenezca a la categoría con id 14.
        """
        try:
            category = TypesCategory.objects.get(id=14)
            category_name = category.name
        except TypesCategory.DoesNotExist:
            raise serializers.ValidationError("La categoría de tipos de persona no está configurada correctamente.")
        
        if value.type_category_id != 14:
            raise serializers.ValidationError(
                f"El tipo de persona debe pertenecer a la categoría '{category_name}'."
            )
        return value

    def validate(self, data):
        """
        Validaciones personalizadas.
        """
        id_user = data.get('id_user')
        document_number = data.get('document_number')
        
        # Si no se proporciona id_user, validar que se hayan proporcionado los campos requeridos
        if not id_user:
            required_fields = [
                'document_number', 'type_document_id', 'name', 
                'first_last_name', 'email'
            ]
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                raise serializers.ValidationError({
                    field: "Este campo es obligatorio cuando no se proporciona un usuario." 
                    for field in missing_fields
                })
        else:
            # Si se proporciona id_user, ignorar los demás campos
            data = {'id_user': id_user}
            
        return data

    def create(self, validated_data):
        """
        Crea un nuevo cliente con los datos validados.
        """
        # Obtener el usuario autenticado
        user = self.context['request'].user
        
        # Si no se proporcionó id_user, usar el usuario autenticado
        if not validated_data.get('id_user'):
            validated_data['id_user'] = user
        
        # Establecer valores por defecto
        validated_data['customer_statues_id'] = 1  # Estado activo por defecto
        validated_data['id_responsible_user'] = user
        
        # La fecha de creación y modificación se establecen automáticamente en el modelo
        
        return super().create(validated_data)
