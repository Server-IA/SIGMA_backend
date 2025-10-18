from django.db import models

class SoilType(models.Model):
    id = models.AutoField(primary_key=True)
    surface = models.CharField(max_length=50, null=False, blank=False)
    low = models.FloatField(null=True, blank=True)
    medium = models.FloatField(null=True, blank=True)
    high = models.FloatField(null=True, blank=True)
    very_high = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'soil_types'
