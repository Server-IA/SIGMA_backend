# service_requests/utils/invoice_generator_utils.py

import uuid
import logging
from django.db import transaction
from django.apps import apps
import logging
from ..models.invoice import Invoice
from decimal import Decimal
from ..models.invoice_line import InvoiceLine

logger = logging.getLogger(__name__)

def generate_unique_reference_code():
    """Genera un código de referencia único para la factura."""
    return 'sigma-fact-' + uuid.uuid4().hex[:8].upper()

def recalculate_invoice_totals(invoice: Invoice):
    """Calcula y actualiza los totales de la factura."""
    lines = invoice.lines.all()
    total_without_taxes = 0
    total_taxes = 0
    total_withholding_taxes = 0

    for line in lines:
        subtotal = line.quantity * line.price_unit
        discount_amount = subtotal * (line.discount_percentage / 100)
        base_tax = subtotal - discount_amount
        tax_amount = base_tax * (line.percentage_taxes_per_line / 100)
        # Retenciones por línea (aplicadas sobre base_tax por defecto)
        line_withholding_total = 0
        wt_list = getattr(line, 'withholding_taxes', None) or []
        for wt in wt_list:
            try:
                rate = float(wt.get('withholding_tax_rate', 0))
            except Exception:
                rate = 0
            if rate > 0:
                line_withholding_total += float(base_tax) * (rate / 100.0)
        
        total_without_taxes += base_tax
        total_taxes += tax_amount
        total_withholding_taxes += line_withholding_total

    with transaction.atomic():
        invoice.total_without_taxes = round(total_without_taxes, 2)
        invoice.total_taxes = round(total_taxes, 2)
        invoice.total_withholding_taxes = round(total_withholding_taxes, 2)
        invoice.amount_to_pay = round(total_without_taxes + total_taxes - total_withholding_taxes, 2)
        invoice.save()

        # Sincronizar el monto a pagar con la Solicitud de Servicio asociada (si existe)
        if getattr(invoice, 'service_request_id', None):
            ServiceRequest = apps.get_model('service_requests', 'ServiceRequest')
            # Actualizamos solo el campo amount_to_pay para evitar side-effects
            ServiceRequest.objects.filter(pk=invoice.service_request_id).update(
                amount_to_pay=float(invoice.amount_to_pay)
            )
    
    return invoice

logger = logging.getLogger(__name__)


def _compute_dv_for_nit(nit: str) -> int:
    """Calcula el dígito de verificación (DV) para un NIT colombiano.

    Implementa el algoritmo DIAN usando los pesos oficiales.
    Retorna el DV como string (0-9). Lanza ValueError si el NIT no es numérico.
    """
    if nit is None:
        raise ValueError("NIT no puede ser None para cálculo de DV")
    nit_digits = ''.join(str(nit).strip().split())
    if not nit_digits.isdigit():
        raise ValueError("NIT debe ser numérico para cálculo de DV")

    # Pesos DIAN aplicados de derecha a izquierda
    weights_right = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    # Alinear desde el final del NIT con el inicio de la lista (3,7,13,...)
    total = 0
    nit_reversed = nit_digits[::-1]
    for i, ch in enumerate(nit_reversed):
        if i >= len(weights_right):
            # Si el NIT tiene más de 15 dígitos, continuar sin peso adicional (no usual)
            w = 0
        else:
            w = weights_right[i]
        total += int(ch) * w

    remainder = total % 11
    dv = remainder if remainder in (0, 1) else 11 - remainder
    return int(dv)


def build_factus_payload(invoice: Invoice):
    """
    Construye el diccionario de datos para la API Factus,
    usando los modelos existentes de Cliente y Régimen.
    """
    Customer = apps.get_model('service_requests', 'Customer')
    InvoiceIssuer = apps.get_model('service_requests', 'InvoiceIssuer')
    
    try:
        customer = Customer.objects.select_related('type_document_id', 'tax_regime', 'person_type').get(pk=invoice.customer_id)
    except Customer.DoesNotExist:
        raise ValueError("Cliente no encontrado para la factura.")
    
    try:
        issuer = InvoiceIssuer.objects.get(id_invoice_issuer=1)
    except InvoiceIssuer.DoesNotExist:
        raise ValueError("No se encontró el emisor predeterminado en la db.")

    # Validación de campos requeridos del cliente
    required_fields = {
        'type_document_id': 'Tipo de documento',
        'document_number': 'Número de documento',
        'tax_regime_id': 'Régimen tributario',
        'person_type_id': 'Tipo de persona',
        'id_municipality': 'Municipio',
        'address': 'Dirección',
        'email': 'Correo electrónico',
        'phone': 'Teléfono'
    }

    missing_fields = []
    for field, label in required_fields.items():
        if not getattr(customer, field):
            missing_fields.append(label)

    if missing_fields:
        raise ValueError(f"Faltan campos requeridos del cliente: {', '.join(missing_fields)}")

    if not customer.type_document_id or not hasattr(customer.type_document_id, 'id_document_type'):
        raise ValueError("El tipo de documento del cliente es inválido o no está configurado")

    lines = invoice.lines.all()
    if not lines.exists():
        raise ValueError("La factura debe tener al menos una línea de servicio.")

    # 1. Mapeo de ITEMS
    factus_items = []
    for line in lines:
        is_excluded = 1 if float(line.percentage_taxes_per_line) == 0.0 else 0 
        
        # Precio base (sin IVA) desde BD
        base_price = float(line.price_unit)
        
        if not is_excluded and float(line.percentage_taxes_per_line) > 0:
            tax_rate = float(line.percentage_taxes_per_line)
            price_with_tax = base_price * (1 + tax_rate / 100)
        else:
            price_with_tax = base_price
        
        factus_items.append({
            "code_reference": line.code_reference,
            "name": line.service_name,
            "quantity": float(line.quantity),
            "discount_rate": float(line.discount_percentage),
            "price": round(price_with_tax, 2),
            "tax_rate": f"{float(line.percentage_taxes_per_line):.2f}",
            "unit_measure_id": line.units_measurement_id,
            "standard_code_id": 1,
            "is_excluded": is_excluded,
            "tribute_id": line.tribute_id,
            "withholding_taxes": (line.withholding_taxes or [])
        })

    is_legal = str(customer.person_type_id) == '1'
    customer_names = customer.name if not is_legal else customer.legal_entity_name

    payment_method_code = str(getattr(invoice, 'payment_method_id', None) or '10')

    # Determinar DV confiable SOLO para NIT: si falta o es distinto al calculado, usar el calculado
    dv_final = None  # tipo int cuando disponible
    # Detectar si el tipo de documento del cliente corresponde a NIT
    doc_name = None
    try:
        doc_name = (getattr(customer.type_document_id, 'name', None) or '').strip()
    except Exception:
        doc_name = ''
    is_nit_doc = isinstance(doc_name, str) and 'NIT' in doc_name.upper()
    try:
        if is_nit_doc:
            dv_calculated = _compute_dv_for_nit(str(customer.document_number))  # int
            provided_raw = getattr(customer, 'check_digit', None)
            provided_dv = int(str(provided_raw)) if (provided_raw is not None and str(provided_raw).isdigit()) else None
            if provided_dv is not None and provided_dv == dv_calculated:
                dv_final = provided_dv
            else:
                dv_final = dv_calculated
                logger.info(
                    f"[DV] Usando DV calculado={dv_final} (suministrado={provided_dv}). Cliente id={customer.pk}"
                )
    except Exception as e:
        # Si no se puede calcular, dejar el suministrado si es numérico; si no, None
        if is_nit_doc:
            provided = getattr(customer, 'check_digit', None)
            if provided is not None and str(provided).isdigit():
                dv_final = int(str(provided))
            else:
                dv_final = None
            logger.warning(f"[DV] No fue posible calcular DV para NIT '{customer.document_number}': {e}")

    payload = {
        "document": "01",
        "numbering_range_id": 8, 
        "reference_code": invoice.reference_code,
        "observation": invoice.observation or "",
        "payment_method_code": payment_method_code, 

        "establishment": {
            "name": issuer.issuer_name,
            "address": issuer.issuer_address,
            "phone_number": issuer.issuer_phone,
            "email": issuer.issuer_email,
            "municipality_id": issuer.issuer_municipality
        },
        "customer": {
            "identification": str(customer.document_number),
            # Incluir 'dv' solo cuando es NIT y hay valor numérico
            **({"dv": dv_final} if (is_nit_doc and dv_final is not None) else {}),
            "company": customer.legal_entity_name if is_legal else '',
            "trade_name": customer.bussiness_name or '',
            "names": customer_names,
            "address": customer.address,
            "email": customer.email,
            "phone": customer.phone,
            "legal_organization_id": customer.person_type_id,
            "tribute_id": customer.tax_regime_id,
            "identification_document_id": customer.type_document_id.id_document_type, 
            "municipality_id": str(customer.id_municipality)
        },
        
        "items": factus_items,
    }

    # Construir allowance_charges (si existen)
    allowance_charges_list = []
    api_resp = invoice.api_response or {}
    stored_allowances = api_resp.get('allowance_charges', [])
    
    if stored_allowances and isinstance(stored_allowances, list):
        for ac in stored_allowances:
            allowance_charges_list.append({
                "concept_type": ac.get("concept_type", "03"),
                "is_surcharge": ac.get("is_surcharge", True),
                "reason": ac.get("reason", ""),
                "base_amount": ac.get("base_amount", "0.00"),
                "amount": ac.get("amount", "0.00")
            })
    
    if allowance_charges_list:
        payload["allowance_charges"] = allowance_charges_list
    
    return payload