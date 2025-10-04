from django.db import models


class MaintenanceReportUser(models.Model):
    """
    Modelo intermedio para la relación muchos a muchos entre MaintenanceReport y User.
    Permite que un reporte de mantenimiento tenga múltiples usuarios asignados.
    """
    id_maintenance_report_user = models.AutoField(primary_key=True)
    id_maintenance_report = models.ForeignKey(
        'maintenance.MaintenanceReport',
        on_delete=models.PROTECT,
        db_column='id_maintenance_report',
        related_name='maintenance_report_users'
    )
    id_user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        db_column='id_user',
        related_name='maintenance_report_users'
    )
    assignment_date = models.DateTimeField(auto_now_add=True, db_column='assignment_date')
    
    class Meta:
        db_table = 'maintenance_report_users'
        unique_together = (('id_maintenance_report', 'id_user'),)
        
    def __str__(self):
        return f"{self.id_user} - {self.id_maintenance_report}"
