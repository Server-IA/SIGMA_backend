from django.db import models

class City(models.Model):
    id_city = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    id_region = models.ForeignKey('parameterization.Region', on_delete=models.PROTECT)

    class Meta:
        db_table = 'cities'