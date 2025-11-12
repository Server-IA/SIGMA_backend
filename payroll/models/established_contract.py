from django.db import models

class EstablishedContract(models.Model):
    PAYMENT_FREQUENCY_CHOICES = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
    ]
    
    SALARY_TYPE_CHOICES = [
        ('Por horas', 'Por horas'),
        ('Por días', 'Por días'),
        ('Mensual fijo', 'Mensual fijo'),
    ]
    
    contract_code = models.CharField(primary_key=True, max_length=20, null=False, db_column="contract_code")
    id_employee_charge = models.ForeignKey("parameterization.EmployeeCharge", on_delete=models.PROTECT, related_name="established_contracts", db_column="employee_charges_id_employee_charge", null=False, blank=False)
    description = models.CharField(max_length=100, null=True, blank=True, db_column="description")
    contract_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="established_contracts_by_contract_type", db_column="contract_type", null=False, blank=False)
    start_date = models.DateField(db_column="start_date", null=False, blank=False)
    end_date = models.DateField(db_column="end_date", null=False, blank=False)
    payment_frequency_type = models.CharField(max_length=20, choices=PAYMENT_FREQUENCY_CHOICES, null=False, blank=False, db_column="payment_frequency_type")
    minimum_hours = models.IntegerField(null=True, blank=True, db_column="minimum_hours")
    workday_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="established_contracts_by_workday_type", db_column="workday_type", null=True, blank=True)
    work_mode_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="established_contracts_by_work_mode_type", db_column="work_mode_type", null=True, blank=True)
    salary_type = models.CharField(max_length=20, choices=SALARY_TYPE_CHOICES, null=False, blank=False, db_column="salary_type")
    salary_base = models.FloatField(null=False, blank=False, db_column="salary_base")
    currency_type = models.ForeignKey("parameterization.Types", on_delete=models.PROTECT, related_name="established_contracts_by_currency_type", db_column="currency_type", null=False, blank=False)
    trial_period_days = models.IntegerField(null=True, blank=True, db_column="trial_period_days")
    vacation_days = models.IntegerField(null=False, blank=False, db_column="vacation_days")
    cumulative_vacation = models.IntegerField(null=True, blank=True, db_column="cumulative_vacation")
    vacation_frequency_days = models.IntegerField(null=True, blank=True, db_column="vacation_frequency_days")
    maximum_disability_days = models.IntegerField(null=False, blank=False, db_column="maximum_disability_days")
    overtime = models.FloatField(null=False, blank=False, db_column="overtime")
    overtime_period = models.IntegerField(null=True, blank=True, db_column="overtime_period")
    notice_period_days = models.IntegerField(null=True, blank=True, db_column="notice_period_days")
    established_contract_status = models.ForeignKey("parameterization.Statues", on_delete=models.PROTECT, related_name="established_contracts_by_status", db_column="established_contract_status", null=False, blank=False)
    creation_date = models.DateTimeField(db_column="creation_date", null=False, blank=False)
    modification_date = models.DateTimeField(db_column="modification_date", null=False, blank=False)
    id_responsible_user = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="established_contracts_responsible", db_column="id_responsible_user", null=False, blank=False)

    class Meta:
        db_table = "established_contracts"

