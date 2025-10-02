from django.db import models


class MaintenanceReportSpareParts(models.Model):
    id_maintenance_report_spare_part = models.AutoField(primary_key=True)
    
    # Relación con el reporte de mantenimiento
    id_maintenance_report = models.ForeignKey(
        'maintenance.MaintenanceReport',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='spare_parts_used',
        db_column='id_maintenance_report'
    )
    
    # Datos de la parte (antes en MaintenanceSpareParts)
    spare_part_brand = models.ForeignKey(
        'parameterization.Brands',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='maintenance_report_spare_parts_by_brand',
        db_column='spare_part_brand'
    )
    name = models.CharField(max_length=255, null=False, blank=False, db_column="name")
    spare_parts_cost = models.FloatField(null=False, blank=False, db_column="spare_parts_cost")
    
    # Datos específicos del uso en este reporte (antes en MaintenanceSparePartsMaintenance)
    quantity_used = models.IntegerField(null=False, blank=False, default=1, db_column="quantity_used")
    cost_at_time = models.FloatField(null=False, blank=False, db_column="cost_at_time")
    
    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_report_spare_parts'

    def __str__(self):
        return f"{self.name} - {self.quantity_used} unidades"
