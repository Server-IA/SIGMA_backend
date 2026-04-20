from django.db import models

class Data(models.Model):
    id_data = models.AutoField(primary_key=True)
    data = models.FloatField(null=True)
    id_parameter = models.ForeignKey('machinery.Parameters', on_delete=models.PROTECT, db_column='id_parameter', null=False)
    registered_at = models.DateTimeField(null=False)
    id_device = models.ForeignKey('machinery.TelemetryDevices', on_delete=models.PROTECT, db_column='id_device', null=False)
    id_request = models.ForeignKey('service_requests.ServiceRequest', on_delete=models.PROTECT, db_column='id_request', null=False)
    id_machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, db_column='id_machinery', null=False)
    id_user = models.ForeignKey('users.User', on_delete=models.PROTECT, db_column='id_user', null=False)
    obd_fault = models.CharField(max_length=20, null=True, blank=True)
    alert = models.BooleanField(null=False, blank=False)
    class Meta:
        db_table = 'data'
