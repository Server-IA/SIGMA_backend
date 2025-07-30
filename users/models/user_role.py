from django.db import models

class UsersRoles(models.Model):
    id_users_roles = models.AutoField(primary_key=True)
    id_user = models.ForeignKey('users.user', on_delete=models.DO_NOTHING)
    id_role = models.ForeignKey('users.role', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'users_roles'
        unique_together = (('id_user', 'id_role'),)