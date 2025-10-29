# service_requests/models/invoice.py

from django.db import models
from django.utils import timezone

CUSTOMER_MODEL = 'service_requests.Customer'
TAX_REGIME_MODEL = 'service_requests.TaxRegime'
SERVICE_REQUEST_MODEL = 'service_requests.ServiceRequest'
STATUES_MODEL = 'parameterization.Statues'

class Invoice(models.Model):
    id_invoice = models.AutoField(primary_key=True)
    customer = models.ForeignKey(CUSTOMER_MODEL, on_delete=models.PROTECT, related_name='invoices')
    tax_regime = models.ForeignKey(TAX_REGIME_MODEL, on_delete=models.PROTECT)
    
    service_request = models.ForeignKey(SERVICE_REQUEST_MODEL, on_delete=models.PROTECT, related_name='invoices', null=True, blank=True)

    reference_code = models.CharField(max_length=100, unique=True, db_index=True)
    invoice_date = models.DateField(default=timezone.now)
    
    status = models.ForeignKey(
        STATUES_MODEL,
        on_delete=models.PROTECT,
        help_text='Estado actual de la factura (ref: Statues)'
    )

    payment_method = models.ForeignKey(
        'service_requests.PaymentMethod',
        on_delete=models.PROTECT,
        help_text="Método de pago (ref: PaymentMethod)",
        null=True, blank=True
    )
    observation = models.TextField(blank=True, null=True)

    # Totales
    total_without_taxes = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_taxes = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_withholding_taxes = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    amount_to_pay = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Campos FE
    cufe = models.CharField(max_length=255, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    api_response = models.JSONField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # URLs públicas de archivos en Firebase Storage
    invoice_pdf_url = models.URLField(max_length=500, blank=True, null=True)
    invoice_xml_url = models.URLField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'invoice'