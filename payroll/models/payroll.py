from django.db import models


class Payroll(models.Model):
    id_payroll = models.AutoField(primary_key=True, db_column="id_payroll")
    start_date = models.DateField(db_column="start_date", null=False, blank=False)
    end_date = models.DateField(db_column="end_date", null=False, blank=False)
    id_employee = models.ForeignKey("payroll.Employee", on_delete=models.PROTECT, related_name="payrolls", db_column="id_employee", null=False, blank=False)
    id_employee_contract = models.ForeignKey("payroll.EmployeeContract", on_delete=models.PROTECT, related_name="payrolls_by_contract", db_column="id_employee_contract", null=False, blank=False)
    base_salary = models.FloatField(db_column="base_salary", null=False, blank=False, default=0.0)
    # Cantidad de días/horas/meses trabajados
    time_worked = models.FloatField(null=False, blank=False, db_column="time_worked", default=0.0)
    total_deductions = models.FloatField(null=False, blank=False, db_column="total_deductions", default=0.0)
    # Valor total de incrementos (devengos)
    total_increments = models.FloatField(null=False, blank=False, db_column="total_increments", default=0.0)
    # Valor neto final a pagar
    net_pay = models.FloatField(null=False, blank=False, db_column="net_pay", default=0.0)
    creation_date = models.DateTimeField(db_column="creation_date", null=False, blank=False)
    id_responsible_user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="payrolls_responsible", db_column="id_responsible_user", null=False, blank=False)

    class Meta:
        db_table = "payrolls"
