import logging
from django.utils import timezone
from datetime import datetime, timedelta
import pytz  # Asegúrate de tenerlo instalado (viene por defecto con Django)
from maintenance.models.maintenance_scheduling import MaintenanceScheduling
from machinery.models.machinery_usage_sheet import MachineryUsageSheet

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

def test_job():
    """Job de prueba: imprime hora y un mensaje."""
    print(f"[TEST JOB] ejecutado a {timezone.now().isoformat()}")

def set_inoperative_on_expired_contract_job():
    """
    Cambia a inoperativa (id=5) toda maquinaria cuyo contrato de uso
    haya vencido (contract_end_date < hoy en zona local de Colombia).

    Además, registra la justificación "Contrato vencido" y escribe logs.
    """
    logger = logging.getLogger(__name__)

    # Zona horaria de Colombia
    colombia_tz = pytz.timezone("America/Bogota")

    # Fecha local 'hoy' en Colombia
    now_local = timezone.now().astimezone(colombia_tz)
    today_local = now_local.date()

    # Buscar hojas de uso cuyo contrato venció antes de hoy
    qs = (
        MachineryUsageSheet.objects
        .select_related("id_machinery")
        .filter(contract_end_date__lt=today_local)
        .exclude(id_machinery__machinery_operational_status_id=5)
    )

    updated = 0
    for usage in qs:
        machinery = usage.id_machinery
        if not machinery:
            continue

        # Actualizar a inoperativa (id=5) y justificar
        machinery.machinery_operational_status_id = 5
        # Guardamos la justificación en el modelo de maquinaria
        try:
            machinery.justification = "Contrato vencido"
        except Exception:
            # Si no existe o hay restricción, ignoramos y solo actualizamos estado
            pass
        machinery.save(update_fields=["machinery_operational_status", "justification", "modification_date"])  # modification_date es auto_now
        updated += 1

        logger.info(
            "Maquinaria %s marcada INOPERATIVA (5) por contrato vencido (fin: %s).",
            getattr(machinery, "id_machinery", None),
            getattr(usage, "contract_end_date", None),
        )

    logger.info(
        "Job set_inoperative_on_expired_contract_job ejecutado (Colombia hoy=%s). %s maquinarias actualizadas.",
        today_local,
        updated,
    )
