from django.db import models

class ContractPaymentsEstablishedContract(models.Model):
    id_contract_payment = models.AutoField(primary_key=True, db_column="id_contract_payment")
    date_payment = models.DateField(db_column="date_payment", null=False, blank=False)
    id_day_of_week = models.ForeignKey("payroll.DaysOfWeek", on_delete=models.PROTECT, related_name="contract_payments_by_day", db_column="id_day_of_week", null=False, blank=False)
    established_contracts_contract_code = models.ForeignKey("payroll.EstablishedContract", on_delete=models.PROTECT, related_name="contract_payments", db_column="established_contracts_contract_code", null=False, blank=False)

    class Meta:
        db_table = "contract_payments_established_contract"

