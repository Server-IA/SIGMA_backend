from django.utils import timezone
from django.db.models import Max
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
            'id_service',
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
            'description': {'required': False},
            'id_service': {'read_only': True}
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

    def generate_service_id(self):
        current_year = timezone.now().year
        # Find the highest service number for the current year
        max_service = Service.objects.filter(
            id_service__startswith=f'SVC-{current_year}'
        ).aggregate(Max('id_service'))

        if max_service['id_service__max']:
            # Extract the number part and increment it
            last_number = int(max_service['id_service__max'].split('-')[-1])
            new_number = last_number + 1
        else:
            # First service of the year
            new_number = 1

        return f'SVC-{current_year}-{new_number:04d}'

    def validate_base_price(self, value):
        """
        Valida que el precio base sea mayor a 0.
        """
        if value <= 0:
            raise serializers.ValidationError({
                'base_price': 'El precio base debe ser mayor a 0'
            })
        return value
    def validate(self, attrs):
        """
        Genera automáticamente el ID del servicio.
        """
        attrs['id_service'] = self.generate_service_id()
        return attrs

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
