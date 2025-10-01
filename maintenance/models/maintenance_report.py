from django.db import models


class MaintenanceReport(models.Model):
    id_maintenance_report = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, null=False, blank=False, db_column="title")
    description = models.CharField(max_length=600, null=False, blank=False, db_column="description")
    creation_date = models.DateField(auto_now_add=True, db_column="creation_date")
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
    
    # Campos adicionales para la historia de usuario
    time_invested_hours = models.IntegerField(null=False, blank=False, db_column="time_invested_hours")
    time_invested_minutes = models.IntegerField(null=False, blank=False, db_column="time_invested_minutes")
    recommendations = models.TextField(null=True, blank=True, db_column="recommendations")
    total_cost = models.FloatField(default=0.0, db_column="total_cost")
    
    # Fechas de auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")

    class Meta:
        db_table = 'maintenance_reports'

    def __str__(self):
        return f"{self.title}"