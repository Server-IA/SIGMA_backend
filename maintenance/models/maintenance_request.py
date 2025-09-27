from django.db import models
from machinery.models.machinery import Machinery


class MaintenanceRequest(models.Model):
    id_maintenance_request = models.AutoField(primary_key=True)

    # Selector de la maquinaria (FK). En el front se mostrará "serial_number + apodo/nombre".
    id_machinery = models.ForeignKey(Machinery, on_delete=models.PROTECT, related_name="maintenance_requests", db_column="id_machinery", null=False, blank=False)

    # Tipo de mantenimiento (parametrizable, ej: preventivo/correctivo)
    maintenance_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="maintenance_requests_by_type", db_column="maintenance_type", null=False,blank=False)

    # Descripción de la problemática (obligatorio)
    description = models.CharField(max_length=300, null=False, blank=False, db_column="problem_description")

    # Prioridad (parametrizable de estados: alta, media, baja)
    priority = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="maintenance_requests_by_priority", db_column="priority_type", null=False, blank=False)

    # Estado de la solicitud (parametrizable de estados)
    request_status = models.ForeignKey("parameterization.Statues", on_delete=models.PROTECT, related_name="maintenance_requests_by_status", db_column="request_status", null=False, blank=False)

    # Fecha de detección (obligatoria)
    detected_at = models.DateField(db_column="detected_at", null=False, blank=False)

    # Auditoría
    registration_date = models.DateTimeField(auto_now=True, db_column="registration_date")
    modification_date = models.DateTimeField(auto_now=True, db_column="modification_date")
    id_responsible_user = models.ForeignKey("users.User", on_delete=models.PROTECT, null=False, related_name="maintenance_requests_responsible", db_column="id_responsible_user")

    class Meta:
        db_table = "maintenance_request"
