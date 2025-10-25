from rest_framework import serializers
from machinery.models.telemetry_devices import TelemetryDevices

class TelemetryDevicesDetailedSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='id_statues.name', read_only=True)
    status_id = serializers.IntegerField(source='id_statues.id_statues', read_only=True)
    id_device = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = TelemetryDevices
        fields = [
            'id_device',
            'name',
            'IMEI',
            'registration_date',
            'status_id',
            'status_name',
        ]
        read_only_fields = fields
