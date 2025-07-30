from django.db import models

class Types(models.Model):
    id_types = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)
    id_types_categories = models.ForeignKey('parameterization.TypesCategory', on_delete=models.PROTECT)
    creation_date = models.DateTimeField()
    modification_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)
    id_statues = models.ForeignKey('Statues', on_delete=models.PROTECT)

    class Meta:
        db_table = 'types'
