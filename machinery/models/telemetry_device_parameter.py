from django.db import models

class TelemetryDeviceParameter(models.Model):
    id = models.AutoField(primary_key=True)
    telemetry_device = models.ForeignKey('machinery.TelemetryDevices', on_delete=models.PROTECT)
    parameter = models.ForeignKey('machinery.Parameters', on_delete=models.PROTECT)

    class Meta:
        db_table = 'telemetry_device_parameter'
        unique_together = ('telemetry_device', 'parameter')
