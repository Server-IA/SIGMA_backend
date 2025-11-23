from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class TemporaryPayrollAdjustment(models.Model):
    """
    Ajustes temporales cargados desde Excel para nómina masiva.
    Se confirman o descartan al generar la nómina.
    """
    
    ADJUSTMENT_TYPE_CHOICES = [
        ('deduccion', 'Deducción'),
        ('incremento', 'Incremento'),
    ]
    
    AMOUNT_TYPE_CHOICES = [
        ('Porcentaje', 'Porcentaje'),
        ('fijo', 'Fijo'),
    ]

    APPLICATION_TYPE_CHOICES = [
        ("SalarioBase", "Salario Base"),
        ("SalarioFinal", "Salario Final"),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmado'),
        ('rejected', 'Rechazado'),
    ]
    
    # Identificación
    id_temp_adjustment = models.AutoField(primary_key=True)    
    # Relaciones
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='temp_payroll_adjustments'
    )
    user_creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_temp_adjustments'
    )
    
    # Datos del ajuste
    adjustment_name = models.CharField(max_length=255)  # Nombre de la novedad
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    amount_type = models.CharField(max_length=20, choices=AMOUNT_TYPE_CHOICES)
    amount_value = models.DecimalField(max_digits=15, decimal_places=2)
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPE_CHOICES, null=False, blank=False, db_column="application_deduction_type")
    # Datos del periodo de nómina
    start_date_adjustment = models.DateField()
    end_date_adjustment = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    description = models.CharField(max_length=255)  # Descripción de la carga
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    batch_id = models.UUIDField(db_index=True)  # Para agrupar ajustes del mismo Excel

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # TTL de 24 horas
    

    
    class Meta:
        db_table = 'temporary_payroll_adjustments'
    
    def save(self, *args, **kwargs):
        # Establecer fecha de expiración (24 horas desde creación)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)