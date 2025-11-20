from django.db import models

class EmployeeContractIncrease(models.Model):
    AMOUNT_TYPE_CHOICES = [
        ('Porcentaje', 'Porcentaje'),
        ('fijo', 'Fijo'),
    ]
    
    APPLICATION_INCREASE_TYPE_CHOICES = [
        ('SalarioBase', 'Salario Base'),
        ('SalarioFinal', 'Salario Final'),
    ]
    
    id_employee_contract_increase = models.AutoField(primary_key=True, db_column="id_employee_contract_increase")
    increase_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="employee_contract_increases_by_type", db_column="increase_type", null=False, blank=False)
    amount_type = models.CharField(max_length=20, choices=AMOUNT_TYPE_CHOICES, null=False, blank=False, db_column="amount_type")
    amount_value = models.FloatField(null=False, blank=False, db_column="amount_value")
    application_increase_type = models.CharField(max_length=20, choices=APPLICATION_INCREASE_TYPE_CHOICES, null=False, blank=False, db_column="application_increase_type")
    start_date_increase = models.DateField(null=True, blank=True, db_column="start_date_increase")
    end_date_increase = models.DateField(null=True, blank=True, db_column="end_date_increase")
    description = models.CharField(max_length=255, null=True, blank=True, db_column="description")
    amount = models.FloatField(null=True, blank=True, db_column="amount")
    employee_contracts_contract_code = models.ForeignKey("payroll.EmployeeContract", on_delete=models.PROTECT, related_name="employee_contract_increases", db_column="employee_contracts_contract_code", null=False, blank=False)

    class Meta:
        db_table = "employee_contract_increases"