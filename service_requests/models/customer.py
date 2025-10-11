from django.db import models

class Customer(models.Model):
    id_customer = models.AutoField(primary_key=True)
    id_user = models.OneToOneField('users.User', on_delete=models.PROTECT, null=True, blank=True, related_name='customer_profile')
    document_number = models.IntegerField(null=True, blank=True)
    type_document_id = models.ForeignKey('service_requests.DocumentType', on_delete=models.PROTECT, null=True, blank=True,)
    check_digit = models.IntegerField(null=True, blank=True)
    person_type = models.ForeignKey('service_requests.PersonType', on_delete=models.PROTECT, null=False, blank=False, related_name='person_type')
    legal_entity_name = models.CharField(max_length=100, null=False, blank=False)
    name = models.CharField(max_length=100, null=True, blank=True,)
    first_last_name = models.CharField(max_length=100, null=True, blank=True,)
    second_last_name = models.CharField(max_length=100, null=True, blank=True,)
    email = models.CharField(max_length=100, null=True, blank=True,)
    phone = models.CharField(max_length=100, null=True, blank=True,)
    address = models.CharField(max_length=100, null=True, blank=True,)
    id_municipality = models.IntegerField(null=False, blank=False)
    tax_regime = models.IntegerField(null=False, blank=False)
    customer_statues = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, related_name='customer_statues')
    creation_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False, related_name='responsible_for_customers')

    class Meta:
        db_table = 'customer'