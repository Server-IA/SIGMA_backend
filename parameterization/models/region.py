from django.db import models

class Region(models.Model):
    id_region = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    id_country = models.ForeignKey('parameterization.Country', on_delete=models.PROTECT)

    class Meta:
        db_table = 'regions'
