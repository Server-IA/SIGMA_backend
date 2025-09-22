from rest_framework import serializers
from users.models.user import User
from machinery.models import Machinery, MachineryUsageSheet
from parameterization.models import Types, Units


class MachineryUsageSheetCreateSerializer(serializers.ModelSerializer):
    id_machinery = serializers.PrimaryKeyRelatedField(queryset=Machinery.objects.all(), required=True)
    usage_condition = serializers.PrimaryKeyRelatedField(queryset=Types.objects.all(), required=True)
    tenancy_type = serializers.PrimaryKeyRelatedField(queryset=Types.objects.all(), required=False, allow_null=True)
    distance_unit = serializers.PrimaryKeyRelatedField(queryset=Units.objects.all(), required=True)
    responsible_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True, source='id_responsible_user')

    class Meta:
        model = MachineryUsageSheet
        fields = [
            'id_machinery',
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

    def validate(self, data):
        tenancy = data.get('tenancy_type')
        contract_end = data.get('contract_end_date')
        if tenancy and getattr(tenancy, 'name', '').strip().lower() != 'propia':
            if not contract_end:
                raise serializers.ValidationError({
                    'contract_end_date': "La fecha fin de contrato es obligatoria si la tenencia no es 'propia'."
                })
        return data

    def create(self, validated_data):
        machinery = validated_data['id_machinery']
        if MachineryUsageSheet.objects.filter(id_machinery=machinery).exists():
            raise serializers.ValidationError({"id_machinery": "Esta maquinaria ya tiene una ficha de uso registrada."})
        return MachineryUsageSheet.objects.create(**validated_data)


