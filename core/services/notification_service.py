import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MaintenanceSchedulingNotificationContext:
    scheduling_id: int
    machinery_id: int
    scheduled_at: str
    previous_technician_id: Optional[int]
    new_technician_id: Optional[int]


def notify_maintenance_scheduling_update(ctx: MaintenanceSchedulingNotificationContext):
    """
    Punto de extensión para correo/sistema.
    Por ahora registra en logs (integración de email/event-bus puede conectarse aquí).
    """
    logger.info(
        "Notificación actualización mantenimiento programado | id=%s machinery=%s when=%s prev_tech=%s new_tech=%s",
        ctx.scheduling_id,
        ctx.machinery_id,
        ctx.scheduled_at,
        ctx.previous_technician_id,
        ctx.new_technician_id,
    )


