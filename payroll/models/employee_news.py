from django.db import models

class EmployeeNews(models.Model):
    NEWS_TYPE_CHOICES = [
        ('CREACION_EMPLEADO', 'Creación de empleado'),
        ('ACTUALIZACION_EMPLEADO', 'Actualizar empleado'),
        ('DESACTIVACION_EMPLEADO', 'Desactivar empleado'),
        ('GENERAR_OTRO_SI', 'Generar otro si'),
        ('CAMBIO_CONTRATO', 'Cambio de contrato'),
        ('FINALIZACION_CONTRATO', 'Finalización de contrato'),
    ]

    id_employee_new = models.AutoField(primary_key=True)
    id_employee = models.ForeignKey('payroll.Employee', on_delete=models.PROTECT, null=False, blank=False)
    observation = models.CharField(max_length=255, null=True, blank=True)
    news_date = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    news_type = models.CharField(max_length=30, choices=NEWS_TYPE_CHOICES, null=False, blank=False)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'employee_news'

