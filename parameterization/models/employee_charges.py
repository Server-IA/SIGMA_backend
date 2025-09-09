from django.db import models

class EmployeeCharge(models.Model):
    id_employee_charge = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    description = models.CharField(max_length=255, null=True)
    id_employee_department = models.ForeignKey('parameterization.EmployeeDepartment', on_delete=models.PROTECT, null=True)
    modification_date = models.DateTimeField(null=True)
    creation_date = models.DateTimeField(null=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=True)
    id_statues = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT)

    class Meta:
        db_table = 'employee_charges'
