from django.db import models

class Implementation(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=False, blank=False)
    real_name = models.CharField(max_length=50, null=False, blank=False)
    k_base = models.FloatField(null=True, blank=True)
    n = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'implementations'
