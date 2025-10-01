from django.db import models
from machinery.models.machinery import Machinery

class MaintenanceScheduling(models.Model):
    id_maintenance_scheduling = models.CharField(primary_key=True, max_length=20, null=False)
    id_maintenance_request = models.ForeignKey("maintenance.MaintenanceRequest", on_delete=models.PROTECT, related_name="maintenance_schedulings", db_column="id_maintenance_request", null=True, blank=True)
    id_machinery = models.ForeignKey(Machinery, on_delete=models.PROTECT, related_name="maintenance_schedulings", db_column="id_machinery", null=False, blank=False)
    scheduled_at = models.DateTimeField(db_column="scheduled_at", null=False, blank=False)
    details = models.CharField(max_length=350, null=False, blank=False, db_column="details")
    assigned_technician = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="maintenance_schedulings_assigned", db_column="id_assigned_technician", null=False, blank=False)
    maintenance_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="maintenance_schedulings_by_type", db_column="maintenance_type", null=False, blank=False)
    maintenance_scheduling_status = models.ForeignKey("parameterization.Statues", on_delete=models.PROTECT, related_name="maintenance_scheduling_by_status", db_column="maintenance_scheduling_status", null=False, blank=False)
    justification = models.CharField(max_length=300, null=True, blank=True)
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")
    id_responsible_user = models.ForeignKey("users.User", on_delete=models.PROTECT, null=False, related_name="maintenance_schedulings_responsible", db_column="id_responsible_user")

    class Meta:
        db_table = "maintenance_scheduling"
