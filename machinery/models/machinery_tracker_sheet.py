from django.db import models

class MachineryTrackerSheet(models.Model):
    id_tracker_sheet = models.AutoField(primary_key=True)
    id_machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, null=False, blank=False)
    terminal_serial_number = models.CharField(max_length=100, null=False, blank=False)
    gps_serial_number = models.CharField(max_length=100, null=True, blank=True)
    chassis_number = models.CharField(max_length=100, null=True, blank=True)
    engine_number = models.CharField(max_length=100, null=True, blank=True)
    registration_date = models.DateField(auto_now=True)
    modification_date = models.DateField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)
    justification = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'machinery_tracker_sheet'
