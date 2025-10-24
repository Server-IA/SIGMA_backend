from django.db import models

class OBDFaultMachinery(models.Model):
    id = models.AutoField(primary_key=True)
    id_obd_fault = models.ForeignKey('machinery.OBD_Faults', on_delete=models.PROTECT, null=False, blank=False, db_column='id_obd_fault')
    id_machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, null=False, blank=False, db_column='id_machinery')
    alert_enabled = models.BooleanField(null=False, blank=False)
    id_maintenance = models.ForeignKey('maintenance.Maintenance', on_delete=models.PROTECT, null=True, blank=True, db_column='id_maintenance')

    class Meta:
        db_table = 'obd_fault_machinery'