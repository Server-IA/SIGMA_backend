from typing import Any, Dict, List, Optional, Tuple
import logging

def maintenance_snapshot(maint_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para el modelo Maintenance.
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
        val = _safe_get(maint_obj, attr)
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

    responsible = _safe_get(maint_obj, "id_responsible_user")
    responsible_id = None
    if responsible is not None:
        responsible_id = getattr(responsible, "id", None) or getattr(responsible, "pk", None)

    return {
        "id_maintenance": (
            _safe_get(maint_obj, "id_maintenance")
            or _safe_get(maint_obj, "id")
            or _safe_get(maint_obj, "pk")
        ),
        "name": _safe_get(maint_obj, "name"),
        "description": _safe_get(maint_obj, "description"),
        "maintenance_type": serialize_attr("maintenance_type"),
        "maintenance_status": serialize_attr("maintenance_status"),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
        "registration_date": str(_safe_get(maint_obj, "registration_date")),
        "modification_date": str(_safe_get(maint_obj, "modification_date")),
    }

def maintenance_request_snapshot(instance) -> dict:
    """
    Genera un snapshot del estado de un MaintenanceRequest para auditoría.
    """
    if not instance:
        return {}

    return {
        "id_maintenance_request": instance.id_maintenance_request,
        "id_machinery": instance.id_machinery_id,
        "maintenance_type": instance.maintenance_type_id,
        "description": instance.description,
        "priority": instance.priority_id,
        "request_status": instance.request_status_id,
        "justification": instance.justification,
        "detected_at": (
            instance.detected_at.isoformat() if instance.detected_at else None
        ),
        "registration_date": (
            instance.registration_date.isoformat() if instance.registration_date else None
        ),
        "modification_date": (
            instance.modification_date.isoformat() if instance.modification_date else None
        ),
        "id_responsible_user": instance.id_responsible_user_id,
    }

def maintenance_scheduling_snapshot(ms_obj) -> Dict[str, Any]:
    """
    Snapshot ligero y JSON-serializable para MaintenanceScheduling.
    Devuelve sólo primitivos: ids, strings, números, booleans o None.
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
        val = _safe_get(ms_obj, attr)
        if val is None:
            return None
        # primitivos tal cual
        if isinstance(val, (int, float, str, bool)):
            return val
        # dict-like
        if isinstance(val, dict):
            return val.get("id") or val.get("pk") or val.get("name") or None
        # instancia Django u objeto con id/pk
        try:
            if hasattr(val, "id") or hasattr(val, "pk"):
                return getattr(val, "id", None) or getattr(val, "pk", None)
            if hasattr(val, "name"):
                return getattr(val, "name", None)
        except Exception:
            pass
        return None

    responsible = _safe_get(ms_obj, "id_responsible_user")
    responsible_id = None
    if responsible is not None:
        responsible_id = getattr(responsible, "id", None) or getattr(responsible, "pk", None)

    return {
        "id_maintenance_scheduling": (
            _safe_get(ms_obj, "id_maintenance_scheduling")
            or _safe_get(ms_obj, "id")
            or _safe_get(ms_obj, "pk")
        ),
        "id_maintenance_request": serialize_attr("id_maintenance_request"),
        "id_machinery": serialize_attr("id_machinery"),
        "scheduled_at": str(_safe_get(ms_obj, "scheduled_at")),
        "details": _safe_get(ms_obj, "details"),
        "assigned_technician": serialize_attr("assigned_technician"),
        "maintenance_type": serialize_attr("maintenance_type"),
        "maintenance_scheduling_status": serialize_attr("maintenance_scheduling_status"),
        "justification": _safe_get(ms_obj, "justification"),
        "id_consecutive": serialize_attr("id_consecutive"),
        "registration_date": str(_safe_get(ms_obj, "registration_date")),
        "modification_date": str(_safe_get(ms_obj, "modification_date")),
        "id_responsible_user": str(responsible_id) if responsible_id else None,
    }