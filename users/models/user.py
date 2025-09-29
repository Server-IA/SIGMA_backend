from django.db import models

class User(models.Model):
    id_user = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'users'