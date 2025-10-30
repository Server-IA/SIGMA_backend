# service_requests/services/invoice_electronic_service.py

from django.db import transaction
from service_requests.models.invoice import Invoice
from parameterization.models import Statues
from core.services.factus_service import FactusService, FactusServiceError
import json
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

factus_api = FactusService() 

def build_api_payload(invoice):
    """
    Transforma el objeto Invoice de Django al payload JSON para Factus,
    adaptándose al modelo Customer proporcionado.
    """
    customer = invoice.customer 
    
    # Estructura Customer (Mapeo de Nombres y Acceso a IDs) 
    customer_payload = {
        # Campos de identificación y nombres (Conversión a string si es necesario)
        "identification": str(customer.document_number),
        "dv": str(customer.check_digit), # Mapeado de check_digit
        "company": customer.legal_entity_name or "", # Mapeado de legal_entity_name
        "trade_name": customer.bussiness_name or "", # Mapeado de bussiness_name
        
        "names": customer.name or f"{customer.first_last_name} {customer.second_last_name}".strip(),
        
        "address": customer.address or "",
        "email": customer.email or "",
        "phone": customer.phone or "",
        
        "legal_organization_id": str(customer.person_type_id), # OK: Usa la FK person_type_id
        "tribute_id": str(customer.tax_regime_id), # OK: Usa la FK tax_regime_id
        "identification_document_id": customer.type_document_id_id, # OK: Usa la FK type_document_id_id
        
        # Campo que ya era un IntegerField
        "municipality_id": str(customer.id_municipality) 
    }

    # Estructura Items (Se mantiene sin cambios en base a oiceLine)
    items_payload = []
    for line in invoice.lines.all():
        is_excluded = 1 if Decimal(line.tax_per_line_type) == Decimal('0.00') else 0
        
        items_payload.append({
            "code_reference": line.code_reference,
            "name": line.service_name,
            "quantity": float(line.quantity),
            "discount_rate": float(line.discount_percentage),
            "price": float(line.price_unit),
            "tax_rate": f"{line.tax_per_line_type:.2f}", 
            "unit_measure_id": line.unit_measure_id, 
            "standard_code_id": 1, 
            "is_excluded": is_excluded, 
            "tribute_id": line.tribute_id, 
            "withholding_taxes": []
        })

    # Estructura Principal
    payload = {
        "document": "01", 
        "numbering_range_id": invoice.numbering_range_id,
        "reference_code": invoice.reference_code,
        "observation": invoice.observation or "", 
        "payment_method_code": invoice.payment_method_code,
        "customer": customer_payload,
        "items": items_payload,
        "allowance_charges": [] 
    }
    
    return payload
@transaction.atomic
def send_invoice_to_api(invoice):
    """
    Maneja el flujo completo: transformación, envío (vía FactusService) y actualización de la DB.
    """
    # 1. Preparar la carga útil
    payload = build_api_payload(invoice)

    try:
        # 2. Enviar a la API externa a través de la clase FactusService
        response_data = factus_api.generate_invoice(payload)
        
        # 3. Procesar respuesta exitosa (Factura Aceptada / En Proceso)
        # Cambiar a estado VALIDADA (26)
        invoice.status_id = 26
        invoice.invoice_number = response_data.get('invoice_number', invoice.reference_code)
        invoice.cufe = response_data.get('cufe_code') 
        invoice.api_response = json.dumps(response_data)
        invoice.save(update_fields=['status', 'invoice_number', 'cufe', 'api_response'])
        
        logger.info(f"Factura {invoice.id_invoice} validada correctamente. CUFE: {invoice.cufe}")
        
        return {
            "detail": "Factura Electrónica enviada y validada exitosamente.",
            "status": "validada",
            "cufe": invoice.cufe
        }

    except FactusServiceError as e:
        # Si la API falla o la validación es rechazada, cambiar a estado RECHAZADA (27)
        invoice.status_id = 27
        invoice.api_response = str(e)
        invoice.save(update_fields=['status', 'api_response'])
        
        logger.error(f"Error al validar factura {invoice.id_invoice}: {str(e)}")
        
        raise Exception(f"Fallo en la validación de Factus: {str(e)}")