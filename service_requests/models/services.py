from django.db import models

class Service(models.Model):
    id_service = models.AutoField(primary_key=True)
    service_name = models.CharField(max_length=100, null=False, blank=False)
    description = models.CharField(max_length=500, null=True, blank=True)
    service_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=False, blank=False, related_name='service_type')
    base_price = models.FloatField(null=False, blank=False)
    price_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False, related_name='service_price_unit')
    applicable_tax = models.IntegerField(null=False, blank=False)
    tax_rate = models.FloatField(null=True, blank=True)
    is_vat_exempt = models.BooleanField(default=False, null=True, blank=True)
    service_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, related_name='service_status')
    creation_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False, blank=False, related_name='responsible_for_services')

    class Meta:
        db_table = 'services'
