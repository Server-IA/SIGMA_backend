from django.db import models

class User(models.Model):
    id_user = models.CharField(primary_key=True, max_length=255)
    identification = models.ForeignKey('users.person', on_delete=models.PROTECT, null=True, db_column='identification')
    user_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, db_column='user_status')
    password = models.CharField(max_length=255)
    creation_date = models.DateField()
    modification_date = models.DateField()
    id_responsible_user = models.ForeignKey('self', on_delete=models.PROTECT, null=True, db_column='id_responsible_user')

    roles = models.ManyToManyField(
        'Role',
        through='UsersRoles',
        related_name='users'
    )

    class Meta:
        db_table = 'users'