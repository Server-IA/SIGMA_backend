from rest_framework import serializers
from machinery.models.specific_technical_sheet import SpecificTechnicalSheet

class SpecificTechnicalSheetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detailed information of a specific technical sheet.
    Includes all fields from the model with related fields expanded.
    """
    # Motor y transmisión
    power_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    engine_type = serializers.PrimaryKeyRelatedField(read_only=True)
    cylinder_capacity_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    cylinder_arrangement_type = serializers.PrimaryKeyRelatedField(read_only=True)
    traction_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    fuel_consumption_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    transmission_system_type = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Capacidad y rendimiento
    fuel_capacity_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    carrying_capacity_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    operating_weight_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    max_speed_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    draft_force_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    maximum_altitude_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    performance_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    
    # Dimensiones y peso
    dimension_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    net_weight_unit = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Sistemas auxiliares e hidráulicos
    air_conditioning_system_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    air_conditioning_system_consumption_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    maximum_working_pressure_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    pump_flow_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    hydraulic_tank_capacity_unit = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    
    # Normatividad y seguridad
    emission_level_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    cabin_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    
    # Relación con la máquina
    id_machinery = serializers.PrimaryKeyRelatedField(read_only=True)
    
    # Usuario responsable
    id_responsible_user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SpecificTechnicalSheet
        fields = [
            # ID
            'id_specific_technical_sheet',
            
            # Motor y transmisión
            'power', 'power_unit', 'engine_type', 'cylinder_capacity', 'cylinder_capacity_unit',
            'cylinder_arrangement_type', 'cylinder_count', 'traction_type', 'fuel_consumption',
            'fuel_consumption_unit', 'transmission_system_type',
            
            # Capacidad y rendimiento
            'fuel_capacity', 'fuel_capacity_unit', 'carrying_capacity', 'carrying_capacity_unit',
            'operating_weight', 'operating_weight_unit', 'max_speed', 'max_speed_unit',
            'draft_force', 'draft_force_unit', 'maximum_altitude', 'maximum_altitude_unit',
            'minimum_performance', 'maximum_performance', 'performance_unit',
            
            # Dimensiones y peso
            'width', 'length', 'height', 'dimension_unit', 'net_weight', 'net_weight_unit',
            
            # Sistemas auxiliares e hidráulicos
            'air_conditioning_system_type', 'air_conditioning_system_consumption',
            'air_conditioning_system_consumption_unit', 'maximum_working_pressure',
            'maximum_working_pressure_unit', 'pump_flow', 'pump_flow_unit',
            'hydraulic_tank_capacity', 'hydraulic_tank_capacity_unit',
            
            # Normatividad y seguridad
            'emission_level_type', 'cabin_type',
            
            # Relación con la máquina
            'id_machinery',
            
            # Fechas
            'registration_date', 'modification_date',
            
            # Usuario responsable y justificación
            'id_responsible_user', 'justification'
        ]
