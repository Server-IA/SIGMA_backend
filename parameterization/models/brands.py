from django.db import models


class Brands(models.Model):
    id_brands = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255)
    id_brands_categories = models.ForeignKey(
        'parameterization.BrandsCategory',
        on_delete=models.PROTECT
    )
    modification_date = models.DateTimeField()
    creation_date = models.DateTimeField()
    id_responsible_user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        null=True
    )
    id_statues = models.ForeignKey(
        'parameterization.Statues',
        on_delete=models.PROTECT
    )

    class Meta:
        db_table = 'brands'


