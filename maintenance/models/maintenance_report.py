from django.db import models
from django.apps import apps


class MaintenanceReport(models.Model):
    id_maintenance_report = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False, blank=False, db_column="title")
    description = models.CharField(max_length=600, null=False, blank=False, db_column="description")
    id_responsible_user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='maintenance_reports_responsible',
        db_column='id_responsible_user'
    )
    id_maintenance_scheduling = models.ForeignKey(
        'maintenance.MaintenanceScheduling',
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name='maintenance_reports',
        db_column='id_maintenance_scheduling'
    )
    spare_parts_total_cost = models.FloatField(default=0.0, db_column="spare_parts_total_cost")
    
    currency_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='currency_unit')

    # Campos adicionales para la historia de usuario
    time_invested_hours = models.IntegerField(null=False, blank=False, db_column="time_invested_hours")
    time_invested_minutes = models.IntegerField(null=False, blank=False, db_column="time_invested_minutes")
    time_invested_seconds = models.IntegerField(null=False, blank=False, db_column="time_invested_seconds")
    recommendations = models.TextField(null=True, blank=True, db_column="recommendations")
    total_cost = models.FloatField(default=0.0, db_column="total_cost")
    
    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_reports'

    # Many-to-many relationship with User through MaintenanceReportUser
    assigned_users = models.ManyToManyField(
        'users.User',
        through='maintenance.MaintenanceReportUser',
        through_fields=('id_maintenance_report', 'id_user'),
        related_name='assigned_maintenance_reports',
        help_text="Usuarios asignados a este reporte de mantenimiento"
    )

    def __str__(self):
        return f"{self.title}"