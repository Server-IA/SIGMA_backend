import logging
from django.utils import timezone
from datetime import datetime, timedelta
import pytz  # Asegúrate de tenerlo instalado (viene por defecto con Django)
from maintenance.models.maintenance_scheduling import MaintenanceScheduling

logger = logging.getLogger(__name__)

def update_machinery_status_job():
    """
    Actualiza machinery_operational_status a 6 para todas las maquinarias
    cuyo mantenimiento esté programado para hoy (según hora local de Colombia)
    y cuyo estado de mantenimiento sea 13.
    """
    # Zona horaria local de Colombia
    colombia_tz = pytz.timezone("America/Bogota")

    # Obtener hora actual en la zona local
    now_local = timezone.now().astimezone(colombia_tz)
    today_local = now_local.date()

    # Calcular inicio y fin del día local
    start_of_day_local = colombia_tz.localize(datetime.combine(today_local, datetime.min.time()))
    end_of_day_local = start_of_day_local + timedelta(days=1)

    # Convertir a UTC para comparar con el campo 'scheduled_at' en la BD (que está en UTC)
    start_of_day_utc = start_of_day_local.astimezone(pytz.UTC)
    end_of_day_utc = end_of_day_local.astimezone(pytz.UTC)

    # Buscar mantenimientos del día local actual (convertido a UTC)
    schedulings = MaintenanceScheduling.objects.select_related("id_machinery").filter(
        scheduled_at__gte=start_of_day_utc,
        scheduled_at__lt=end_of_day_utc,
        maintenance_scheduling_status_id=13,
    )

    count = 0
    for scheduling in schedulings:
        machinery = scheduling.id_machinery
        if machinery and machinery.machinery_operational_status_id != 6:
            machinery.machinery_operational_status_id = 6
            machinery.save(update_fields=["machinery_operational_status"])
            count += 1
            logger.info(
                "Maquinaria %s actualizada a estado 6 por programación %s.",
                getattr(machinery, "id_machinery", None),
                getattr(scheduling, "id_maintenance_scheduling", None),
            )

    logger.info(
        "Job ejecutado (zona local Colombia): %s programaciones encontradas hoy (estado 13). %s maquinarias actualizadas.",
        schedulings.count(),
        count,
    )
