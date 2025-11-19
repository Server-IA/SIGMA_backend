from django.db import models


class Employee(models.Model):
    id_employee = models.AutoField(primary_key=True)
    id_user = models.OneToOneField('users.User', on_delete=models.PROTECT, db_column="id_user", null=True, blank=True, unique=True)
    email = models.EmailField(max_length=255, null=False, blank=False, unique=True)
    id_employee_charge = models.ForeignKey('parameterization.EmployeeCharge', on_delete=models.PROTECT, null=False, blank=False)
    employee_status = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, null=False, blank=False)
    creation_date = models.DateTimeField(db_column="creation_date", null=False, blank=False)
    modification_date = models.DateTimeField(db_column="modification_date", null=False, blank=False)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='employee_responsible_user', null=False, blank=False)

    class Meta:
        db_table = 'employees'
