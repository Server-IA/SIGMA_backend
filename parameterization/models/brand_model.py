from django.db import models


class Models(models.Model):
    id_model = models.AutoField(primary_key=True)
    id_brand = models.ForeignKey(
        'parameterization.Brands',
        on_delete=models.PROTECT,
        null=True
    )
    name = models.CharField(max_length=255, default="")
    description = models.CharField(max_length=255, null=True)
    modification_date = models.DateTimeField(null=True)
    creation_date = models.DateTimeField(null=True)
    id_responsible_user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        null=True
    )
    id_statues = models.ForeignKey(
        'parameterization.Statues',
        on_delete=models.PROTECT,
        default=1
    )

    class Meta:
        db_table = 'models'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'id_brand'],
                name='uniq_model_name_per_brand'
            )
        ]


