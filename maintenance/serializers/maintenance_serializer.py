from rest_framework import serializers
from maintenance.models import Maintenance

class MaintenanceSerializer(serializers.ModelSerializer):
    # Exponer el ID del responsable como entero
    id_responsible_user = serializers.IntegerField(source='id_responsible_user_id', read_only=True)

    class Meta:
        model = Maintenance
        fields = [
            'id_maintenance',
            'name',
            'description',
            'maintenance_type',
            'maintenance_status',
            'id_responsible_user',
            'registration_date',
            'modification_date',
        ]
        read_only_fields = ('id_maintenance', 'id_responsible_user', 'registration_date', 'modification_date')