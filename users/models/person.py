from django.db import models

class Person(models.Model):
    identification = models.CharField(primary_key=True, max_length=255)
    document_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, related_name='document_type')
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    first_last_name = models.CharField(max_length=255)
    second_last_name = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateField()
    email = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    gender_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, related_name='gender_type')
    id_city = models.ForeignKey('parameterization.City', on_delete=models.PROTECT)
    creation_date = models.DateField()
    modification_date = models.DateField()
    id_responsible_user = models.ForeignKey('users.user', on_delete=models.PROTECT)
    person_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)

    class Meta:
        db_table = 'persons'