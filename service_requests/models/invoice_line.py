# service_requests/models/invoice_line.py

from django.db import models

INVOICE_MODEL = 'service_requests.Invoice'
SERVICE_CATALOGUE_MODEL = 'service_requests.Service' 

class InvoiceLine(models.Model):
    id_invoice_line = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(INVOICE_MODEL, related_name='lines', on_delete=models.CASCADE) 
    
    service_item = models.ForeignKey(SERVICE_CATALOGUE_MODEL, on_delete=models.PROTECT)
    
    service_name = models.CharField(max_length=255) # Duplica Service.service_name
    code_reference = models.CharField(max_length=50, blank=True, null=True) # Campo añadido para Facturación Electrónica (FE)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    price_unit = models.DecimalField(max_digits=15, decimal_places=2) # Duplica Service.base_price
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Impuestos
    percentage_taxes_per_line = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) # Duplica Service.tax_rate
    tax_per_line_type = models.CharField(max_length=50, default='IVA') # Tipo de impuesto
    
    # Campos DIAN
    units_measurement_id = models.IntegerField(default=70) 
    tribute_id = models.CharField(max_length=10, default='1')

    # Retenciones por línea 
    withholding_taxes = models.JSONField(blank=True, null=True, default=list)

    class Meta:
        db_table = 'invoice_line'