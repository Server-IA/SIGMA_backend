from django.db import models

class OBD_Faults(models.Model):
    id_obd_fault = models.AutoField(primary_key=True)
    code = models.CharField(max_length=20, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'obd_faults'