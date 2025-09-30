import logging
import os
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Tuple

import requests
from django.db import transaction
from django.utils import timezone

from machinery.models import Machinery, MachineryUsageSheet, PeriodicMaintenanceScheduling
from maintenance.models import MaintenanceRequest
from maintenance.models.maintenance import Maintenance
from parameterization.models import Statues, Types


logger = logging.getLogger(__name__)


# --- Parámetros ajustables (con override por variable de entorno) ---
ACTIVE_MACHINERY_STATUS_ID = int(os.getenv("ACTIVE_MACHINERY_STATUS_ID", "4"))
PENDING_REQUEST_STATUS_ID = int(os.getenv("PENDING_REQUEST_STATUS_ID", "10"))

MAINTENANCE_TYPE_CATEGORY_ID = int(os.getenv("MAINTENANCE_TYPE_CATEGORY_ID", "12"))
PRIORITY_CATEGORY_ID = int(os.getenv("PRIORITY_CATEGORY_ID", "13"))

MAINTENANCE_TYPE_PREVENTIVE_ID = int(os.getenv("MAINTENANCE_TYPE_PREVENTIVE_ID", "14"))
MAINTENANCE_TYPE_CORRECTIVE_ID = int(os.getenv("MAINTENANCE_TYPE_CORRECTIVE_ID", "15"))

DEFAULT_PRIORITY_TYPE_ID = int(os.getenv("DEFAULT_PRIORITY_TYPE_ID", "16"))
INACTIVITY_DAYS_THRESHOLD = int(os.getenv("INACTIVITY_DAYS_THRESHOLD", "14"))

AUTO_JUSTIFICATION = "AUTO"


def _km_from(raw_value: Optional[Decimal], unit_symbol: Optional[str]) -> Optional[Decimal]:
    """Convierte la distancia expresada en la hoja de uso a kilómetros."""

    if raw_value is None:
        return None

    try:
        value = Decimal(raw_value)
    except (InvalidOperation, TypeError):
        return None

    symbol = (unit_symbol or "").strip().lower()

    if symbol == "km":
        return value
    if symbol == "m":
        return value / Decimal(1000)
    if symbol in {"mi", "mile", "miles"}:
        return value * Decimal("1.60934")

    # Unidad desconocida: evitar decisiones incorrectas
    logger.warning("Unidad de distancia no soportada para conversión a km: %s", symbol)
    return None


def _pending_status() -> Optional[Statues]:
    try:
        return Statues.objects.get(pk=PENDING_REQUEST_STATUS_ID)
    except Statues.DoesNotExist:
        logger.error("Estado pendiente (id=%s) no existe en parametrización", PENDING_REQUEST_STATUS_ID)
        return None


def _resolve_priority(event_key: str) -> Optional[Types]:
    """Obtiene la prioridad a utilizar de acuerdo al evento. Fallback: primer registro por categoría."""

    try:
        default = Types.objects.get(pk=DEFAULT_PRIORITY_TYPE_ID)
        return default
    except Types.DoesNotExist:
        pass

    queryset = Types.objects.filter(id_types_categories_id=PRIORITY_CATEGORY_ID).order_by("id_types")
    return queryset.first()


def _corrective_type() -> Optional[Types]:
    """Obtiene el tipo de mantenimiento correctivo o el primero de la categoría."""

    try:
        return Types.objects.get(pk=MAINTENANCE_TYPE_CORRECTIVE_ID)
    except Types.DoesNotExist:
        pass

    return Types.objects.filter(id_types_categories_id=MAINTENANCE_TYPE_CATEGORY_ID).order_by("id_types").first()


def _exists_pending_request(machinery_id: int, maintenance_type_id: int) -> bool:
    return MaintenanceRequest.objects.filter(
        id_machinery_id=machinery_id,
        maintenance_type_id=maintenance_type_id,
        request_status_id=PENDING_REQUEST_STATUS_ID,
    ).exists()


def _should_skip_machinery(machinery: Machinery) -> bool:
    status_id = getattr(machinery, "machinery_operational_status_id", None)

    if status_id is None:
        return True

    if status_id != ACTIVE_MACHINERY_STATUS_ID:
        logger.debug(
            "Maquinaria %s omitida: estado operativo id=%s",
            machinery.id_machinery,
            status_id,
        )
        return True

    return False


def _build_description(title: str, reason: str, extra: Optional[str] = None) -> str:
    parts = [f"[{AUTO_JUSTIFICATION}] {title}", reason]
    if extra:
        parts.append(extra)
    # Limitar a la longitud máxima del modelo (300 caracteres)
    return " | ".join(parts)[:300]


def _create_request(
    *,
    machinery: Machinery,
    maintenance_type: Types,
    priority: Types,
    description: str,
    detected_at,
    pending_status: Statues,
    dry_run: bool,
) -> Optional[int]:
    if dry_run:
        logger.info(
            "[dry-run] Generar solicitud automática para maquinaria %s (tipo=%s)",
            machinery.id_machinery,
            maintenance_type.id_types,
        )
        return None

    try:
        with transaction.atomic():
            request = MaintenanceRequest.objects.create(
                id_machinery=machinery,
                maintenance_type=maintenance_type,
                description=description,
                priority=priority,
                request_status=pending_status,
                detected_at=detected_at,
                id_responsible_user=None,
                justification=AUTO_JUSTIFICATION,
            )
        logger.info(
            "Solicitud automática creada: id=%s maquinaria=%s",
            request.id_maintenance_request,
            machinery.id_machinery,
        )
        return request.id_maintenance_request
    except Exception as exc:
        logger.error(
            "No se pudo crear la solicitud automática para maquinaria %s: %s",
            machinery.id_machinery,
            exc,
        )
        return None


def _evaluate_periodic_schedules(now, pending_status: Statues, dry_run: bool) -> Tuple[int, int]:
    total_checked = 0
    total_created = 0

    schedules = (
        PeriodicMaintenanceScheduling.objects.select_related("machinery", "maintenance", "maintenance__maintenance_type")
        .all()
    )

    usage_by_machinery = {
        usage.id_machinery_id: usage
        for usage in MachineryUsageSheet.objects.select_related("distance_unit").all()
    }

    for schedule in schedules:
        total_checked += 1
        machinery = schedule.machinery

        if not machinery or _should_skip_machinery(machinery):
            continue

        usage_sheet = usage_by_machinery.get(machinery.id_machinery)
        if not usage_sheet:
            logger.debug(
                "Maquinaria %s sin ficha de uso: no se evalúa mantenimiento periódico",
                machinery.id_machinery,
            )
            continue

        trigger_reason = None
        trigger_extra = None

        if schedule.usage_hours is not None:
            try:
                current_hours = Decimal(usage_sheet.usage_hours or 0)
            except (InvalidOperation, TypeError):
                logger.warning(
                    "Horas de uso inválidas para maquinaria %s: %s",
                    machinery.id_machinery,
                    usage_sheet.usage_hours,
                )
                current_hours = Decimal(0)

            if current_hours >= Decimal(schedule.usage_hours):
                trigger_reason = (
                    f"Umbral de horas alcanzado ({current_hours} h >= {schedule.usage_hours} h)"
                )
                trigger_extra = "Disparo por horas de uso"

        if trigger_reason is None and schedule.distance_km is not None:
            km_value = _km_from(
                usage_sheet.distance_value,
                getattr(usage_sheet.distance_unit, "symbol", None),
            )
            if km_value is None:
                logger.warning(
                    "No se pudo convertir distancia para maquinaria %s (unidad=%s)",
                    machinery.id_machinery,
                    getattr(usage_sheet.distance_unit, "symbol", None),
                )
            elif km_value >= Decimal(schedule.distance_km):
                trigger_reason = (
                    f"Umbral de distancia alcanzado ({km_value} km >= {schedule.distance_km} km)"
                )
                trigger_extra = "Disparo por distancia"

        if trigger_reason is None:
            continue

        maintenance: Maintenance = schedule.maintenance
        maintenance_type = getattr(maintenance, "maintenance_type", None)
        if maintenance_type is None:
            logger.warning(
                "Mantenimiento %s sin tipo asociado. No se genera solicitud automática",
                maintenance.id_maintenance if maintenance else None,
            )
            continue

        if _exists_pending_request(machinery.id_machinery, maintenance_type.id_types):
            continue

        priority = _resolve_priority("periodic")
        if priority is None:
            logger.error("No se encontró prioridad válida para solicitudes automáticas")
            continue

        description = _build_description(maintenance.name, trigger_reason, trigger_extra)

        created_id = _create_request(
            machinery=machinery,
            maintenance_type=maintenance_type,
            priority=priority,
            description=description,
            detected_at=now.date(),
            pending_status=pending_status,
            dry_run=dry_run,
        )

        if created_id is not None or dry_run:
            total_created += 1

    return total_checked, total_created


def _evaluate_inactivity(now, pending_status: Statues, dry_run: bool) -> Tuple[int, int]:
    total_checked = 0
    total_created = 0

    limit_date = (now - timedelta(days=INACTIVITY_DAYS_THRESHOLD)).date()

    usage_sheets = MachineryUsageSheet.objects.select_related(
        "id_machinery", "id_machinery__machinery_operational_status"
    )

    corrective_type = _corrective_type()
    priority = _resolve_priority("inactivity")

    if corrective_type is None or priority is None:
        logger.error(
            "No se pueden generar solicitudes automáticas por inactividad: tipo correctivo=%s prioridad=%s",
            corrective_type,
            priority,
        )
        return total_checked, total_created

    for usage_sheet in usage_sheets:
        machinery = usage_sheet.id_machinery
        if not machinery:
            continue

        total_checked += 1

        if _should_skip_machinery(machinery):
            continue

        last_update = usage_sheet.modification_date
        if last_update is None:
            continue

        if last_update > limit_date:
            continue

        if _exists_pending_request(machinery.id_machinery, corrective_type.id_types):
            continue

        reason = (
            f"Inactividad ≥ {INACTIVITY_DAYS_THRESHOLD} días (última actualización: {last_update})"
        )
        description = _build_description("Revisión por inactividad", reason)

        created_id = _create_request(
            machinery=machinery,
            maintenance_type=corrective_type,
            priority=priority,
            description=description,
            detected_at=now.date(),
            pending_status=pending_status,
            dry_run=dry_run,
        )

        if created_id is not None or dry_run:
            total_created += 1

    return total_checked, total_created


def _notify_authorizers(summary: Dict) -> None:
    auth_service_url = os.getenv("AUTH_SERVICE_URL")
    if not auth_service_url:
        return

    endpoint = f"{auth_service_url.rstrip('/')}/users/users/send-maintenance-authorization-notification"
    payload = {
        "module": "maintenance",
        "event": "auto_requests_generated",
        "summary": summary,
        "generated_at": timezone.now().isoformat(),
    }

    try:
        requests.post(endpoint, json=payload, timeout=10)
    except Exception as exc:
        logger.warning("No se pudo enviar notificación de solicitudes automáticas: %s", exc)


def run_generate_auto_requests(*, dry_run: bool = False) -> Dict:
    now = timezone.now()
    pending_status = _pending_status()

    if pending_status is None:
        return {
            "dry_run": dry_run,
            "checked_periodic": 0,
            "created_periodic": 0,
            "checked_inactivity": 0,
            "created_inactivity": 0,
        }

    periodic_checked, periodic_created = _evaluate_periodic_schedules(
        now, pending_status, dry_run
    )

    inactivity_checked, inactivity_created = _evaluate_inactivity(
        now, pending_status, dry_run
    )

    summary = {
        "dry_run": dry_run,
        "checked_periodic": periodic_checked,
        "created_periodic": periodic_created,
        "checked_inactivity": inactivity_checked,
        "created_inactivity": inactivity_created,
        "generated_at": now.isoformat(),
    }

    if not dry_run and (periodic_created or inactivity_created):
        _notify_authorizers(summary)

    logger.info(
        "Resultado job solicitudes automáticas: %s",
        summary,
    )

    return summary


