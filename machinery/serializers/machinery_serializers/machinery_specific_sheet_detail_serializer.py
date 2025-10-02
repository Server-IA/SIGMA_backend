from rest_framework import serializers
from machinery.models.specific_technical_sheet import SpecificTechnicalSheet
from parameterization.models.units import Units
from parameterization.models.types import Types

class SpecificTechnicalSheetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving detailed information of a specific technical sheet.
    Includes all fields from the model with related fields expanded and their names.
    """
    
    # Helper method to get unit name
    def get_unit_name(self, obj, field_name):
        unit_id = getattr(obj, f'{field_name}_id', None)
        if not unit_id:
            return None
        try:
            return Units.objects.get(pk=unit_id).name
        except Units.DoesNotExist:
            return None
    
    # Helper method to get type name
    def get_type_name(self, obj, field_name):
        type_id = getattr(obj, f'{field_name}_id', None)
        if not type_id:
            return None
        try:
            return Types.objects.get(pk=type_id).name
        except Types.DoesNotExist:
            return None
    
    # Motor y transmisión
    power_unit = serializers.IntegerField(source='power_unit_id', read_only=True)
    power_unit_name = serializers.SerializerMethodField()
    engine_type = serializers.IntegerField(source='engine_type_id', read_only=True)
    engine_type_name = serializers.SerializerMethodField()
    cylinder_capacity_unit = serializers.IntegerField(source='cylinder_capacity_unit_id', read_only=True)
    cylinder_capacity_unit_name = serializers.SerializerMethodField()
    cylinder_arrangement_type = serializers.IntegerField(source='cylinder_arrangement_type_id', read_only=True)
    cylinder_arrangement_type_name = serializers.SerializerMethodField()
    traction_type = serializers.IntegerField(source='traction_type_id', read_only=True, allow_null=True)
    traction_type_name = serializers.SerializerMethodField()
    fuel_consumption_unit = serializers.IntegerField(source='fuel_consumption_unit_id', read_only=True)
    fuel_consumption_unit_name = serializers.SerializerMethodField()
    transmission_system_type = serializers.IntegerField(source='transmission_system_type_id', read_only=True)
    transmission_system_type_name = serializers.SerializerMethodField()
    
    # Capacidad y rendimiento
    fuel_capacity_unit = serializers.IntegerField(source='fuel_capacity_unit_id', read_only=True, allow_null=True)
    fuel_capacity_unit_name = serializers.SerializerMethodField()
    carrying_capacity_unit = serializers.IntegerField(source='carrying_capacity_unit_id', read_only=True, allow_null=True)
    carrying_capacity_unit_name = serializers.SerializerMethodField()
    operating_weight_unit = serializers.IntegerField(source='operating_weight_unit_id', read_only=True)
    operating_weight_unit_name = serializers.SerializerMethodField()
    max_speed_unit = serializers.IntegerField(source='max_speed_unit_id', read_only=True)
    max_speed_unit_name = serializers.SerializerMethodField()
    draft_force_unit = serializers.IntegerField(source='draft_force_unit_id', read_only=True, allow_null=True)
    draft_force_unit_name = serializers.SerializerMethodField()
    maximum_altitude_unit = serializers.IntegerField(source='maximum_altitude_unit_id', read_only=True, allow_null=True)
    maximum_altitude_unit_name = serializers.SerializerMethodField()
    performance_unit = serializers.IntegerField(source='performance_unit_id', read_only=True, allow_null=True)
    performance_unit_name = serializers.SerializerMethodField()
    
    # Dimensiones y peso
    dimension_unit = serializers.IntegerField(source='dimension_unit_id', read_only=True)
    dimension_unit_name = serializers.SerializerMethodField()
    net_weight_unit = serializers.IntegerField(source='net_weight_unit_id', read_only=True)
    net_weight_unit_name = serializers.SerializerMethodField()
    
    # Sistemas auxiliares e hidráulicos
    air_conditioning_system_type = serializers.IntegerField(source='air_conditioning_system_type_id', read_only=True, allow_null=True)
    air_conditioning_system_type_name = serializers.SerializerMethodField()
    air_conditioning_system_consumption_unit = serializers.IntegerField(source='air_conditioning_system_consumption_unit_id', read_only=True, allow_null=True)
    air_conditioning_system_consumption_unit_name = serializers.SerializerMethodField()
    maximum_working_pressure_unit = serializers.IntegerField(source='maximum_working_pressure_unit_id', read_only=True, allow_null=True)
    maximum_working_pressure_unit_name = serializers.SerializerMethodField()
    pump_flow_unit = serializers.IntegerField(source='pump_flow_unit_id', read_only=True, allow_null=True)
    pump_flow_unit_name = serializers.SerializerMethodField()
    hydraulic_tank_capacity_unit = serializers.IntegerField(source='hydraulic_tank_capacity_unit_id', read_only=True, allow_null=True)
    hydraulic_tank_capacity_unit_name = serializers.SerializerMethodField()
    
    # Normatividad y seguridad
    emission_level_type = serializers.IntegerField(source='emission_level_type_id', read_only=True, allow_null=True)
    emission_level_type_name = serializers.SerializerMethodField()
    cabin_type = serializers.IntegerField(source='cabin_type_id', read_only=True, allow_null=True)
    cabin_type_name = serializers.SerializerMethodField()
    
    # Métodos para obtener nombres de unidades
    def get_power_unit_name(self, obj): return self.get_unit_name(obj, 'power_unit')
    def get_cylinder_capacity_unit_name(self, obj): return self.get_unit_name(obj, 'cylinder_capacity_unit')
    def get_fuel_consumption_unit_name(self, obj): return self.get_unit_name(obj, 'fuel_consumption_unit')
    def get_fuel_capacity_unit_name(self, obj): return self.get_unit_name(obj, 'fuel_capacity_unit')
    def get_carrying_capacity_unit_name(self, obj): return self.get_unit_name(obj, 'carrying_capacity_unit')
    def get_operating_weight_unit_name(self, obj): return self.get_unit_name(obj, 'operating_weight_unit')
    def get_max_speed_unit_name(self, obj): return self.get_unit_name(obj, 'max_speed_unit')
    def get_draft_force_unit_name(self, obj): return self.get_unit_name(obj, 'draft_force_unit')
    def get_maximum_altitude_unit_name(self, obj): return self.get_unit_name(obj, 'maximum_altitude_unit')
    def get_performance_unit_name(self, obj): return self.get_unit_name(obj, 'performance_unit')
    def get_dimension_unit_name(self, obj): return self.get_unit_name(obj, 'dimension_unit')
    def get_net_weight_unit_name(self, obj): return self.get_unit_name(obj, 'net_weight_unit')
    def get_air_conditioning_system_consumption_unit_name(self, obj): return self.get_unit_name(obj, 'air_conditioning_system_consumption_unit')
    def get_maximum_working_pressure_unit_name(self, obj): return self.get_unit_name(obj, 'maximum_working_pressure_unit')
    def get_pump_flow_unit_name(self, obj): return self.get_unit_name(obj, 'pump_flow_unit')
    def get_hydraulic_tank_capacity_unit_name(self, obj): return self.get_unit_name(obj, 'hydraulic_tank_capacity_unit')
    
    # Métodos para obtener nombres de tipos
    def get_engine_type_name(self, obj): return self.get_type_name(obj, 'engine_type')
    def get_cylinder_arrangement_type_name(self, obj): return self.get_type_name(obj, 'cylinder_arrangement_type')
    def get_traction_type_name(self, obj): return self.get_type_name(obj, 'traction_type')
    def get_transmission_system_type_name(self, obj): return self.get_type_name(obj, 'transmission_system_type')
    def get_air_conditioning_system_type_name(self, obj): return self.get_type_name(obj, 'air_conditioning_system_type')
    def get_emission_level_type_name(self, obj): return self.get_type_name(obj, 'emission_level_type')
    def get_cabin_type_name(self, obj): return self.get_type_name(obj, 'cabin_type')
    
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
            'power', 'power_unit', 'power_unit_name', 'engine_type', 'engine_type_name', 
            'cylinder_capacity', 'cylinder_capacity_unit', 'cylinder_capacity_unit_name',
            'cylinder_arrangement_type', 'cylinder_arrangement_type_name', 'cylinder_count', 
            'traction_type', 'traction_type_name', 'fuel_consumption',
            'fuel_consumption_unit', 'fuel_consumption_unit_name', 'transmission_system_type',
            'transmission_system_type_name',
            
            # Capacidad y rendimiento
            'fuel_capacity', 'fuel_capacity_unit', 'fuel_capacity_unit_name', 
            'carrying_capacity', 'carrying_capacity_unit', 'carrying_capacity_unit_name',
            'operating_weight', 'operating_weight_unit', 'operating_weight_unit_name',
            'max_speed', 'max_speed_unit', 'max_speed_unit_name',
            'draft_force', 'draft_force_unit', 'draft_force_unit_name', 
            'maximum_altitude', 'maximum_altitude_unit', 'maximum_altitude_unit_name',
            'minimum_performance', 'maximum_performance', 'performance_unit', 'performance_unit_name',
            
            # Dimensiones y peso
            'width', 'length', 'height', 
            'dimension_unit', 'dimension_unit_name', 
            'net_weight', 'net_weight_unit', 'net_weight_unit_name',
            
            # Sistemas auxiliares e hidráulicos
            'air_conditioning_system_type', 'air_conditioning_system_type_name',
            'air_conditioning_system_consumption',
            'air_conditioning_system_consumption_unit', 'air_conditioning_system_consumption_unit_name',
            'maximum_working_pressure',
            'maximum_working_pressure_unit', 'maximum_working_pressure_unit_name', 
            'pump_flow', 'pump_flow_unit', 'pump_flow_unit_name',
            'hydraulic_tank_capacity', 'hydraulic_tank_capacity_unit', 'hydraulic_tank_capacity_unit_name',
            
            # Normatividad y seguridad
            'emission_level_type', 'emission_level_type_name', 
            'cabin_type', 'cabin_type_name',
            
            # Relación con la máquina
            'id_machinery',
            
            # Fechas
            'registration_date', 'modification_date',
            
            # Usuario responsable y justificación
            'id_responsible_user', 'justification'
        ]
