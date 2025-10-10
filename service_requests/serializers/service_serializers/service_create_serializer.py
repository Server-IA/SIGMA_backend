from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from service_requests.models.services import Service
from parameterization.models import Types, Statues, Units
from users.models.user import User

class ServiceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para la creación de servicios.
    Campos obligatorios: service_name, service_type, base_price, price_unit, applicable_tax, service_status
    """
    responsible_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='id_responsible_user',
        required=False
    )

    service_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        required=True
    )

    price_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(),
        required=True
    )

    class Meta:
        model = Service
        fields = [
            'service_name',
            'description',
            'service_type',
            'base_price',
            'price_unit',
            'applicable_tax',
            'tax_rate',
            'is_vat_exempt',
            'service_status',
            'responsible_user',
        ]
        extra_kwargs = {
            'service_name': {'required': True},
            'base_price': {'required': True},
            'applicable_tax': {'required': True},
            'service_status': {'required': False},
            'is_vat_exempt': {'required': False},
            'tax_rate': {'required': False},
            'description': {'required': False}
        }

    def validate_service_name(self, value):
        """
        Valida que el nombre del servicio sea único.
        """
        # Verificar si ya existe un servicio con el mismo nombre (case-insensitive)
        if Service.objects.filter(service_name__iexact=value).exists():
            raise serializers.ValidationError({
                'service_name': 'Ya existe un servicio con este nombre.'
            })
        return value

    def validate_service_type(self, value):
        """
        Valida que el tipo de servicio pertenezca a la categoría con id 14.
        """
        if not value.id_types_categories or value.id_types_categories.id_types_categories != 14:
            from parameterization.models import TypesCategory
            try:
                expected_category = TypesCategory.objects.get(id_types_categories=14)
                error_msg = (
                    f"El tipo de servicio debe pertenecer a la categoría '{expected_category.name}'. "
                    f"Tipo recibido: {value.name if value else 'Ninguno'}"
                )
            except TypesCategory.DoesNotExist:
                error_msg = "El tipo de servicio debe pertenecer a la categoría con ID 14"
                
            raise serializers.ValidationError({
                'service_type': error_msg
            })
        return value

    def validate_price_unit(self, value):
        """
        Valida que la unidad de precio pertenezca a la categoría con id 10.
        """
        if not value.id_units_categories or value.id_units_categories.id_units_categories != 10:
            from parameterization.models import UnitsCategory
            try:
                expected_category = UnitsCategory.objects.get(id_units_categories=10)
                raise serializers.ValidationError(
                    f"La unidad de precio debe pertenecer a la categoría '{expected_category.name}' (ID: 10)."
                )
            except UnitsCategory.DoesNotExist:
                raise serializers.ValidationError("Categoría de unidad de precio no encontrada")
        return value

    def validate_base_price(self, value):
        """
        Valida que el precio base sea mayor a 0.
        """
        if value <= 0:
            raise serializers.ValidationError({
                'base_price': 'El precio base debe ser mayor a 0'
            })
        return value

    def create(self, validated_data):
        """
        Crea un nuevo servicio con el estado por defecto 1 (Activo)
        y el usuario responsable del contexto de la petición.
        """
        # Obtener el estado con id 1 (Activo)
        try:
            status = Statues.objects.get(id_statues=1)
        except Statues.DoesNotExist:
            raise serializers.ValidationError({
                'service_status': 'No se encontró el estado por defecto para el servicio'
            })
            
        # Obtener el usuario del request
        request_user = self.context['request'].user
        
        # Si el usuario es un JWTUser, obtener el ID del usuario
        if hasattr(request_user, 'id'):
            user_id = request_user.id
            try:
                user = User.objects.get(id_user=user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'non_field_errors': ['El usuario autenticado no existe en la base de datos']
                })
        else:
            user = request_user
            
        # Establecer el estado por defecto y el usuario responsable
        validated_data['service_status'] = status
        validated_data['id_responsible_user'] = user
        
        # Crear el servicio
        return super().create(validated_data)
