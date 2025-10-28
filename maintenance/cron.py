import logging
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from maintenance.models.maintenance_scheduling import MaintenanceScheduling
from machinery.models.machinery_usage_sheet import MachineryUsageSheet
from maintenance.models.maintenance_request import MaintenanceRequest
from machinery.models.periodic_maintenance import PeriodicMaintenanceScheduling
from parameterization.models.types import Types
from django.db.models import Q
from decimal import Decimal
from service_requests.models import ServiceRequest
from parameterization.models.statues import Statues
from django.db import transaction

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

def generate_automatic_maintenance_requests_job():
    """
    Genera automáticamente solicitudes de mantenimiento cuando las maquinarias
    alcanzan las horas de uso configuradas en periodic_maintenance_scheduling.
    
    Condiciones:
    - Compara usage_hours del periodic_maintenance_scheduling con usage_hours del machinery_usage_sheet
    - Solo genera solicitudes para maquinarias activas (excluye estados 3 y 5)
    - Permite múltiples solicitudes con diferentes tipos de mantenimiento
    - Asigna prioridad desde tipos con categoría 13
    - Estado inicial: 10 (Pendiente)
    """
    logger.info("Iniciando job de generación automática de solicitudes de mantenimiento...")
    
    # Zona horaria de Colombia
    colombia_tz = pytz.timezone("America/Bogota")
    now_local = timezone.now().astimezone(colombia_tz)
    today_local = now_local.date()
    
    # Obtener prioridad por defecto (primera de categoría 13)
    default_priority = None
    try:
        default_priority = Types.objects.filter(id_types_categories_id=13).first()
        if not default_priority:
            logger.error("No se encontró ningún tipo de prioridad en la categoría 13. No se generarán solicitudes.")
            return
    except Exception as e:
        logger.error(f"Error al obtener prioridad por defecto: {str(e)}")
        return
    
    # Obtener todas las programaciones periódicas activas (por horas de uso)
    # Excluir estados 3 y 5
    periodic_maintenances = (
        PeriodicMaintenanceScheduling.objects
        .select_related('machinery', 'maintenance', 'maintenance__maintenance_type')
        .filter(usage_hours__isnull=False)  # Solo las configuradas por horas
        .exclude(machinery__machinery_operational_status_id__in=[3, 5])  # Excluir estados 3 y 5
    )
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for pm_schedule in periodic_maintenances:
        try:
            machinery = pm_schedule.machinery
            maintenance = pm_schedule.maintenance
            configured_hours = pm_schedule.usage_hours  # Integer (ej: 500)
            
            # Verificar que la maquinaria esté activa (estado 4)
            if machinery.machinery_operational_status_id != 4:
                logger.debug(
                    f"Maquinaria {machinery.id_machinery} no está en estado activo (actual: {machinery.machinery_operational_status_id}). Omitiendo..."
                )
                skipped_count += 1
                continue
            
            # Obtener las horas de uso actuales de la maquinaria
            try:
                usage_sheet = MachineryUsageSheet.objects.get(id_machinery=machinery)
                # Convertir Decimal a entero (solo la parte entera antes del punto)
                current_hours_decimal = usage_sheet.usage_hours or Decimal('0')
                current_hours = int(current_hours_decimal)  # 520.50 → 520
            except MachineryUsageSheet.DoesNotExist:
                logger.warning(
                    f"No se encontró hoja de uso para maquinaria {machinery.id_machinery}. Omitiendo..."
                )
                skipped_count += 1
                continue
            
            # Verificar si se alcanzaron o superaron las horas configuradas
            if current_hours < configured_hours:
                logger.debug(
                    f"Maquinaria {machinery.id_machinery}: horas actuales ({current_hours}) "
                    f"< horas configuradas ({configured_hours}). No requiere mantenimiento aún."
                )
                skipped_count += 1
                continue
            
            # Generar consecutivo de solicitud
            request_id = generate_automatic_request_id()
            
            # Crear la solicitud automática con estado 10 (Pendiente)
            maintenance_request = MaintenanceRequest.objects.create(
                id_maintenance_request=request_id,
                id_machinery=machinery,
                maintenance_type=maintenance.maintenance_type,
                description=maintenance.description or f"Mantenimiento automático: {maintenance.name}",
                priority=default_priority,
                request_status_id=10,  # 10 = Pendiente (obligatorio)
                detected_at=today_local,
                id_responsible_user=None,  # Sistema automático
                registration_date=timezone.now(),
                modification_date=timezone.now(),
            )
            
            created_count += 1
            logger.info(
                f"✅ Solicitud automática {request_id} creada: "
                f"Maquinaria {machinery.id_machinery} - {machinery.machinery_name} | "
                f"Tipo: {maintenance.maintenance_type.name} | "
                f"Horas: {current_hours}/{configured_hours} (decimal original: {current_hours_decimal}) | "
                f"Prioridad: {default_priority.name} | "
                f"Estado: 10 (Pendiente)"
            )
            
            # TODO: Enviar notificación (implementar según sistema de notificaciones)
            # send_maintenance_request_notification(maintenance_request, permission_id=117)
            
        except Exception as e:
            error_count += 1
            logger.error(
                f"❌ Error al procesar mantenimiento periódico {pm_schedule.id_periodic_maintenance_scheduling}: {str(e)}",
                exc_info=True
            )
    
    # Resumen de ejecución
    logger.info(
        f"Job de solicitudes automáticas finalizado. "
        f"Creadas: {created_count} | Omitidas: {skipped_count} | Errores: {error_count}"
    )


def generate_automatic_request_id():
    """
    Genera un ID único para solicitud automática con formato: SOL-YYYY-NNNN
    """
    current_year = timezone.now().year
    
    # Buscar el último consecutivo del año actual
    last_request = (
        MaintenanceRequest.objects
        .filter(id_maintenance_request__startswith=f'SOL-{current_year}')
        .order_by('-id_maintenance_request')
        .first()
    )
    
    if last_request:
        # Extraer el número y incrementar
        try:
            last_number = int(last_request.id_maintenance_request.split('-')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        # Primera solicitud del año
        new_number = 1
    
    return f'SOL-{current_year}-{new_number:04d}'


def start_pending_requests_job():
    """
    Cambia el estado de las solicitudes de servicio de 'Pendiente' (20) a 'En Proceso' (21)
    y actualiza la fecha de inicio a la fecha actual del job.
    Además, cambia el estado de la maquinaria asignada a 'Reservada' (7).
    """
    logger = logging.getLogger(__name__)

    # Zona horaria de Colombia
    colombia_tz = pytz.timezone("America/Bogota")
    now_local = timezone.now().astimezone(colombia_tz)
    today_local = now_local.date()

    # Buscar solicitudes en estado pendiente (20)
    pending_requests = (
        ServiceRequest.objects
        .select_related('request_status', 'id_responsible_user')
        .prefetch_related('machinery_users__machinery')
        .filter(request_status_id=20)
    )

    updated_requests = 0
    updated_machinery = 0
    errors = 0

    # Obtener estado 21 (En Proceso) y 7 (Reservada)
    try:
        status_21 = Statues.objects.get(id_statues=21)
        status_7 = Statues.objects.get(id_statues=7)
    except Statues.DoesNotExist as e:
        logger.error(f"Estado requerido no encontrado: {str(e)}")
        return

    for request in pending_requests:
        try:
            with transaction.atomic():
                # Cambiar estado de solicitud a 21 (En Proceso)
                request.request_status = status_21
                # Actualizar fecha de inicio a la fecha actual
                request.scheduled_start_date = today_local
                request.save(update_fields=['request_status', 'scheduled_start_date', 'modification_date'])

                updated_requests += 1

                # Cambiar estado de maquinaria asignada a 7 (Reservada)
                machinery_updated = 0
                for machinery_user in request.machinery_users.all():
                    machinery = machinery_user.machinery
                    if machinery and machinery.machinery_operational_status_id != 7:
                        machinery.machinery_operational_status = status_7
                        machinery.save(update_fields=['machinery_operational_status', 'modification_date'])
                        machinery_updated += 1

                updated_machinery += machinery_updated

                logger.info(
                    f"Solicitud {request.id_request} actualizada: estado 20→21, "
                    f"fecha inicio: {today_local}, maquinaria actualizada: {machinery_updated}"
                )

        except Exception as e:
            errors += 1
            logger.error(
                f"Error procesando solicitud {getattr(request, 'id_request', 'unknown')}: {str(e)}",
                exc_info=True
            )

    logger.info(
        f"Job start_pending_requests_job ejecutado (Colombia: {today_local}). "
        f"Solicitudes actualizadas: {updated_requests}, "
        f"Maquinarias actualizadas: {updated_machinery}, "
        f"Errores: {errors}"
    )
