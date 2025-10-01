from rest_framework import serializers
from machinery.models.machinery import Machinery

class MachineryListActiveSerializer(serializers.ModelSerializer):
    """
    Serializer para listar máquinas activas con campos específicos.
    """
    class Meta:
        model = Machinery
        fields = ['id_machinery', 'machinery_name', 'serial_number']
        read_only_fields = fields
