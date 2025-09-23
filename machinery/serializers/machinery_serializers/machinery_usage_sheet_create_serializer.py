from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from users.models.user import User
from machinery.models import Machinery, MachineryUsageSheet
from parameterization.models import Types, Units, Statues, TypesCategory, StatuesCategory, UnitsCategory


class MachineryUsageSheetCreateSerializer(serializers.ModelSerializer):
    id_machinery = serializers.PrimaryKeyRelatedField(queryset=Machinery.objects.all(), required=True)
    usage_condition = serializers.PrimaryKeyRelatedField(queryset=Statues.objects.all(), required=True)
    tenancy_type = serializers.PrimaryKeyRelatedField(queryset=Types.objects.all(), required=False, allow_null=True)
    distance_unit = serializers.PrimaryKeyRelatedField(queryset=Units.objects.all(), required=True)
    responsible_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='id_responsible_user')

    class Meta:
        model = MachineryUsageSheet
        fields = [
            'id_machinery',
            'is_own',
            'acquisition_date',
            'usage_condition',
            'usage_hours',
            'distance_value',
            'distance_unit',
            'tenancy_type',
            'contract_end_date',
            'responsible_user',
        ]
        extra_kwargs = {
            'acquisition_date': {'required': True},
            'usage_condition': {'required': True},
            'usage_hours': {'required': True},
            'distance_value': {'required': True},
            'distance_unit': {'required': True},
            'is_own': {'required': False, 'default': False},
        }

    def validate_usage_hours(self, value):
        if value is None:
            raise serializers.ValidationError("Las horas de uso son obligatorias.")
        if value < 0:
            raise serializers.ValidationError("Las horas de uso no pueden ser negativas.")
        return value

    def validate_distance_value(self, value):
        if value is None:
            raise serializers.ValidationError("La distancia recorrida es obligatoria.")
        if value < 0:
            raise serializers.ValidationError("La distancia recorrida no puede ser negativa.")
        return value

    def validate_usage_condition(self, value):
        """
        Validar que el estado de uso pertenezca a la categoría con id 3
        """
        if value.id_statues_categories_id != 3:
            expected_category = StatuesCategory.objects.get(id_statues_categories=3)
            raise ValidationError(
                f"El estado de uso debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def validate_distance_unit(self, value):
        """
        Validar que la unidad de distancia pertenezca a la categoría con id 7
        """
        if value.id_units_categories_id != 7:
            expected_category = UnitsCategory.objects.get(id_units_categories=7)
            raise ValidationError(
                f"La unidad de distancia debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def validate_tenancy_type(self, value):
        """
        Validar que el tipo de tenencia pertenezca a la categoría con id 11
        """
        if value and value.id_types_categories_id != 11:
            expected_category = TypesCategory.objects.get(id_types_categories=11)
            raise ValidationError(
                f"El tipo de tenencia debe pertenecer a la categoría '{expected_category.name}'."
            )
        return value

    def to_internal_value(self, data):
        """
        Maneja la conversión de datos de entrada antes de la validación
        """
        # Hacer una copia mutable de los datos
        data = data.copy()
        
        # Convertir is_own a booleano
        is_own = data.get('is_own', False)
        if isinstance(is_own, str):
            is_own = is_own.lower() in ('true', '1')
        data['is_own'] = is_own  # Actualizar el valor en los datos
        
        # Limpiar campos opcionales cuando is_own es true
        if is_own:
            if 'contract_end_date' in data and data['contract_end_date'] == '':
                data['contract_end_date'] = None
            if 'tenancy_type' in data and data['tenancy_type'] == '':
                data['tenancy_type'] = None
        
        # Procesar los datos con el método padre
        return super().to_internal_value(data)

    def validate(self, data):
        """
        Validaciones generales del serializer
        """
        is_own = data.get('is_own', False)
        
        # Si la maquinaria es propia, eliminamos los campos tenancy_type y contract_end_date
        if is_own:
            if 'tenancy_type' in data:
                data.pop('tenancy_type', None)
            if 'contract_end_date' in data:
                data.pop('contract_end_date', None)
        # Si no es propia, validamos que los campos requeridos estén presentes
        else:
            # Validar tenancy_type
            if 'tenancy_type' not in data or data['tenancy_type'] is None or data['tenancy_type'] == '':
                raise ValidationError({
                    'tenancy_type': "El tipo de tenencia es obligatorio cuando la maquinaria no es propia."
                })
            
            # Validar contract_end_date
            if 'contract_end_date' not in data or data['contract_end_date'] is None or data['contract_end_date'] == '':
                raise ValidationError({
                    'contract_end_date': "La fecha fin de contrato es obligatoria cuando la maquinaria no es propia."
                })
            
            # Validar formato de fecha si se proporciona
            if 'contract_end_date' in data and data['contract_end_date']:
                try:
                    from datetime import datetime
                    if isinstance(data['contract_end_date'], str):
                        datetime.strptime(data['contract_end_date'], '%Y-%m-%d')
                except ValueError:
                    raise ValidationError({
                        'contract_end_date': 'Formato de fecha inválido. Use el formato YYYY-MM-DD.'
                    })
        
        return data

    def create(self, validated_data):
        machinery = validated_data['id_machinery']
        if MachineryUsageSheet.objects.filter(id_machinery=machinery).exists():
            raise serializers.ValidationError({"id_machinery": "Esta maquinaria ya tiene una ficha de uso registrada."})
        return MachineryUsageSheet.objects.create(**validated_data)
