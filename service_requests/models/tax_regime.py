from django.db import models


class TaxRegime(models.Model):
    id_tax_regime = models.AutoField(primary_key=True)
    code = models.CharField(max_length=100, null=False, blank=False, unique=True)
    name = models.CharField(max_length=100, null=False, blank=False)

    class Meta:
        db_table = 'tax_regime'
