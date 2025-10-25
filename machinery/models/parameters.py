from django.db import models

class Parameters(models.Model):
    id = models.AutoField(primary_key=True)
    parameter_name = models.CharField(max_length=50, null=False, blank=False)
    avl_id_parameter = models.IntegerField(unique=True, null=False)
    description = models.CharField(max_length=200, null=True, blank=True)
    minimum_range = models.BigIntegerField(null=True, blank=True)
    maximum_range = models.BigIntegerField(null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    minimun_message = models.CharField(max_length=100, null=True, blank=True)
    maximum_message = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'parameters'
