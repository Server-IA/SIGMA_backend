from django.db import models

class EventTypeMachinery(models.Model):
    id = models.AutoField(primary_key=True)
    id_event_type = models.ForeignKey('machinery.EventTypes', on_delete=models.PROTECT, null=False, blank=False, db_column='id_event_type')
    id_machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, null=False, blank=False, db_column='id_machinery')
    id_maintenance = models.ForeignKey('maintenance.Maintenance', on_delete=models.PROTECT, null=True, blank=True, db_column='id_maintenance')
    threshold = models.FloatField(null=True, blank=True)
    alert_enabled = models.BooleanField(null=False, blank=False)

    class Meta:
        db_table = 'event_type_machinery'