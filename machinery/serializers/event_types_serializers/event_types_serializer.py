from rest_framework import serializers
from machinery.models.event_types import EventTypes

class EventTypesSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo EventTypes.
    Incluye todos los campos: id_event_type, name
    """
    class Meta:
        model = EventTypes
        fields = ['id_event_type', 'name']
