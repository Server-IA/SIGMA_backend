from django.db import models

class EstablishedDeduction(models.Model):
    AMOUNT_TYPE_CHOICES = [
        ('Porcentaje', 'Porcentaje'),
        ('fijo', 'Fijo'),
    ]
    
    APPLICATION_DEDUCTION_TYPE_CHOICES = [
        ('SalarioBase', 'Salario Base'),
        ('SalarioFinal', 'Salario Final'),
        ('SalarioPorHora', 'Salario Por Hora'),
    ]
    
    id_established_deduction = models.AutoField(primary_key=True, db_column="id_established_deduction")
    deduction_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="established_deductions_by_type", db_column="deduction_type", null=False, blank=False)
    amount_type = models.CharField(max_length=20, choices=AMOUNT_TYPE_CHOICES, null=False, blank=False, db_column="amount_type")
    amount_value = models.FloatField(null=False, blank=False, db_column="amount_value")
    application_deduction_type = models.CharField(max_length=20, choices=APPLICATION_DEDUCTION_TYPE_CHOICES, null=False, blank=False, db_column="application_deduction_type")
    start_date_deduction = models.DateField(null=True, blank=True, db_column="start_date_deduction")
    end_date_deductions = models.DateField(null=True, blank=True, db_column="end_date_deductions")
    description = models.CharField(max_length=255, null=True, blank=True, db_column="description")
    amount = models.FloatField(null=True, blank=True, db_column="amount")
    established_contracts_contract_code = models.ForeignKey("payroll.EstablishedContract", on_delete=models.PROTECT, related_name="established_deductions", db_column="established_contracts_contract_code", null=False, blank=True)

    class Meta:
        db_table = "established_deductions"

