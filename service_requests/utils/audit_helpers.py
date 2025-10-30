from typing import Any, Dict, Optional, Tuple, Union
from django.utils import timezone

def service_snapshot(service_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para el modelo Service.
    Devuelve solo primitivos: ids, strings, números, booleans o None.
    """
    if not service_obj:
        return {}
        
    return {
        'id_service': getattr(service_obj, 'id_service', None),
        'service_name': getattr(service_obj, 'service_name', None),
        'description': getattr(service_obj, 'description', None),
        'service_type_id': getattr(service_obj.service_type, 'id_types', None) if hasattr(service_obj, 'service_type') and service_obj.service_type else None,
        'base_price': float(getattr(service_obj, 'base_price', 0)),
        'price_unit_id': getattr(service_obj.price_unit, 'id_units', None) if hasattr(service_obj, 'price_unit') and service_obj.price_unit else None,
        'applicable_tax': getattr(service_obj, 'applicable_tax', None),
        'tax_rate': float(getattr(service_obj, 'tax_rate', 0)) if getattr(service_obj, 'tax_rate', None) is not None else None,
        'is_vat_exempt': bool(getattr(service_obj, 'is_vat_exempt', False)),
        'service_status_id': getattr(service_obj.service_status, 'id_statues', None) if hasattr(service_obj, 'service_status') and service_obj.service_status else None,
        'creation_date': getattr(service_obj, 'creation_date', None).isoformat() if getattr(service_obj, 'creation_date', None) else None,
        'modification_date': getattr(service_obj, 'modification_date', None).isoformat() if getattr(service_obj, 'modification_date', None) else None,
        'id_responsible_user_id': getattr(service_obj.id_responsible_user, 'id_user', None) if hasattr(service_obj, 'id_responsible_user') and service_obj.id_responsible_user else None,
    }


def _get_user_id(obj) -> Optional[int]:
    """
    Obtiene el ID de usuario de diferentes maneras posibles.
    Maneja los casos:
    1. id_user como campo directo
    2. id_user_id como foreign key
    3. id_user como objeto User
    """
    # Caso 1: id_user es un entero o None
    if hasattr(obj, 'id_user'):
        user = getattr(obj, 'id_user', None)
        if user is None:
            return None
        if isinstance(user, int):
            return user
        if hasattr(user, 'id'):  # Es un objeto User
            return getattr(user, 'id')
    
    # Caso 2: id_user_id (foreign key)
    if hasattr(obj, 'id_user_id'):
        return getattr(obj, 'id_user_id', None)
    
    # Caso 3: Buscar en el diccionario si es que es un dict
    if isinstance(obj, dict):
        if 'id_user' in obj:
            user = obj['id_user']
            if user is None:
                return None
            if isinstance(user, int):
                return user
            if hasattr(user, 'id'):
                return getattr(user, 'id')
        return obj.get('id_user_id')
    
    return None

def get_actor_info(current_user: Any) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extrae actor_id, actor_name y actor_role_name del usuario autenticado,
    asegurando compatibilidad con distintos tipos de user (objeto JWTUser, dict, etc.).
    """
    if not current_user:
        return "Sistema", "Sistema", "Sistema"

    # actor_id
    actor_id = None
    if hasattr(current_user, "id"):
        actor_id = str(getattr(current_user, "id", "")) or "Sistema"
    elif isinstance(current_user, dict):
        actor_id = str(current_user.get("id", "")) or "Sistema"
    else:
        actor_id = "Sistema"

    # actor_name — revisamos varios lugares
    actor_name = "Sistema"
    if hasattr(current_user, "name") and getattr(current_user, "name"):
        actor_name = str(getattr(current_user, "name"))
    elif hasattr(current_user, "username") and getattr(current_user, "username"):
        actor_name = str(getattr(current_user, "username"))
    elif hasattr(current_user, "email") and getattr(current_user, "email"):
        actor_name = str(getattr(current_user, "email"))
    elif hasattr(current_user, "_request") and hasattr(current_user._request, "auth"):
        auth = current_user._request.auth or {}
        actor_name = str(auth.get("name") or auth.get("username") or "Sistema")
    elif isinstance(current_user, dict):
        actor_name = str(current_user.get("name") or current_user.get("username") or "Sistema")

    # actor_role
    role_name = "Usuario"
    if hasattr(current_user, "_request") and hasattr(current_user._request, "auth"):
        auth = current_user._request.auth or {}
        roles = auth.get("rol") or auth.get("roles") or []
        if roles and isinstance(roles, list) and len(roles) > 0:
            role = roles[0]
            if isinstance(role, dict):
                role_name = str(role.get("name", "Usuario"))
    
    return str(actor_id), str(actor_name), str(role_name)


def customer_snapshot(customer_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para el modelo Customer.
    Devuelve solo primitivos: ids, strings, números, booleans o None.
    """
    def _safe_get(o, attr, default=None):
        try:
            # dict-like first
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(customer_obj, attr)
        if val is None:
            return None
        # Si ya es primitivo
        if isinstance(val, (int, float, str, bool)):
            return val
        # Si es dict con id/pk/name
        if isinstance(val, dict):
            return val.get("id") or val.get("pk") or val.get("name") or None
        # Instancia Django u objeto con id/pk
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        # Si tiene nombre
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        # Fallback seguro
        return None

    return {
        "id_customer": _safe_get(customer_obj, "id_customer") or _safe_get(customer_obj, "id") or _safe_get(customer_obj, "pk"),
        "document_number": _safe_get(customer_obj, "document_number"),
        "type_document_id": serialize_attr("type_document_id"),
        "check_digit": _safe_get(customer_obj, "check_digit"),
        "person_type": serialize_attr("person_type"),
        "legal_entity_name": _safe_get(customer_obj, "legal_entity_name"),
        "name": _safe_get(customer_obj, "name"),
        "first_last_name": _safe_get(customer_obj, "first_last_name"),
        "second_last_name": _safe_get(customer_obj, "second_last_name"),
        "email": _safe_get(customer_obj, "email"),
        "phone": _safe_get(customer_obj, "phone"),
        "address": _safe_get(customer_obj, "address"),
        "id_municipality": _safe_get(customer_obj, "id_municipality"),
        "tax_regime": serialize_attr("tax_regime"),
        "customer_statues": serialize_attr("customer_statues"),
        "id_responsible_user": serialize_attr("id_responsible_user"),
        # id_user puede venir de diferentes maneras
        "id_user": _get_user_id(customer_obj),
    }


def service_request_snapshot(service_request_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para el modelo ServiceRequest.
    Devuelve solo primitivos: ids, strings, números, booleans o None.
    """
    def _safe_get(o, attr, default=None):
        try:
            # dict-like first
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    if not service_request_obj:
        return {}
    
    return {
        'id_request': _safe_get(service_request_obj, 'id_request'),
        'customer_id': _safe_get(service_request_obj.customer, 'id_customer') if hasattr(service_request_obj, 'customer') and service_request_obj.customer else None,
        'request_detail': _safe_get(service_request_obj, 'request_detail'),
        'scheduled_start_date': _safe_get(service_request_obj, 'scheduled_start_date').isoformat() if _safe_get(service_request_obj, 'scheduled_start_date') else None,
        'scheduled_end_date': _safe_get(service_request_obj, 'scheduled_end_date').isoformat() if _safe_get(service_request_obj, 'scheduled_end_date') else None,
        'request_status_id': _safe_get(service_request_obj.request_status, 'id_statues') if hasattr(service_request_obj, 'request_status') and service_request_obj.request_status else None,
        'creation_date': _safe_get(service_request_obj, 'creation_date', timezone.now()).isoformat(),
        'modification_date': _safe_get(service_request_obj, 'modification_date', timezone.now()).isoformat(),
        'id_responsible_user': _safe_get(service_request_obj, 'id_responsible_user_id') if hasattr(service_request_obj, 'id_responsible_user_id') else (
            _safe_get(service_request_obj.id_responsible_user, 'id_user') if hasattr(service_request_obj, 'id_responsible_user') and service_request_obj.id_responsible_user else None
        ),
        'payment_method': _safe_get(service_request_obj, 'payment_method_id') if hasattr(service_request_obj, 'payment_method_id') else (
            _safe_get(service_request_obj.payment_method, 'id_payment_method') if hasattr(service_request_obj, 'payment_method') and service_request_obj.payment_method else None
        ),
        'payment_status_id': _safe_get(service_request_obj, 'payment_status_id') if hasattr(service_request_obj, 'payment_status_id') else (
            _safe_get(service_request_obj.payment_status, 'id_statues') if hasattr(service_request_obj, 'payment_status') and service_request_obj.payment_status else None
        ),
        'amount_paid': float(_safe_get(service_request_obj, 'amount_paid')) if _safe_get(service_request_obj, 'amount_paid') is not None else None,
        'currency_unit_amount_paid': _safe_get(service_request_obj, 'currency_unit_amount_paid_id') if hasattr(service_request_obj, 'currency_unit_amount_paid_id') else (
            _safe_get(service_request_obj.currency_unit_amount_paid, 'id_units') if hasattr(service_request_obj, 'currency_unit_amount_paid') and service_request_obj.currency_unit_amount_paid else None
        ),
        'amount_to_pay': float(_safe_get(service_request_obj, 'amount_to_pay')) if _safe_get(service_request_obj, 'amount_to_pay') is not None else None,
        'currency_unit_amount_to_pay': _safe_get(service_request_obj, 'currency_unit_amount_to_pay_id') if hasattr(service_request_obj, 'currency_unit_amount_to_pay_id') else (
            _safe_get(service_request_obj.currency_unit_amount_to_pay, 'id_units') if hasattr(service_request_obj, 'currency_unit_amount_to_pay') and service_request_obj.currency_unit_amount_to_pay else None
        ),
        'confirmation_datetime': _safe_get(service_request_obj, 'confirmation_datetime').isoformat() if _safe_get(service_request_obj, 'confirmation_datetime') else None,
        'confirmation_user_id': _safe_get(service_request_obj, 'confirmation_user_id') if hasattr(service_request_obj, 'confirmation_user_id') else (
            _safe_get(service_request_obj.confirmation_user, 'id_user') if hasattr(service_request_obj, 'confirmation_user') and service_request_obj.confirmation_user else None
        ),
    }


def service_request_related_models_snapshot(service_request_obj) -> Dict[str, Any]:
    """
    Crea un snapshot de los modelos relacionados con una solicitud de servicio.
    Incluye location y machinery_users.
    """
    if not service_request_obj:
        return {}
    
    snapshot = {
        'location': None,
        'machinery_users': []
    }
    
    # Snapshot de la ubicación si existe
    if hasattr(service_request_obj, 'request_location') and service_request_obj.request_location:
        loc = service_request_obj.request_location
        location_data = {
            'id_request_location': loc.id_request_location,
            'latitude': float(loc.latitude) if loc.latitude is not None else None,
            'longitude': float(loc.longitude) if loc.longitude is not None else None,
            'place_name': loc.place_name,
            'country': loc.country,
            'department': loc.department,
            'city_id': loc.city_id,
            'area': float(loc.area) if loc.area is not None else None,
            'area_unit_id': loc.area_unit_id,
            'altitude': float(loc.altitude) if loc.altitude is not None else None,
            'altitude_unit_id': loc.altitude_unit_id
        }
        snapshot['location'] = {k: v for k, v in location_data.items() if v is not None}
    
    # Snapshot de las máquinas y operarios asignados
    if hasattr(service_request_obj, 'machinery_users') and service_request_obj.machinery_users.exists():
        for mu in service_request_obj.machinery_users.all():
            snapshot['machinery_users'].append({
                'id_request_machinery_user': mu.id_request_machinery_user,
                'machinery_id': mu.machinery_id,
                'user_id': mu.user_id,
                'soil_type': mu.soil_type_id,
                'texture': mu.texture_id,
                'humidity_level': float(mu.humidity_level) if mu.humidity_level is not None else None,
                'implementation': mu.implementation_id,
                'depth': float(mu.depth) if mu.depth is not None else None,
                'slope': float(mu.slope) if mu.slope is not None else None,
                'work_duration': float(mu.work_duration) if mu.work_duration is not None else None
            })
    
    return snapshot


def service_request_cancel_snapshot(service_request_obj, machinery_statuses: Optional[list] = None) -> Dict[str, Any]:
    """
    Snapshot específico para cancelación de solicitudes.
    Incluye datos de cancelación y el estado de las maquinarias luego de cancelar.

    Parameters:
    - service_request_obj: instancia de ServiceRequest ya actualizada a estado cancelado (23)
    - machinery_statuses: lista de dicts con info de maquinaria, ejemplo:
        [{
            'id_machinery': 1,
            'machinery_operational_status_id': 4
        }, ...]
      Si no se provee, se deja en [].
    """
    if not service_request_obj:
        return {}

    def _safe_get(o, attr, default=None):
        try:
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    machinery_statuses = machinery_statuses or []

    return {
        'id_request': _safe_get(service_request_obj, 'id_request'),
        'request_status_id': _safe_get(service_request_obj.request_status, 'id_statues') if hasattr(service_request_obj, 'request_status') and service_request_obj.request_status else None,
        'completion_cancellation_observations': _safe_get(service_request_obj, 'completion_cancellation_observations'),
        'completion_cancellation_datetime': _safe_get(service_request_obj, 'completion_cancellation_datetime').isoformat() if _safe_get(service_request_obj, 'completion_cancellation_datetime') else None,
        'completion_cancellation_user_id': _safe_get(service_request_obj.completion_cancellation_user, 'id_user') if hasattr(service_request_obj, 'completion_cancellation_user') and service_request_obj.completion_cancellation_user else None,
        'machinery_statuses': machinery_statuses,
    }

def invoice_snapshot(invoice_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y serializable en JSON para el modelo Invoice.
    Devuelve solo valores primitivos o None.
    """
    if not invoice_obj:
        return {}

    def _safe_get(obj, attr, default=None):
        try:
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)
        except Exception:
            return default

    def serialize_attr(attr):
        val = _safe_get(invoice_obj, attr)
        if val is None:
            return None
        if isinstance(val, (int, float, str, bool)):
            return val
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "pk"):
            return getattr(val, "pk", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return str(val)

    return {
        "id_invoice": _safe_get(invoice_obj, "id_invoice"),
        "reference_code": _safe_get(invoice_obj, "reference_code"),
        "invoice_number": _safe_get(invoice_obj, "invoice_number"),
        "invoice_date": str(_safe_get(invoice_obj, "invoice_date")),
        "cufe": _safe_get(invoice_obj, "cufe"),
        "status": serialize_attr("status"),
        "customer": serialize_attr("customer"),
        "tax_regime": serialize_attr("tax_regime"),
        "service_request": serialize_attr("service_request"),
        "payment_method": serialize_attr("payment_method"),
        "amount_to_pay": float(_safe_get(invoice_obj, "amount_to_pay") or 0.0),
        "total_without_taxes": float(_safe_get(invoice_obj, "total_without_taxes") or 0.0),
        "total_taxes": float(_safe_get(invoice_obj, "total_taxes") or 0.0),
        "total_withholding_taxes": float(_safe_get(invoice_obj, "total_withholding_taxes") or 0.0),
        "invoice_pdf_url": _safe_get(invoice_obj, "invoice_pdf_url"),
        "invoice_xml_url": _safe_get(invoice_obj, "invoice_xml_url"),
        "created_at": str(_safe_get(invoice_obj, "created_at")),
        "sent_at": str(_safe_get(invoice_obj, "sent_at")),
        "modification_date": _safe_get(invoice_obj, 'modification_date', timezone.now()).isoformat()
    }