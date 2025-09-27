from rest_framework import serializers
from machinery.models.machinery_tracker_sheet import MachineryTrackerSheet


class MachineryTrackerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar únicamente la información de Tracker de la maquinaria.
    """

    class Meta:
        model = MachineryTrackerSheet
        fields = [
            'id_tracker_sheet',
            'terminal_serial_number',
            'gps_serial_number',
            'chassis_number',
            'engine_number'
        ]
