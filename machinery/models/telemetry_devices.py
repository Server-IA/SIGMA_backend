from django.db import models

class TelemetryDevices(models.Model):
    id_device = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=False, blank=False)
    IMEI = models.BigIntegerField(null=False, blank=False)
    id_statues = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)
    registration_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)

    class Meta:
        db_table = 'telemetry_devices'