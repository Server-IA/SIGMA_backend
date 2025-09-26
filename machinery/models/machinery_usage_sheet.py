from django.db import models


class MachineryUsageSheet(models.Model):
    id_usage_sheet = models.AutoField(primary_key=True)
    id_machinery = models.ForeignKey('machinery.Machinery', on_delete=models.PROTECT, null=False, blank=False)

    acquisition_date = models.DateField(null=False, blank=False)
    usage_condition = models.ForeignKey('parameterization.Statues', on_delete=models.PROTECT, null=False, blank=False, related_name='usage_condition_machinery_usage_sheets')
    usage_hours = models.DecimalField(max_digits=12, decimal_places=2, null=False, blank=False)
    distance_value = models.DecimalField(max_digits=14, decimal_places=3, null=False, blank=False)
    distance_unit = models.ForeignKey('parameterization.Units', on_delete=models.PROTECT, null=False, blank=False)

    tenancy_type = models.ForeignKey('parameterization.Types', on_delete=models.PROTECT, null=True, blank=True, related_name='tenancy_type_machinery_usage_sheets')
    is_own = models.BooleanField(default=False)
    contract_end_date = models.DateField(null=True, blank=True)

    registration_date = models.DateField(auto_now=True)
    modification_date = models.DateField(auto_now=True)
    id_responsible_user = models.ForeignKey('users.User', on_delete=models.PROTECT, null=False)
    justification = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'machinery_usage_sheet'
        constraints = [
            models.UniqueConstraint(fields=['id_machinery'], name='unique_usage_sheet_per_machinery')
        ]


