from django.db import models

class Customer(models.Model):
    id_customer = models.AutoField(primary_key=True)
    id_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True, blank=True, unique=True)
    document_number = models.IntegerField(null=True, blank=True)
    type_document_id = models.ForeignKey('service_requests.DocumentType', on_delete=models.PROTECT, null=True, blank=True,)
    person_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null = True, blank = True, related_name='person_type')
    name = models.CharField(max_length=100, null=True, blank=True,)
    first_last_name = models.CharField(max_length=100, null=True, blank=True,)
    second_last_name = models.CharField(max_length=100, null=True, blank=True,)
    email = models.CharField(max_length=100, null=True, blank=True,)
    phone = models.CharField(max_length=100, null=True, blank=True,)
    address = models.CharField(max_length=100, null=True, blank=True,)
    customer_statues = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, related_name='customer_statues')
    creation_date = models.DateTimeField(auto_now=True)
    modification_date = models.DateTimeField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)

    class Meta:
        db_table = 'customer'