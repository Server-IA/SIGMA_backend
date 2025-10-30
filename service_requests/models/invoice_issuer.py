"""Model for storing invoice issuer information.

This file previously contained a duplicated class definition which caused
`RuntimeWarning: Model 'service_requests.invoiceissuer' was already registered` when
loading Django models (e.g. during `makemigrations`). The duplicate block was removed
and the file cleaned up to define the model once.
"""

from django.db import models

INVOICE_MODEL = 'service_requests.Invoice'

class InvoiceIssuer(models.Model):
    id_invoice_issuer = models.AutoField(primary_key=True)
    invoice = models.OneToOneField(
        INVOICE_MODEL, 
        related_name='issuer', 
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Configurado para ser null por modelo de negocio actual."
    )

    issuer_name = models.CharField(max_length=255)
    issuer_identification = models.CharField(max_length=100, blank=True, null=True)
    issuer_address = models.CharField(max_length=255, blank=True, null=True)
    issuer_email = models.EmailField(blank=True, null=True)
    issuer_phone = models.CharField(max_length=50, blank=True, null=True)
    issuer_municipality = models.IntegerField(blank=True, null=True, help_text="ID del municipio del emisor")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice_issuer'

    def __str__(self):
        return f"Issuer for Invoice {getattr(self.invoice, 'id_invoice', 'unknown')}: {self.issuer_name}"
