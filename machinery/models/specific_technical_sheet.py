from django.db import models
from machinery.models import Machinery

class SpecificTechnicalSheet(models.Model):
    id_specific_technical_sheet = models.AutoField(primary_key=True)

    # Motor y transmisión
    power = models.FloatField(null=False, blank=False)
    power_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='power_unit')
    engine_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=False, blank=False, related_name='engine_type')
    cylinder_capacity = models.FloatField(null=False, blank=False)
    cylinder_capacity_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='cylinder_capacity_unit')
    cylinder_arrangement_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=False, blank=False, related_name='cylinder_arrangement_type')
    cylinder_count = models.IntegerField(null=False, blank=False)
    traction_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=True, blank=True, related_name='traction_type')
    fuel_consumption = models.FloatField(null=False, blank=False)
    fuel_consumption_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='fuel_consumption_unit')
    transmission_system_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=False, blank=False, related_name='transmission_system_type')

    # Capacidad y rendimiento
    fuel_capacity = models.FloatField(null=True, blank=True)
    fuel_capacity_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='fuel_capacity_unit')
    carrying_capacity = models.FloatField(null=True, blank=True)
    carrying_capacity_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='carrying_capacity_unit')
    operating_weight = models.CharField(max_length=255, null=False, blank=False)
    operating_weight_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='operating_weight_unit')
    max_speed = models.FloatField(null=False, blank=False)
    max_speed_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='max_speed_unit')
    draft_force = models.FloatField(null=True, blank=True)
    draft_force_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='draft_force_unit')
    maximum_altitude = models.FloatField(null=True, blank=True)
    maximum_altitude_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='maximum_altitude_unit')
    minimum_performance = models.IntegerField(null=True, blank=True)
    maximum_performance = models.IntegerField(null=True, blank=True)
    performance_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='performance_unit')

    # Dimensiones y peso
    width = models.FloatField(null=False, blank=False)
    length = models.FloatField(null=False, blank=False)
    height = models.FloatField(null=False, blank=False)
    dimension_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='dimension_unit')
    net_weight = models.FloatField(null=False, blank=False)
    net_weight_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='net_weight_unit')

    # Sistemas auxiliares e hidráulicos
    air_conditioning_system_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=True, blank=True, related_name='air_conditioning_system_type')
    air_conditioning_system_consumption = models.FloatField(null=True, blank=True)
    air_conditioning_system_consumption_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='air_conditioning_system_consumption_unit')
    maximum_working_pressure = models.FloatField(null=True, blank=True)
    maximum_working_pressure_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='maximum_working_pressure_unit')
    pump_flow = models.FloatField(null=True, blank=True)
    pump_flow_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='pump_flow_unit')
    hydraulic_tank_capacity = models.FloatField(null=True, blank=True)
    hydraulic_tank_capacity_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='hydraulic_tank_capacity_unit')

    # Normatividad y seguridad
    emission_level_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=True, blank=True, related_name='emission_level_type')
    cabin_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=True, blank=True, related_name='cabin_type')

    # Relación con la máquina (una por máquina)
    id_machinery = models.OneToOneField(Machinery, on_delete=models.PROTECT, unique=True)

    #fecha y usuario responsable
    registration_date = models.DateField(auto_now=True)
    modification_date = models.DateField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)

    class Meta:
        db_table = 'specific_technical_sheets'
