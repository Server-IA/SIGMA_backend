from django.db import models


class MaintenanceSpareParts(models.Model):
    id_maintenance_spare_parts = models.AutoField(primary_key=True)
    spare_part_brand = models.ForeignKey(
        'parameterization.Brands',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='maintenance_spare_parts_by_brand',
        db_column='spare_part_brand'
    )
    name = models.CharField(max_length=255, null=False, blank=False, db_column="name")
    spare_parts_cost = models.FloatField(null=False, blank=False, db_column="spare_parts_cost")
    
    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_spare_parts'

    def __str__(self):
        return f"{self.name}"
