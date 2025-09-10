from django.db import models


class Units(models.Model):
    id_units = models.AutoField(primary_key=True)
    id_units_categories = models.ForeignKey('parameterization.UnitsCategory', on_delete=models.PROTECT, editable=False)
    name = models.CharField(max_length=255, blank=False, null=False)
    symbol = models.CharField(max_length=50, blank=True, null=True)
    id_types = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, blank=False, null=False)
    modification_date = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)
    id_statues = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)

    class Meta:
        db_table = 'units'


