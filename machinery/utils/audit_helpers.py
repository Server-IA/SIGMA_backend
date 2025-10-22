from typing import Any, Dict, List, Optional, Tuple
import logging


def pick_primary_role_and_ids_from_current_user(current_user: Dict[str, Any]) -> Tuple[Optional[str], List[int]]:
    """
    Devuelve (actor_role_principal, lista_ids_roles) usando payload del JWT.
    """
    roles = current_user.get("rol", []) or []
    if not roles:
        return None, []
    admin = next((r for r in roles if (r.get("name") or "").strip().lower() == "administrador"), None)
    primary = (admin.get("name") if admin else roles[0].get("name")) if roles else None
    ids = [int(r["id"]) for r in roles if "id" in r]
    return primary, ids

def get_actor_info(current_user: Any) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extrae actor_id, actor_name y actor_role_name del usuario autenticado,
    asegurando compatibilidad con distintos tipos de user (objeto JWTUser, dict, etc.).
    """

    if not current_user:
        return None, None, None

    # actor_id
    actor_id = None
    if hasattr(current_user, "id"):
        actor_id = str(getattr(current_user, "id", None))
    elif isinstance(current_user, dict):
        actor_id = str(current_user.get("id"))

    # actor_name — revisamos varios lugares
    actor_name = None
    if hasattr(current_user, "name"):
        actor_name = getattr(current_user, "name", None)
    elif hasattr(current_user, "username"):
        actor_name = getattr(current_user, "username", None)
    elif hasattr(current_user, "payload") and isinstance(current_user.payload, dict):
        actor_name = current_user.payload.get("name") or current_user.payload.get("username")
    elif isinstance(current_user, dict):
        actor_name = current_user.get("name") or current_user.get("username")

    # Construcción de user_data para roles
    user_data = {}
    if hasattr(current_user, "__dict__"):
        user_data = current_user.__dict__

    if hasattr(current_user, "roles"):
        user_data["rol"] = current_user.roles
    elif hasattr(current_user, "payload") and isinstance(current_user.payload, dict):
        user_data["rol"] = current_user.payload.get("rol", [])
    elif isinstance(current_user, dict):
        user_data = current_user

    # actor_role_name
    actor_role_name, _ = pick_primary_role_and_ids_from_current_user(user_data)

    if not actor_role_name:
        logging.warning("Usuario autenticado pero sin rol detectado.")
    if not actor_name:
        logging.warning("Usuario autenticado pero sin name detectado.")

    return actor_id, actor_name, actor_role_name

# Machinery snapshot (1)
def machinery_snapshot(mach_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    responsible_user = _safe_get(mach_obj, "responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    def serialize_attr(attr):
        val = _safe_get(mach_obj, attr)
        if hasattr(val, "id"):
            return getattr(val, "id", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return val

    return {
        "id_machinery": (
            _safe_get(mach_obj, "id_machinery")
            or _safe_get(mach_obj, "id")
            or _safe_get(mach_obj, "pk")
        ),
        "machinery_name": _safe_get(mach_obj, "machinery_name"),
        "serial_number": _safe_get(mach_obj, "serial_number"),
        "machinery_type": serialize_attr("machinery_type"),
        "id_model": serialize_attr("id_model"),
        "machinery_secondary_type": serialize_attr("machinery_secondary_type"),
        "responsible_user": str(responsible_id) if responsible_id else None,
        "manufacturing_year": _safe_get(mach_obj, "manufacturing_year"),
        "tariff_subheading": _safe_get(mach_obj, "tariff_subheading"),
        "image_path": _safe_get(mach_obj, "image_path"),
    }

# Machinery tracker snapshot (2)
def machinery_tracker_snapshot(tracker_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(tracker_obj, attr)
        if val is None:
            return None
        # Si ya es primitivo
        if isinstance(val, (int, str, float)):
            return val
        # Si es modelo Django u objeto con id/pk
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        # Si tiene nombre
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        # Fallback seguro
        return None

    responsible_user = _safe_get(tracker_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_tracker_sheet": (
            _safe_get(tracker_obj, "id_tracker_sheet")
            or _safe_get(tracker_obj, "id")
            or _safe_get(tracker_obj, "pk")
        ),
        "id_machinery": serialize_attr("id_machinery"),
        "terminal_serial_number": _safe_get(tracker_obj, "terminal_serial_number"),
        "gps_serial_number": _safe_get(tracker_obj, "gps_serial_number"),
        "chassis_number": _safe_get(tracker_obj, "chassis_number"),
        "engine_number": _safe_get(tracker_obj, "engine_number"),
        "registration_date": str(_safe_get(tracker_obj, "registration_date")),
        "modification_date": str(_safe_get(tracker_obj, "modification_date")),
        "responsible_user": str(responsible_id) if responsible_id else None,
        "justification": _safe_get(tracker_obj, "justification"),
    }

# Machinery technical sheet snapshot (3)
def specific_technical_snapshot(tech_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(tech_obj, attr)
        if val is None:
            return None
        # Si ya es primitivo
        if isinstance(val, (int, str, float)):
            return val
        # Si es modelo Django u objeto con id/pk
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        # Si tiene nombre
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        # Fallback seguro
        return None

    responsible_user = _safe_get(tech_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_specific_technical_sheet": (
            _safe_get(tech_obj, "id_specific_technical_sheet")
            or _safe_get(tech_obj, "id")
            or _safe_get(tech_obj, "pk")
        ),
        "id_machinery": serialize_attr("id_machinery"),

        # Motor y transmisión
        "power": _safe_get(tech_obj, "power"),
        "power_unit": serialize_attr("power_unit"),
        "engine_type": serialize_attr("engine_type"),
        "cylinder_capacity": _safe_get(tech_obj, "cylinder_capacity"),
        "cylinder_capacity_unit": serialize_attr("cylinder_capacity_unit"),
        "cylinder_arrangement_type": serialize_attr("cylinder_arrangement_type"),
        "cylinder_count": _safe_get(tech_obj, "cylinder_count"),
        "traction_type": serialize_attr("traction_type"),
        "fuel_consumption": _safe_get(tech_obj, "fuel_consumption"),
        "fuel_consumption_unit": serialize_attr("fuel_consumption_unit"),
        "transmission_system_type": serialize_attr("transmission_system_type"),

        # Capacidad y rendimiento
        "fuel_capacity": _safe_get(tech_obj, "fuel_capacity"),
        "fuel_capacity_unit": serialize_attr("fuel_capacity_unit"),
        "carrying_capacity": _safe_get(tech_obj, "carrying_capacity"),
        "carrying_capacity_unit": serialize_attr("carrying_capacity_unit"),
        "operating_weight": _safe_get(tech_obj, "operating_weight"),
        "operating_weight_unit": serialize_attr("operating_weight_unit"),
        "max_speed": _safe_get(tech_obj, "max_speed"),
        "max_speed_unit": serialize_attr("max_speed_unit"),
        "draft_force": _safe_get(tech_obj, "draft_force"),
        "draft_force_unit": serialize_attr("draft_force_unit"),
        "maximum_altitude": _safe_get(tech_obj, "maximum_altitude"),
        "maximum_altitude_unit": serialize_attr("maximum_altitude_unit"),
        "minimum_performance": _safe_get(tech_obj, "minimum_performance"),
        "maximum_performance": _safe_get(tech_obj, "maximum_performance"),
        "performance_unit": serialize_attr("performance_unit"),

        # Dimensiones y peso
        "width": _safe_get(tech_obj, "width"),
        "length": _safe_get(tech_obj, "length"),
        "height": _safe_get(tech_obj, "height"),
        "dimension_unit": serialize_attr("dimension_unit"),
        "net_weight": _safe_get(tech_obj, "net_weight"),
        "net_weight_unit": serialize_attr("net_weight_unit"),

        # Sistemas auxiliares e hidráulicos
        "air_conditioning_system_type": serialize_attr("air_conditioning_system_type"),
        "air_conditioning_system_consumption": _safe_get(tech_obj, "air_conditioning_system_consumption"),
        "air_conditioning_system_consumption_unit": serialize_attr("air_conditioning_system_consumption_unit"),
        "maximum_working_pressure": _safe_get(tech_obj, "maximum_working_pressure"),
        "maximum_working_pressure_unit": serialize_attr("maximum_working_pressure_unit"),
        "pump_flow": _safe_get(tech_obj, "pump_flow"),
        "pump_flow_unit": serialize_attr("pump_flow_unit"),
        "hydraulic_tank_capacity": _safe_get(tech_obj, "hydraulic_tank_capacity"),
        "hydraulic_tank_capacity_unit": serialize_attr("hydraulic_tank_capacity_unit"),

        # Normatividad y seguridad
        "emission_level_type": serialize_attr("emission_level_type"),
        "cabin_type": serialize_attr("cabin_type"),

        # Fechas y usuario responsable
        "registration_date": str(_safe_get(tech_obj, "registration_date")),
        "modification_date": str(_safe_get(tech_obj, "modification_date")),
        "responsible_user": str(responsible_id) if responsible_id else None,
        "justification": _safe_get(tech_obj, "justification"),
    }

# Machinery usage snapshot (4)
def machinery_usage_snapshot(usage_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(usage_obj, attr)
        if val is None:
            return None
        # Si ya es primitivo
        if isinstance(val, (int, str, float, bool)):
            return val
        # Si es modelo Django u objeto con id/pk
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        # Si tiene nombre
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        # Fallback seguro
        return None

    responsible_user = _safe_get(usage_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_usage_sheet": (
            _safe_get(usage_obj, "id_usage_sheet")
            or _safe_get(usage_obj, "id")
            or _safe_get(usage_obj, "pk")
        ),
        "id_machinery": serialize_attr("id_machinery"),

        # Fechas / valores
        "acquisition_date": str(_safe_get(usage_obj, "acquisition_date")),
        "usage_condition": serialize_attr("usage_condition"),
        # usage_hours y distance_value: si vienen como Decimal los dejamos como str para no perder precisión
        "usage_hours": (
            str(_safe_get(usage_obj, "usage_hours")) if _safe_get(usage_obj, "usage_hours") is not None else None
        ),
        "distance_value": (
            str(_safe_get(usage_obj, "distance_value")) if _safe_get(usage_obj, "distance_value") is not None else None
        ),
        "distance_unit": serialize_attr("distance_unit"),

        "tenancy_type": serialize_attr("tenancy_type"),
        "is_own": bool(_safe_get(usage_obj, "is_own")) if _safe_get(usage_obj, "is_own") is not None else False,
        "contract_end_date": str(_safe_get(usage_obj, "contract_end_date")),

        # registro y metadatos
        "registration_date": str(_safe_get(usage_obj, "registration_date")),
        "modification_date": str(_safe_get(usage_obj, "modification_date")),
        "responsible_user": str(responsible_id) if responsible_id else None,
        "justification": _safe_get(usage_obj, "justification"),
    }

# Machinery documentation snapshot (5)
def machinery_documentation_snapshot(doc_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(doc_obj, attr)
        if val is None:
            return None
        # Si ya es primitivo
        if isinstance(val, (int, str, float)):
            return val
        # Si es modelo Django u objeto con id/pk
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        # Si tiene nombre
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        # Fallback seguro
        return None

    responsible_user = _safe_get(doc_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_machinery_documentation": (
            _safe_get(doc_obj, "id_machinery_documentation")
            or _safe_get(doc_obj, "id")
            or _safe_get(doc_obj, "pk")
        ),
        "id_machinery": serialize_attr("id_machinery"),
        "document": _safe_get(doc_obj, "document"),
        "path": _safe_get(doc_obj, "path"),
        "creation_date": str(_safe_get(doc_obj, "creation_date")),
        "responsible_user": str(responsible_id) if responsible_id else None,
        "justification": _safe_get(doc_obj, "justification"),
    }

# Machinery periodic maintenance snapshot (6)
def periodic_maintenance_snapshot(pm_obj) -> Dict[str, Any]:
    """
    Snapshot ligero de PeriodicMaintenanceScheduling.
    Devuelve solo primitivos: ids, strings, números o None.
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
        val = _safe_get(pm_obj, attr)
        if val is None:
            return None
        # primitivos pasados tal cual
        if isinstance(val, (int, float, str, bool)):
            return val
        # modelo Django u objeto con id/pk
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        # si tiene nombre
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        # fallback seguro
        return None

    return {
        "id_periodic_maintenance_scheduling": (
            _safe_get(pm_obj, "id_periodic_maintenance_scheduling")
            or _safe_get(pm_obj, "id")
            or _safe_get(pm_obj, "pk")
        ),
        "machinery": serialize_attr("machinery"),
        "maintenance": serialize_attr("maintenance"),
        # trigger alternatives (one of these will be not-None per constraint)
        "usage_hours": _safe_get(pm_obj, "usage_hours"),
        "distance_km": _safe_get(pm_obj, "distance_km"),
    }

def build_meta_with_machinery_id(
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    base_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Construye un meta que siempre incluye id_machinery si existe
    en el snapshot before/after.
    """
    meta = dict(base_meta or {})

    def extract(snapshot: Optional[Dict[str, Any]]) -> Optional[int]:
        if not snapshot:
            return None
        return snapshot.get("id_machinery")

    mach_id = extract(after) or extract(before)
    if mach_id is not None:
        meta["id_machinery"] = mach_id

    return meta

def telemetry_devices_snapshot(device_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(device_obj, attr)
        if val is None:
            return None
        if isinstance(val, (int, str, float)):
            return val
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return None

    responsible_user = _safe_get(device_obj, "id_responsible_user")
    responsible_id = None
    if responsible_user is not None:
        responsible_id = getattr(responsible_user, "id", None) or getattr(responsible_user, "pk", None)

    return {
        "id_device": _safe_get(device_obj, "id_device") or _safe_get(device_obj, "id") or _safe_get(device_obj, "pk"),
        "name": _safe_get(device_obj, "name"),
        "IMEI": _safe_get(device_obj, "IMEI"),
        "id_statues": serialize_attr("id_statues"),
        "registration_date": str(_safe_get(device_obj, "registration_date")),
        "modification_date": str(_safe_get(device_obj, "modification_date")),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }

def telemetry_device_parameter_snapshot(param_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(param_obj, attr)
        if val is None:
            return None
        if isinstance(val, (int, str, float)):
            return val
        if hasattr(val, "id") or hasattr(val, "pk"):
            return getattr(val, "id", None) or getattr(val, "pk", None)
        if hasattr(val, "name"):
            return getattr(val, "name", None)
        return None

    return {
        "id": _safe_get(param_obj, "id") or _safe_get(param_obj, "pk"),
        "telemetry_device": serialize_attr("telemetry_device"),
        "parameter": serialize_attr("parameter"),
    }

# Telemetry device snapshot
def telemetry_device_snapshot_toggle(dev_obj) -> Dict[str, Any]:
    def _safe_get(o, attr, default=None):
        try:
            return getattr(o, attr, default)
        except Exception:
            return default

    def serialize_attr(attr: str):
        val = _safe_get(dev_obj, attr)
        if val is None:
            return None
        if isinstance(val, (int, float, str, bool)):
            return val
        try:
            if hasattr(val, "id") or hasattr(val, "pk"):
                return getattr(val, "id", None) or getattr(val, "pk", None)
            if hasattr(val, "name"):
                return getattr(val, "name", None)
        except Exception:
            pass
        return None

    responsible = _safe_get(dev_obj, "id_responsible_user")
    responsible_id = None
    if responsible is not None:
        responsible_id = getattr(responsible, "id", None) or getattr(responsible, "pk", None)

    return {
        "id_device": _safe_get(dev_obj, "id_device") or _safe_get(dev_obj, "id") or _safe_get(dev_obj, "pk"),
        "name": _safe_get(dev_obj, "name"),
        "status_id": serialize_attr("id_statues"),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
        "registration_date": str(_safe_get(dev_obj, "registration_date")),
        "modification_date": str(_safe_get(dev_obj, "modification_date")),
    }