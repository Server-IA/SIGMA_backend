import os
from datetime import datetime
import pytz
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
import requests
import logging

from payroll.models import Employee, EmployeeContract
from payroll.utils.contract_history_report_generator import (
    generate_contract_history_pdf,
    build_otrosi_entries,
)

logger = logging.getLogger(__name__)


def _get_external_user_by_id(user_id: int, request) -> dict | None:
    """Obtiene información del usuario desde el servicio externo usando su ID.
    Usa el endpoint POST /users/users/basic-user-list/by-ids."""
    if not user_id:
        return None
    
    base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
    if not base_url:
        logger.warning("AUTH_SERVICE_URL no configurado, no se puede consultar usuario")
        return None
    
    url = f"{base_url}/users/users/basic-user-list/by-ids"
    headers = {'Content-Type': 'application/json'}
    
    auth = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
        request.headers.get('Authorization') if hasattr(request, 'headers') else None
    )
    if auth:
        headers['Authorization'] = auth
    
    try:
        resp = requests.post(url, json={'ids': [user_id]}, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Servicio externo respondió {resp.status_code} al buscar usuario {user_id}")
            return None
        
        payload = resp.json() if resp.content else {}
        data = payload.get('data') or []
        
        if isinstance(data, list):
            for u in data:
                if u and str(u.get('id')) == str(user_id):
                    return u
        
        logger.warning(f"Usuario {user_id} no encontrado en respuesta del servicio externo")
        return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al consultar servicio externo para usuario {user_id}")
        return None
    except Exception as e:
        logger.error(f"Error al consultar servicio externo para usuario {user_id}: {str(e)}")
        return None


class ContractHistoryReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def check_permission(self, request, required_permission_id: int) -> bool:
        """Verifica si el usuario tiene el permiso requerido por ID.
        
        Extrae permisos del JWT en request.auth desde roles.
        """
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []
        
        permisos_usuario = []
        for rol in user_roles:
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))
        
        return required_permission_id in permisos_usuario
    """ViewSet para generación de informes de Recursos Humanos.

    Submódulo: Generación de informes (Novedades)
    Endpoint implementado: Tipo 1 - Historial de contratos y cargos.
    """

    @action(detail=False, methods=['post'], url_path='contract-history-pdf')
    def contract_history_pdf(self, request):
        """Genera y descarga un PDF del historial de contratos y cargos.

        Body JSON esperado:
        {
          "employee_document": "123456",
          "date_from": "2024-01-01",
          "date_to": "2024-12-31"
        }
        
        Requiere permiso ID: 192 (consulta de informes de contratos).
        """
        required_permission_id = 192
        
        if not self.check_permission(request, required_permission_id):
            logger.warning(f"Usuario sin permiso {required_permission_id} intentó generar reporte de contratos")
            return Response(
                {"success": False, "message": "No tiene permiso para generar informes de contratos"},
                status=status.HTTP_403_FORBIDDEN
            )

        employee_document = request.data.get('employee_document')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')

        # Validaciones básicas
        missing = [f for f in ['employee_document', 'date_from', 'date_to'] if not request.data.get(f)]
        if missing:
            return Response({"success": False, "message": f"Faltan campos: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse fechas
        try:
            df_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            dt_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            return Response({"success": False, "message": "Formato de fecha inválido (usar YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)

        if df_obj >= dt_obj:
            return Response({"success": False, "message": "La Fecha Desde debe ser menor que Fecha Hasta."}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar empleado local por documento (asumiendo que Employee tiene document_number o relación con User)
        # Nota: Employee no tiene document_number directo, necesitamos buscar por id_user_id
        # Primero intentamos encontrar el empleado, luego validamos con el servicio externo
        
        logger.info(f"Buscando empleado con documento: {employee_document}")
        
        # Estrategia: buscar todos los empleados, luego filtrar por documento desde servicio externo
        # Esto es necesario porque Employee solo tiene id_user_id
        employees = Employee.objects.all()
        
        employee = None
        external_user = None
        
        # Consultar servicio externo para obtener user_id del documento
        # Usamos el endpoint by-ids en batch para todos los user_ids
        user_ids = [emp.id_user_id for emp in employees if emp.id_user_id]
        
        if not user_ids:
            return Response({"success": False, "message": "No hay empleados registrados en el sistema."}, status=status.HTTP_404_NOT_FOUND)
        
        # Consultar datos de usuarios en batch
        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            logger.error("AUTH_SERVICE_URL no configurado")
            return Response({"success": False, "message": "Error de configuración del servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers = {'Content-Type': 'application/json'}
        auth = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
            request.headers.get('Authorization') if hasattr(request, 'headers') else None
        )
        if auth:
            headers['Authorization'] = auth
        
        try:
            resp = requests.post(url, json={'ids': user_ids}, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Servicio externo respondió {resp.status_code}")
                return Response({"success": False, "message": "Error al consultar servicio de usuarios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            payload = resp.json() if resp.content else {}
            users_data = payload.get('data') or []
            
            # Buscar el usuario con el documento proporcionado
            for user in users_data:
                if str(user.get('document_number')) == str(employee_document):
                    external_user = user
                    user_id = user.get('id')
                    # Encontrar el empleado correspondiente
                    employee = next((emp for emp in employees if emp.id_user_id == user_id), None)
                    break
            
            if not external_user:
                logger.info(f"Documento {employee_document} no encontrado en usuarios registrados")
                return Response({"success": False, "message": "El documento ingresado no se encuentra registrado en el sistema."}, status=status.HTTP_404_NOT_FOUND)
            
            if not employee:
                logger.info(f"Usuario encontrado pero no tiene registro de empleado")
                return Response({"success": False, "message": "El documento corresponde a un usuario registrado pero no es empleado."}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error consultando servicio externo: {str(e)}")
            return Response({"success": False, "message": "Error al consultar servicio de usuarios."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Query contratos que intersectan rango
        contracts_qs = EmployeeContract.objects.select_related(
            'id_employee_charge', 'id_employee_department', 'contract_status', 'contract_termination_reason'
        ).filter(
            id_employee_id=employee.id_employee,
            start_date__lte=dt_obj,
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=df_obj)
        ).order_by('start_date', 'contract_code')

        contracts = list(contracts_qs)
        if not contracts:
            return Response({"success": False, "message": "No se encontraron contratos en el rango especificado."}, status=status.HTTP_404_NOT_FOUND)

        # Construir lista de Otrosí
        otrosi_entries = build_otrosi_entries(contracts)
        # Filtrar otrosí por rango (creación dentro del rango)
        otrosi_entries = [o for o in otrosi_entries if df_obj <= o['creation_date'] <= dt_obj]

        # Obtener el nombre del usuario que genera el reporte desde el JWT
        downloader_user = None
        payload = getattr(request, 'auth', None) or {}
        current_user_id = payload.get('id')
        
        if current_user_id:
            # Consultar el usuario actual desde el servicio externo
            current_user_data = _get_external_user_by_id(current_user_id, request)
            if current_user_data:
                name = current_user_data.get('name') or ''
                fln = current_user_data.get('first_last_name') or ''
                sln = current_user_data.get('second_last_name') or ''
                parts = [p for p in [name, fln, sln] if p]
                downloader_user = ' '.join(parts) if parts else None
        
        if not downloader_user:
            downloader_user = 'Sistema'

        try:
            pdf_bytes = generate_contract_history_pdf(
                employee=employee,
                contracts=contracts,
                otrosi_entries=otrosi_entries,
                date_from=date_from,
                date_to=date_to,
                downloader_user=downloader_user,
                logo_path=None,
                employee_user_data=external_user,  # Pasar datos del empleado para documento y nombre
            )
        except Exception as e:
            return Response({"success": False, "message": "No fue posible generar el informe. Intente nuevamente.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Timestamp en zona horaria de Colombia
        colombia_tz = pytz.timezone('America/Bogota')
        timestamp = datetime.now(colombia_tz).strftime('%Y%m%d_%H%M%S')
        filename = f"historial_contratos_{employee.id_employee}_{timestamp}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_bytes)
        response['Cache-Control'] = 'no-cache'
        logger.info(f"PDF generado exitosamente: {filename}, tamaño: {len(pdf_bytes)} bytes")
        return response
