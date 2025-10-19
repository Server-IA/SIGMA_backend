from django.db import models

class PaymentMethod(models.Model):
    code = models.CharField(primary_key=True, max_length=50, unique=True, null=False, blank=False, verbose_name='Código')
    name = models.CharField(max_length=100, null=False, blank=False, verbose_name='Nombre')

    class Meta:
        db_table = 'payment_methods'