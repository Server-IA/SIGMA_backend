from rest_framework import serializers
from machinery.models import (
    ToleranceThresholds,
    OBDFaultMachinery,
    EventTypeMachinery,
    Machinery,
    Parameters,
    OBD_Faults,
    EventTypes
)
from maintenance.models import Maintenance

class ToleranceThresholdsDetailSerializer(serializers.ModelSerializer):
    """Serializer para ToleranceThresholds con detalles del parámetro y mantenimiento"""
    parameter_name = serializers.CharField(source='id_parameter.parameter_name', read_only=True)
    maintenance_name = serializers.CharField(source='id_maintenance.name', read_only=True)

    class Meta:
        model = ToleranceThresholds
        fields = [
            'id', 'id_machinery', 'id_parameter', 'parameter_name',
            'minimum_threshold', 'maximum_threshold',
            'id_maintenance', 'maintenance_name', 'alert_enabled'
        ]

class OBDFaultMachineryDetailSerializer(serializers.ModelSerializer):
    """Serializer para OBDFaultMachinery con detalles del fault y mantenimiento"""
    fault_code = serializers.CharField(source='id_obd_fault.code', read_only=True)
    maintenance_name = serializers.CharField(source='id_maintenance.name', read_only=True)

    class Meta:
        model = OBDFaultMachinery
        fields = [
            'id', 'id_obd_fault', 'fault_code', 'id_machinery',
            'alert_enabled', 'id_maintenance', 'maintenance_name'
        ]

class EventTypeMachineryDetailSerializer(serializers.ModelSerializer):
    """Serializer para EventTypeMachinery con detalles del tipo de evento y mantenimiento"""
    event_name = serializers.CharField(source='id_event_type.name', read_only=True)
    maintenance_name = serializers.CharField(source='id_maintenance.name', read_only=True)

    class Meta:
        model = EventTypeMachinery
        fields = [
            'id', 'id_event_type', 'event_name', 'id_machinery',
            'threshold', 'alert_enabled', 'id_maintenance', 'maintenance_name'
        ]

class MachineryToleranceThresholdsDetailSerializer(serializers.Serializer):
    """
    Serializer para obtener detalles completos de configuraciones de tolerancia por maquinaria.
    Incluye nombres de parámetros, códigos de fallos OBD, nombres de tipos de eventos y nombres de mantenimiento.
    """
    id_machinery = serializers.IntegerField()
    machinery_name = serializers.CharField()

    tolerance_thresholds = ToleranceThresholdsDetailSerializer(many=True)
    obd_fault_machinery = OBDFaultMachineryDetailSerializer(many=True)
    event_type_machinery = EventTypeMachineryDetailSerializer(many=True)
