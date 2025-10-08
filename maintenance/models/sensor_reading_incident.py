from django.db import models


class SensorReadingIncident(models.Model):
    """
    Modelo para registrar incidentes de lectura de sensores o telemetría.
    Cumple con el criterio de aceptación #9 de HU-SM-002.
    """
    id_sensor_incident = models.AutoField(primary_key=True)
    
    id_machinery = models.ForeignKey(
        'machinery.Machinery',
        on_delete=models.PROTECT,
        related_name='sensor_incidents',
        db_column='id_machinery',
        null=False,
        blank=False
    )
    
    incident_type = models.CharField(
        max_length=50,
        db_column='incident_type',
        null=False,
        blank=False,
        help_text='Tipo de incidente: sensor_error, telemetry_error, data_validation_error, etc.'
    )
    
    description = models.TextField(
        db_column='description',
        null=False,
        blank=False,
        help_text='Descripción detallada del error o incidente'
    )
    
    error_details = models.TextField(
        db_column='error_details',
        null=True,
        blank=True,
        help_text='Detalles técnicos del error (stack trace, código de error, etc.)'
    )
    
    notified = models.BooleanField(
        default=False,
        db_column='notified',
        help_text='Indica si se notificó al jefe de mantenimiento'
    )
    
    notification_date = models.DateTimeField(
        null=True,
        blank=True,
        db_column='notification_date',
        help_text='Fecha y hora en que se envió la notificación'
    )
    
    detected_at = models.DateTimeField(
        auto_now_add=True,
        db_column='detected_at',
        help_text='Fecha y hora de detección del incidente'
    )
    
    registration_date = models.DateTimeField(
        auto_now_add=True,
        db_column='registration_date'
    )
    
    modification_date = models.DateTimeField(
        auto_now=True,
        db_column='modification_date'
    )
    
    class Meta:
        db_table = 'sensor_reading_incident'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['id_machinery', '-detected_at']),
            models.Index(fields=['notified', '-detected_at']),
        ]
    
    def __str__(self):
        return f"Incident {self.id_sensor_incident} - {self.incident_type} - Machinery {self.id_machinery_id}"
