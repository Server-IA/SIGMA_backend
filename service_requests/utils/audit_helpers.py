from typing import Any, Dict, Optional, Tuple, Union

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
        "tax_regime": _safe_get(customer_obj, "tax_regime"),
        "customer_statues": serialize_attr("customer_statues"),
        "id_responsible_user": serialize_attr("id_responsible_user"),
        # id_user puede venir de diferentes maneras
        "id_user": _get_user_id(customer_obj),
    }
