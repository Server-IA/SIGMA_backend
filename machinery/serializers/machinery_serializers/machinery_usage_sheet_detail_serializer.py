from rest_framework import serializers

from machinery.models import MachineryUsageSheet


class MachineryUsageSheetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para exponer el detalle de Uso (HU-MAQ-009).
    Incluye una lista de campos faltantes para que el frontend lo muestre sin errores.
    """

    class Meta:
        model = MachineryUsageSheet
        fields = [
            'id_usage_sheet',
            'id_machinery',
            'acquisition_date',
            'usage_condition',
            'usage_hours',
            'distance_value',
            'distance_unit',
            'tenancy_type',
            'is_own',
            'contract_end_date',
            'modification_date',
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        usage_condition = instance.usage_condition
        distance_unit = instance.distance_unit
        tenancy_type = instance.tenancy_type

        data = {
            'id_usage_sheet': instance.id_usage_sheet,
            'id_machinery': instance.id_machinery_id,
            'acquisition_date': instance.acquisition_date,
            'usage_condition': None if not usage_condition else {
                'id': getattr(usage_condition, 'id_statues', None),
                'name': getattr(usage_condition, 'name', None),
            },
            'usage_hours': instance.usage_hours,
            'distance': {
                'value': instance.distance_value,
                'unit': None if not distance_unit else {
                    'id': getattr(distance_unit, 'id_units', None),
                    'name': getattr(distance_unit, 'name', None),
                    'symbol': getattr(distance_unit, 'symbol', None),
                }
            },
            'tenancy_type': None if not tenancy_type else {
                'id': getattr(tenancy_type, 'id_types', None),
                'name': getattr(tenancy_type, 'name', None),
            },
            'is_own': instance.is_own,
            'contract_end_date': instance.contract_end_date,
            'last_modified': instance.modification_date,
        }

        missing_fields = []
        if data['acquisition_date'] in (None, ''):
            missing_fields.append('acquisition_date')
        if data['usage_condition'] is None:
            missing_fields.append('usage_condition')
        if data['usage_hours'] in (None, ''):
            missing_fields.append('usage_hours')
        if data['distance']['value'] in (None, ''):
            missing_fields.append('distance_value')
        if data['distance']['unit'] is None:
            missing_fields.append('distance_unit')
        if data['is_own'] is False:
            if data['tenancy_type'] is None:
                missing_fields.append('tenancy_type')
            if data['contract_end_date'] in (None, ''):
                missing_fields.append('contract_end_date')

        data['missing_fields'] = missing_fields
        return data


