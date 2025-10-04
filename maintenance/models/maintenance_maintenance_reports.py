from django.db import models
from users.models.user import User


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
    
    # Técnico que realizó el mantenimiento
    id_technician = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='maintenance_tasks_performed',
        db_column='id_technician',
        help_text="Técnico que realizó el mantenimiento"
    )
    
    # Costo del mantenimiento asociado a este reporte
    maintenance_cost = models.FloatField(null=False, blank=False, default=0.0, db_column="maintenance_cost")

    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_maintenance_reports'
        # Evitar duplicados de la misma relación
        unique_together = ('id_maintenance', 'id_maintenance_report')

    def __str__(self):
        return f"{self.id_maintenance.name}"
