from django.db import models

class Role(models.Model):
    id_role = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    rol_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, db_column='rol_status')
    modification_date = models.DateTimeField()
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey('users.user', on_delete=models.PROTECT, null=True, db_column='id_responsible_user')

    class Meta:
        db_table = 'roles'