from django.db import models

class TypesCategory(models.Model):
    id_types_categories = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    creation_date = models.DateTimeField()
    modification_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)

    class Meta:
        db_table = 'types_categories'
