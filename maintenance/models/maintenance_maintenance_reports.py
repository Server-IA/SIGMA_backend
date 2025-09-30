from django.db import models


class MaintenanceMaintenanceReports(models.Model):
    id_maintenance = models.ForeignKey(
        'maintenance.Maintenance',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='maintenance_reports_relations',
        db_column='id_maintenance'
    )
    id_maintenance_report = models.ForeignKey(
        'maintenance.MaintenanceReport',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='maintenance_relations',
        db_column='id_maintenance_report'
    )
    
    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_maintenance_reports'
        # Evitar duplicados de la misma relación
        unique_together = ('id_maintenance', 'id_maintenance_report')

    def __str__(self):
        return f"{self.id_maintenance.name}"
