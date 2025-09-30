from django.db import models


class MaintenanceSparePartsMaintenance(models.Model):
    id_maintenance_spare_part = models.ForeignKey(
        'maintenance.MaintenanceSpareParts',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='maintenance_relations',
        db_column='id_maintenance_spare_part'
    )
    id_maintenance_report = models.ForeignKey(
        'maintenance.MaintenanceReport',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='spare_parts_relations',
        db_column='id_maintenance_report'
    )
    
    # Campos adicionales para la relación
    quantity_used = models.IntegerField(null=False, blank=False, default=1, db_column="quantity_used")
    cost_at_time = models.FloatField(null=False, blank=False, db_column="cost_at_time")
    
    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_spare_parts_maintenance'
        # Evitar duplicados de la misma relación
        unique_together = ('id_maintenance_spare_part', 'id_maintenance_report')

    def __str__(self):
        return f"{self.id_maintenance_spare_part.name}"
