from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class EmployeeContractPayment(models.Model):
    id_contract_payment = models.AutoField(primary_key=True, db_column="id_contract_payment")
    date_payment = models.IntegerField(db_column="date_payment", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(31)])
    id_day_of_week = models.ForeignKey("payroll.DaysOfWeek", on_delete=models.PROTECT, related_name="employee_contract_payments_by_day", db_column="id_day_of_week", null=True, blank=True)
    employee_contracts_contract_code = models.ForeignKey("payroll.EmployeeContract", on_delete=models.PROTECT, related_name="contract_payments", db_column="employee_contracts_contract_code", null=False, blank=False)

    class Meta:
        db_table = "employee_contract_payments"