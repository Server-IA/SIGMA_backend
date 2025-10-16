from django.db import models
from django.utils import timezone

class ServiceRequest(models.Model):
    id_request = models.CharField(primary_key=True, max_length=20)
    customer = models.ForeignKey('service_requests.Customer', on_delete=models.PROTECT,null=False, blank=False, related_name='service_requests')
    request_detail = models.TextField(max_length=600, null=False, blank=False)
    scheduled_start_date = models.DateField(null=False, blank=False)
    scheduled_end_date = models.DateField(null=False, blank=False)
    payment_method = models.ForeignKey('service_requests.PaymentMethod', on_delete=models.PROTECT, null=True, blank=True, related_name='payment_method_requests')
    payment_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, null=True, blank=True, related_name='payment_status_requests')
    amount_paid = models.FloatField(null=True, blank=True)
    currency_unit_amount_paid = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='currency_paid_requests')
    amount_to_pay = models.FloatField(null=True, blank=True)
    currency_unit_amount_to_pay = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=True, blank=True, related_name='currency_to_pay_requests')
    confirmation_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True, blank=True, related_name='confirmed_requests')
    confirmation_datetime = models.DateTimeField(null=True, blank=True)
    completion_cancellation_observations = models.TextField(max_length=500, null=True, blank=True)
    completion_cancellation_datetime = models.DateTimeField(null=True, blank=True)
    completion_cancellation_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True, blank=True, related_name='completed_cancelled_requests')
    request_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, null=False, blank=False, related_name='status_requests')
    creation_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False, blank=False, related_name='responsible_user')

    class Meta:
        db_table = 'service_requests'
