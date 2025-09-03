from django.db import models


class UnitsCategory(models.Model):
    id_units_categories = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    modification_date = models.DateTimeField()
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'units_categories'


