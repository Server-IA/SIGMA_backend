from django.db import models

class Country(models.Model):
    id_country = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'countries'