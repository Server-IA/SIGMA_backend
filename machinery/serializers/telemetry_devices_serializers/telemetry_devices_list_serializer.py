from rest_framework import serializers
from machinery.models.telemetry_devices import TelemetryDevices

class TelemetryDevicesListSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='id_statues.name', read_only=True)
    status_id = serializers.IntegerField(source='id_statues.id_status', read_only=True)
    
    class Meta:
        model = TelemetryDevices
        fields = [
            'id_device',
            'name',
            'status_id',
            'status',
        ]
        read_only_fields = fields
