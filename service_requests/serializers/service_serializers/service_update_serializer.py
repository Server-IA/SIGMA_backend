from rest_framework import serializers
from django.utils import timezone
import logging

from service_requests.models.services import Service
from parameterization.models import Types, Units

logger = logging.getLogger(__name__)


class ServiceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para la actualización de servicios.
    Todos los campos son opcionales para permitir actualizaciones parciales.
    """
    
    service_type = serializers.PrimaryKeyRelatedField(
        queryset=Types.objects.all(),
        required=False
    )

    price_unit = serializers.PrimaryKeyRelatedField(
        queryset=Units.objects.all(),
        required=False
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
        ]
        extra_kwargs = {
            'service_name': {'required': False},
            'description': {'required': False},
            'service_type': {'required': False},
            'base_price': {'required': False},
            'price_unit': {'required': False},
            'applicable_tax': {'required': False},
            'tax_rate': {'required': False},
            'is_vat_exempt': {'required': False},
        }

    def validate_service_name(self, value):
        """
        Valida que el nombre del servicio sea único, excluyendo la instancia actual.
        """
        if not value or not value.strip():
            raise serializers.ValidationError(
                "El nombre del servicio no puede estar vacío."
            )
        
        # Excluir la instancia actual de la validación
        queryset = Service.objects.filter(service_name__iexact=value.strip())
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError(
                "Ya existe un servicio con este nombre. Por favor, elija un nombre diferente."
            )
        
        return value.strip()

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
                
            raise serializers.ValidationError(
                error_msg
            )
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
            raise serializers.ValidationError(
                'El precio base debe ser mayor a 0'
            )
        return value

    def validate(self, attrs):
        """
        Validaciones a nivel de objeto.
        """
        # Si se proporciona applicable_tax y es True/1, validar que tax_rate esté presente
        applicable_tax = attrs.get('applicable_tax', getattr(self.instance, 'applicable_tax', None))
        tax_rate = attrs.get('tax_rate', getattr(self.instance, 'tax_rate', None))
        
        if applicable_tax and applicable_tax != 0:
            if tax_rate is None or tax_rate <= 0:
                raise serializers.ValidationError({
                    'tax_rate': 'La tasa de impuesto es obligatoria y debe ser mayor a 0 cuando el servicio tiene impuesto aplicable.'
                })
        
        return attrs

    def update(self, instance, validated_data):
        """
        Actualiza un servicio con los datos validados.
        Optimiza la query usando update_fields.
        """
        # Actualizar la fecha de modificación
        instance.modification_date = timezone.now()
        
        # Actualizar solo los campos proporcionados
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Guardar los cambios con update_fields para optimizar la query
        fields_to_update = list(validated_data.keys()) + ['modification_date']
        instance.save(update_fields=fields_to_update)
        
        logger.info(f"Servicio {instance.id_service} actualizado exitosamente")
        
        return instance
