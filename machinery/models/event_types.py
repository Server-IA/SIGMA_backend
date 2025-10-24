from django.db import models

class EventTypes(models.Model):
    id_event_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=False, blank=False)

    class Meta:
        db_table = 'event_types'
