from typing import Any, Dict

def statues_category_snapshot(statues_category_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    responsible_user = _safe_get(statues_category_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    def serialize_attr(attr):
        val = _safe_get(statues_category_obj, attr)
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return val

    return {
        "id_statues_categories": (
            _safe_get(statues_category_obj, "id_statues_categories")
            or _safe_get(statues_category_obj, "id")
            or _safe_get(statues_category_obj, "pk")
        ),
        "name": _safe_get(statues_category_obj, "name"),
        "description": _safe_get(statues_category_obj, "description"),
        "modification_date": str(_safe_get(statues_category_obj, "modification_date")),
        "creation_date": str(_safe_get(statues_category_obj, "creation_date")),
        "responsible_user": str(responsible_id) if responsible_id else None,
    }


def statues_snapshot(statues_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para el modelo Statues.
    Devuelve sólo primitivos (ids, strings, números, booleans o None).
    """
    def _safe_get(o: Any, attr: str, default=None):
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(statues_obj, attr)
        if val is None:
            return None
        # primitivos tal cual
        if isinstance(val, (int, float, str, bool)):
            return val
        # dict-like
        if isinstance(val, dict):
            return val.get("id") or val.get("pk") or val.get("name") or None
        # instancia Django u objeto con id/pk o name
        try:
            if hasattr(val, "id") or hasattr(val, "pk"):
                return getattr(val, "id", None) or getattr(val, "pk", None)
            if hasattr(val, "name"):
                return getattr(val, "name", None)
        except Exception:
            pass
        return None

    responsible = _safe_get(statues_obj, "id_responsible_user")
    responsible_id = None
    if responsible is not None:
        responsible_id = getattr(responsible, "id", None) or getattr(responsible, "pk", None)

    return {
        "id_statues": (
            _safe_get(statues_obj, "id_statues")
            or _safe_get(statues_obj, "id")
            or _safe_get(statues_obj, "pk")
        ),
        "name": _safe_get(statues_obj, "name"),
        "description": _safe_get(statues_obj, "description"),
        "id_statues_categories": serialize_attr("id_statues_categories"),
        "modification_date": str(_safe_get(statues_obj, "modification_date")) if _safe_get(statues_obj, "modification_date") is not None else None,
        "creation_date": str(_safe_get(statues_obj, "creation_date")) if _safe_get(statues_obj, "creation_date") is not None else None,
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }


def types_category_snapshot(tc_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para TypesCategory.
    Devuelve sólo primitivos (ids, strings, números, booleans o None).
    """
    def _safe_get(o: Any, attr: str, default=None):
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(tc_obj, attr)
        if val is None:
            return None
        # primitivos tal cual
        if isinstance(val, (int, float, str, bool)):
            return val
        # dict-like
        if isinstance(val, dict):
            return val.get("id") or val.get("pk") or val.get("name") or None
        # instancia Django u objeto con id/pk o name
        try:
            if hasattr(val, "id") or hasattr(val, "pk"):
                return getattr(val, "id", None) or getattr(val, "pk", None)
            if hasattr(val, "name"):
                return getattr(val, "name", None)
        except Exception:
            pass
        return None

    responsible = _safe_get(tc_obj, "id_responsible_user")
    responsible_id = None
    if responsible is not None:
        responsible_id = getattr(responsible, "id", None) or getattr(responsible, "pk", None)

    return {
        "id_types_categories": (
            _safe_get(tc_obj, "id_types_categories")
            or _safe_get(tc_obj, "id")
            or _safe_get(tc_obj, "pk")
        ),
        "name": _safe_get(tc_obj, "name"),
        "description": _safe_get(tc_obj, "description"),
        "creation_date": str(_safe_get(tc_obj, "creation_date")) if _safe_get(tc_obj, "creation_date") is not None else None,
        "modification_date": str(_safe_get(tc_obj, "modification_date")) if _safe_get(tc_obj, "modification_date") is not None else None,
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }


def types_snapshot(t_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable del modelo Types.
    Devuelve sólo primitivos y valores seguros para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(t_obj, attr)
        if val is None:
            return None
        if isinstance(val, (int, float, str, bool)):
            return val
        if isinstance(val, dict):
            return val.get("id") or val.get("pk") or val.get("name")
        try:
            if hasattr(val, "id") or hasattr(val, "pk"):
                return getattr(val, "id", None) or getattr(val, "pk", None)
            if hasattr(val, "name"):
                return getattr(val, "name", None)
        except Exception:
            pass
        return None

    responsible = _safe_get(t_obj, "id_responsible_user")
    responsible_id = None
    if responsible is not None:
        responsible_id = getattr(responsible, "id", None) or getattr(responsible, "pk", None)

    return {
        "id_types": (
            _safe_get(t_obj, "id_types")
            or _safe_get(t_obj, "id")
            or _safe_get(t_obj, "pk")
        ),
        "name": _safe_get(t_obj, "name"),
        "description": _safe_get(t_obj, "description"),
        "id_types_categories": serialize_attr("id_types_categories"),
        "id_statues": serialize_attr("id_statues"),
        "creation_date": (
            _safe_get(t_obj, "creation_date").isoformat()
            if _safe_get(t_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(t_obj, "modification_date").isoformat()
            if _safe_get(t_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def brands_category_snapshot(bc_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo BrandsCategory para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    responsible_user = _safe_get(bc_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_brands_categories": (
            _safe_get(bc_obj, "id_brands_categories")
            or _safe_get(bc_obj, "id")
            or _safe_get(bc_obj, "pk")
        ),
        "name": _safe_get(bc_obj, "name"),
        "description": _safe_get(bc_obj, "description"),
        "creation_date": (
            _safe_get(bc_obj, "creation_date").isoformat()
            if _safe_get(bc_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(bc_obj, "modification_date").isoformat()
            if _safe_get(bc_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def brands_snapshot(brand_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo Brands para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    # Usuario responsable
    responsible_user = _safe_get(brand_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    # Serialización de atributos relacionales
    def serialize_attr(attr):
        val = _safe_get(brand_obj, attr)
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return val

    return {
        "id_brands": (
            _safe_get(brand_obj, "id_brands")
            or _safe_get(brand_obj, "id")
            or _safe_get(brand_obj, "pk")
        ),
        "name": _safe_get(brand_obj, "name"),
        "description": _safe_get(brand_obj, "description"),
        "id_brands_categories": serialize_attr("id_brands_categories"),
        "id_statues": serialize_attr("id_statues"),
        "creation_date": (
            _safe_get(brand_obj, "creation_date").isoformat()
            if _safe_get(brand_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(brand_obj, "modification_date").isoformat()
            if _safe_get(brand_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def models_snapshot(model_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo `Models` para auditoría.

    - Devuelve ids/primitivos (int/str) para FKs.
    - Asegura que exista la clave 'id_model' con un valor primitivo o None.
    - Protege contra objetos Django no serializables.
    """
    def _safe_get(o: Any, attr: str, default=None):
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    # Serializa relaciones a IDs/PKs (prioriza id -> pk)
    def serialize_to_id(val: Any):
        if val is None:
            return None
        # si ya es primitivo
        if isinstance(val, (int, float, str, bool)):
            return val
        # dict-like
        if isinstance(val, dict):
            return val.get("id") or val.get("pk") or val.get("id_model") or None
        # objeto Django u otro objeto con id/pk
        try:
            return getattr(val, "id", None) or getattr(val, "pk", None)
        except Exception:
            return None

    # usuario responsable (id)
    responsible_user = _safe_get(model_obj, "id_responsible_user")
    responsible_id = serialize_to_id(responsible_user)

    # construir snapshot
    creation = _safe_get(model_obj, "creation_date")
    modification = _safe_get(model_obj, "modification_date")

    return {
        # Identificador principal: siempre intentar devolver un primitivo usable
        "id_model": (
            _safe_get(model_obj, "id_model")
            or _safe_get(model_obj, "id")
            or _safe_get(model_obj, "pk")
            or None
        ),
        "name": _safe_get(model_obj, "name"),
        "description": _safe_get(model_obj, "description"),
        # FK -> devolver id/pk (no objeto, no name)
        "id_brand": serialize_to_id(_safe_get(model_obj, "id_brand")),
        "id_statues": serialize_to_id(_safe_get(model_obj, "id_statues")),
        "creation_date": (creation.isoformat() if creation is not None else None),
        "modification_date": (modification.isoformat() if modification is not None else None),
        "id_responsible_user": (str(responsible_id) if responsible_id is not None else None),
    }

def units_category_snapshot(unit_cat_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo UnitsCategory para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        """Obtiene un atributo de forma segura, manejando excepciones."""
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    # Usuario responsable
    responsible_user = _safe_get(unit_cat_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_units_categories": (
            _safe_get(unit_cat_obj, "id_units_categories")
            or _safe_get(unit_cat_obj, "id")
            or _safe_get(unit_cat_obj, "pk")
        ),
        "name": _safe_get(unit_cat_obj, "name"),
        "description": _safe_get(unit_cat_obj, "description"),
        "creation_date": (
            _safe_get(unit_cat_obj, "creation_date").isoformat()
            if _safe_get(unit_cat_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(unit_cat_obj, "modification_date").isoformat()
            if _safe_get(unit_cat_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def units_snapshot(unit_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo Units para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        """Obtiene un atributo de forma segura, evitando errores si el campo no existe."""
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    # Usuario responsable
    responsible_user = _safe_get(unit_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    # Función para serializar atributos relacionados (ForeignKeys)
    def serialize_attr(attr):
        val = _safe_get(unit_obj, attr)
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return val

    return {
        "id_units": (
            _safe_get(unit_obj, "id_units")
            or _safe_get(unit_obj, "id")
            or _safe_get(unit_obj, "pk")
        ),
        "name": _safe_get(unit_obj, "name"),
        "symbol": _safe_get(unit_obj, "symbol"),
        "id_units_categories": serialize_attr("id_units_categories"),
        "id_types": serialize_attr("id_types"),
        "id_statues": serialize_attr("id_statues"),
        "creation_date": (
            _safe_get(unit_obj, "creation_date").isoformat()
            if _safe_get(unit_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(unit_obj, "modification_date").isoformat()
            if _safe_get(unit_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def employee_department_snapshot(dept_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo EmployeeDepartment para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        """Obtiene un atributo de forma segura, evitando errores si el campo no existe."""
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    # Usuario responsable
    responsible_user = _safe_get(dept_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    # Serializador de relaciones
    def serialize_attr(attr):
        val = _safe_get(dept_obj, attr)
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return val

    return {
        "id_employee_department": (
            _safe_get(dept_obj, "id_employee_department")
            or _safe_get(dept_obj, "id")
            or _safe_get(dept_obj, "pk")
        ),
        "name": _safe_get(dept_obj, "name"),
        "description": _safe_get(dept_obj, "description"),
        "id_statues": serialize_attr("id_statues"),
        "creation_date": (
            _safe_get(dept_obj, "creation_date").isoformat()
            if _safe_get(dept_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(dept_obj, "modification_date").isoformat()
            if _safe_get(dept_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def employee_charge_snapshot(charge_obj) -> Dict[str, Any]:
    """
    Genera un snapshot JSON-serializable del modelo EmployeeCharge para auditoría.
    """
    def _safe_get(o: Any, attr: str, default=None):
        """Obtiene un atributo de forma segura, evitando errores si el campo no existe."""
        try:
            if o is None:
                return default
            if isinstance(o, dict):
                return o.get(attr, default)
            return getattr(o, attr, default)
        except Exception:
            return default

    # Usuario responsable
    responsible_user = _safe_get(charge_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    # Serializador de relaciones
    def serialize_attr(attr):
        val = _safe_get(charge_obj, attr)
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return val

    return {
        "id_employee_charge": (
            _safe_get(charge_obj, "id_employee_charge")
            or _safe_get(charge_obj, "id")
            or _safe_get(charge_obj, "pk")
        ),
        "name": _safe_get(charge_obj, "name"),
        "contract_prefix": _safe_get(charge_obj, "contract_prefix"),
        "description": _safe_get(charge_obj, "description"),
        "id_employee_department": serialize_attr("id_employee_department"),
        "id_statues": serialize_attr("id_statues"),
        "creation_date": (
            _safe_get(charge_obj, "creation_date").isoformat()
            if _safe_get(charge_obj, "creation_date") else None
        ),
        "modification_date": (
            _safe_get(charge_obj, "modification_date").isoformat()
            if _safe_get(charge_obj, "modification_date") else None
        ),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }