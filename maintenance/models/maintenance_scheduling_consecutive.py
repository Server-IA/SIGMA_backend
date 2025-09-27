from django.db import models

class MaintenanceSchedulingConsecutive(models.Model):
    id_maintenance_scheduling_consecutive = models.AutoField(primary_key=True)
    anio = models.IntegerField(null=False, blank=False)
    code = models.IntegerField(unique=True, null=False, blank=False, db_column="code")

    class Meta:
        db_table = "maintenance_scheduling_consecutive"
