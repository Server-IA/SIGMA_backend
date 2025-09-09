from django.db import models

class Statues(models.Model):
    id_statues = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    id_statues_categories = models.ForeignKey('parameterization.StatuesCategory', on_delete=models.PROTECT)
    modification_date = models.DateTimeField()
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'statues'