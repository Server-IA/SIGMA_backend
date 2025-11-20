from django.db import models


class Payroll(models.Model):
    id_payroll = models.AutoField(primary_key=True, db_column="id_payroll")
    start_date = models.DateField(db_column="start_date", null=False, blank=False)
    end_date = models.DateField(db_column="end_date", null=False, blank=False)
    id_employee = models.ForeignKey("payroll.Employee", on_delete=models.PROTECT, related_name="payrolls", db_column="id_employee", null=False, blank=False)
    id_employee_contract = models.ForeignKey("payroll.EmployeeContract", on_delete=models.PROTECT, related_name="payrolls_by_contract", db_column="id_employee_contract", null=False, blank=False)
    creation_date = models.DateTimeField(db_column="creation_date", null=False, blank=False)
    id_responsible_user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="payrolls_responsible", db_column="id_responsible_user", null=False, blank=False)

    class Meta:
        db_table = "payrolls"
