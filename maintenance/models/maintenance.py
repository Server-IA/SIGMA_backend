from django.conf import settings
from django.db import models

class Maintenance(models.Model):
    id_maintenance = models.AutoField(primary_key=True)

    name = models.CharField(
        max_length=100,   # ejemplo: 100 caracteres máximo
        unique=True,      # evita duplicados en BD
        db_column="name"
    )
    description = models.CharField(
        max_length=300,
        db_column="description"
    )
    # FKs a parameterization.Types
    maintenance_type = models.ForeignKey(
        'parameterization.Types',
        on_delete=models.PROTECT,
        related_name='maintenances_by_type',
        db_column='maintenance_type',
    )
    maintenance_status = models.ForeignKey(
        'parameterization.Types',
        on_delete=models.PROTECT,
        related_name='maintenances_by_status',
        db_column='maintenance_status',
        default=1,  
)

    # Usuario involucrado en la acción sobre Maintenance
    id_responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenances_responsible',
        db_column='id_responsible_user',
    )

    # Fechas solicitadas
    registration_date = models.DateTimeField(auto_now_add=True, db_column='registration_date')
    modification_date = models.DateTimeField(auto_now=True, db_column='modification_date')

    class Meta:
        db_table = 'maintenance'

    def __str__(self):
        return f"{self.name}"