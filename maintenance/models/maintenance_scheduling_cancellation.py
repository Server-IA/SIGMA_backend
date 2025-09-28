from django.db import models


class MaintenanceSchedulingCancellation(models.Model):
    id_maintenance_scheduling_cancellation = models.AutoField(primary_key=True)
    id_maintenance_scheduling = models.ForeignKey(
        "maintenance.MaintenanceScheduling",
        on_delete=models.PROTECT,
        related_name="cancellations",
        db_column="id_maintenance_scheduling",
        null=False,
        blank=False,
    )
    reason = models.CharField(max_length=350, null=False, blank=False, db_column="reason")
    canceled_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="maintenance_scheduling_cancellations",
        db_column="id_canceled_by",
        null=False,
        blank=False,
    )
    canceled_at = models.DateTimeField(auto_now_add=True, db_column="canceled_at")
    notified = models.BooleanField(default=False, db_column="notified")

    class Meta:
        db_table = "maintenance_scheduling_cancellation"

    def __str__(self) -> str:
        return f"Cancelación #{self.id_maintenance_scheduling_cancellation} de programación {self.id_maintenance_scheduling_id}"


