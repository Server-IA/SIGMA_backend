from django.db import models

class Machinery(models.Model):
    id_machinery = models.AutoField(primary_key=True)
    machinery_name = models.CharField(max_length=255, null=False, blank=False)
    manufacturing_year = models.IntegerField(null=True, blank=True)
    serial_number = models.CharField(max_length=50, null=False, blank=False)
    machinery_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=False, blank=False, related_name='machinery_type')
    id_model = models.ForeignKey('parameterization.Models', on_delete=models.PROTECT, null=False, blank=False)
    tariff_subheading = models.CharField(max_length=50, null=True, blank=True)
    machinery_secondary_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null = False, blank = False, related_name='machinery_secondary_type')
    id_city = models.IntegerField(null=True, blank=True)
    image_path = models.CharField(max_length=255, null=True, blank=True)
    id_device = models.ForeignKey('machinery.TelemetryDevices', on_delete=models.PROTECT, null=True, blank=True)
    registration_date = models.DateField(auto_now=True)
    modification_date = models.DateField(auto_now=True)
    machinery_operational_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT,)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)

    class Meta:
        db_table = 'machinery'