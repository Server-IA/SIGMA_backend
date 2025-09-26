from rest_framework import serializers
from machinery.models.machinery import Machinery

class MachineryDetailSerializer(serializers.ModelSerializer):
    machinery_type = serializers.PrimaryKeyRelatedField(read_only=True)
    machinery_secondary_type = serializers.PrimaryKeyRelatedField(read_only=True)
    machinery_operational_status = serializers.PrimaryKeyRelatedField(read_only=True)
    id_model = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    id_device = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Machinery
        fields = [
            'machinery_name',
            'manufacturing_year',
            'serial_number',
            'machinery_type',
            'id_model',
            'tariff_subheading',
            'machinery_secondary_type',
            'id_city',
            'image_path',
            'id_device',
            'justification',
            'machinery_operational_status'
        ]