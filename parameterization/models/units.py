from django.db import models


class Units(models.Model):
    id_units = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    id_units_categories = models.ForeignKey('parameterization.UnitsCategory', on_delete=models.PROTECT)
    modification_date = models.DateTimeField()
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)
    id_statues = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)

    class Meta:
        db_table = 'units'


