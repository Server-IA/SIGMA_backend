from django.db import models
from django.db.models import Q
from machinery.models.machinery import Machinery
from maintenance.models.maintenance import Maintenance

class PeriodicMaintenanceScheduling(models.Model):
    id_periodic_maintenance_scheduling = models.AutoField(
        primary_key=True, db_column="id_periodic_maintenance_scheduling"
    )

    machinery = models.ForeignKey(
        Machinery,
        on_delete=models.PROTECT,
        related_name="periodic_maintenances",
        db_column="id_machinery",
    )

    maintenance = models.ForeignKey(
        Maintenance,
        on_delete=models.PROTECT,
        related_name="periodic_schedules",
        db_column="id_maintenance",
    )

    # Longitud de medida 1 
    usage_hours = models.PositiveIntegerField(db_column="usage_hours", null=True, blank=True)

    # Longitud de medida 2 
    distance_km = models.PositiveIntegerField(db_column="distance_km", null=True, blank=True)

    class Meta:
        db_table = "periodic_maintenance_scheduling"
        constraints = [
            models.CheckConstraint(
                name="pm_exactly_one_trigger",
                check=(
                    (Q(usage_hours__isnull=False) & Q(distance_km__isnull=True)) |
                    (Q(usage_hours__isnull=True) & Q(distance_km__isnull=False))
                ),
            ),
            # Evitar duplicados por maquinaria + mantenimiento + modalidad
            models.UniqueConstraint(
                fields=["machinery", "maintenance", "usage_hours"],
                name="uniq_pm_by_mach_maint_hours",
                condition=Q(usage_hours__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["machinery", "maintenance", "distance_km"],
                name="uniq_pm_by_mach_maint_distance",
                condition=Q(distance_km__isnull=False),
            ),
        ]

    def __str__(self):
        if self.usage_hours is not None:
            return f"{self.machinery_id} · {self.maintenance_id} ({self.usage_hours}h)"
        return f"{self.machinery_id} · {self.maintenance_id} ({self.distance_km}km)"