from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.models import MaintenanceScheduling, MaintenanceReport
from parameterization.models import Statues

from maintenance.serializers.maintenance_report_serializers import (
    MaintenanceReportCreateSerializer,
    MaintenanceReportListSerializer,
    MaintenanceReportDetailSerializer
)
from core.services.pdf_service import build_maintenance_report_pdf
from django.http import HttpResponse
import os
import requests

logger = logging.getLogger(__name__)


class MaintenanceReportViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de reportes de mantenimiento.
    """

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        Adaptado de FastAPI para Django REST Framework.
        """
        # Obtener el payload del JWT desde request.auth
        payload = getattr(request, "auth", None) or {}

        # Obtener roles del payload (soporta "rol" y "roles")
        user_roles = payload.get("rol") or payload.get("roles") or []

        # Extraer todos los IDs de permisos de todos los roles
        permisos_usuario = []
        for rol in user_roles:
            # Obtener permisos del rol (soporta "permisos" y "permissions")
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario

    @action(detail=True, methods=['post'], url_path='create-report')
    def create_maintenance_report(self, request, pk=None):
        """
        Crea un reporte de mantenimiento para un mantenimiento programado específico.

        Este endpoint cumple con el criterio de aceptación #1 de HU-PM-005:
        "El sistema debe permitir registrar reporte de mantenimientos programados
        desde el listado de mantenimientos programados, a través de un botón de 'Reporte'."

        Campos requeridos:
        - title: Título del reporte
        - description: Descripción del mantenimiento (máximo 600 caracteres)
        - time_invested_hours: Horas invertidas
        - time_invested_minutes: Minutos invertidos
        - maintenance_items: Lista de IDs de mantenimientos realizados
        - spare_parts: Lista de repuestos utilizados

        Campos opcionales:
        - recommendations: Recomendaciones
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 127  # maintenance_scheduling.create_report
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear reportes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener el mantenimiento programado
            try:
                scheduling = MaintenanceScheduling.objects.select_related(
                    'maintenance_scheduling_status'
                ).get(pk=pk)
                # Agregar el ID del mantenimiento programado a los datos de la solicitud
                request.data['id_maintenance_scheduling'] = scheduling.id_maintenance_scheduling
            except MaintenanceScheduling.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Mantenimiento programado no encontrado"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Pasar el usuario autenticado como responsible_user si no se proporciona
            data = request.data.copy()
            if 'responsible_user' not in data:
                data['responsible_user'] = request.user.id
                
            serializer = MaintenanceReportCreateSerializer(
                data=data,
                context={'request': request, 'user': request.user}
            )

            if serializer.is_valid():
                instance = serializer.save()

                # Cambiar estado de la programación a 15 (ejecutado) al registrar el reporte
                try:
                    executed_status = Statues.objects.get(pk=15)
                    scheduling.maintenance_scheduling_status = executed_status
                    scheduling.save(update_fields=["maintenance_scheduling_status"])
                except Statues.DoesNotExist:
                    logger.error("Estado 15 (ejecutado) no encontrado en Statues")

                # Actualizar el estado de la maquinaria (esto ahora se maneja en el serializer)
                pass

                return Response(
                    {
                        "success": True,
                        "message": "Reporte de mantenimiento creado exitosamente",
                        "data": {
                            "id_maintenance_report": instance.id_maintenance_report,
                            "id_machinery_status": scheduling.id_machinery.machinery_operational_status.id_statues,
                            "maintenance_scheduling_status": scheduling.maintenance_scheduling_status.id_statues
                        }
                    },
                    status=status.HTTP_201_CREATED
                )

            # Formatear los errores de validación
            error_details = {}
            for field, errors in serializer.errors.items():
                if isinstance(errors, dict):
                    # Si el error ya está en el formato correcto, usarlo directamente
                    error_details.update(errors)
                elif isinstance(errors, list):
                    # Si es una lista de errores, extraer los mensajes
                    error_details[field] = [str(error) for error in errors]
                else:
                    # Cualquier otro formato de error
                    error_details[field] = [str(errors)]
            
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": error_details
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error creando reporte para mantenimiento {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el reporte de mantenimiento",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='list')
    def list_reports(self, request):
        """
        Lista todos los reportes de mantenimiento.
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 130  # maintenance_report.list
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar reportes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            queryset = MaintenanceReport.objects.select_related(
                'id_maintenance_scheduling',
                'id_maintenance_scheduling__id_machinery',
                'id_maintenance_scheduling__assigned_technician',
                'id_responsible_user'
            ).all().order_by('-registration_date')
            
            serializer = MaintenanceReportListSerializer(queryset, many=True)
            
            return Response(
                {
                    "success": True,
                    "message": "Lista de reportes de mantenimiento obtenida exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error listando reportes de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener la lista de reportes de mantenimiento",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='detail')
    def get_report_detail(self, request, pk=None):
        """
        Obtiene los detalles completos de un reporte de mantenimiento.
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 131  # maintenance_report.detail
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para ver detalles de reportes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            report = MaintenanceReport.objects.select_related(
                'id_maintenance_scheduling',
                'id_maintenance_scheduling__id_machinery',
                'id_maintenance_scheduling__assigned_technician',
                'id_responsible_user'
            ).get(pk=pk)
            
            serializer = MaintenanceReportDetailSerializer(report)
            
            return Response(
                {
                    "success": True,
                    "message": "Detalles del reporte obtenidos exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except MaintenanceReport.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Reporte de mantenimiento no encontrado"
                },
                status=status.HTTP_404_NOT_FOUND
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del reporte {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener los detalles del reporte",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='download')
    def download_report(self, request, pk=None):
        """
        Descarga el PDF del reporte de mantenimiento por id_maintenance_scheduling.
        """
        # Verificar autenticación
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 128  # maintenance_report.download
        if not self.check_permission(request, permission_id):
            return Response({"message": "No tiene permisos para descargar reportes."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Obtener el reporte por id_maintenance_scheduling
            report = MaintenanceReport.objects.select_related(
                'id_maintenance_scheduling',
                'id_maintenance_scheduling__id_machinery',
                'id_maintenance_scheduling__assigned_technician',
                'id_maintenance_scheduling__maintenance_type',
                'id_responsible_user'
            ).prefetch_related(
                'maintenance_relations__id_maintenance__maintenance_type',
                'spare_parts_used__spare_part_brand'
            ).get(id_maintenance_scheduling_id=pk)

            # Preparar datos de tablas
            # Mantenimientos realizados
            maintenance_items = []

            # Obtener información de todos los técnicos asignados al reporte desde servicio de usuarios
            technicians_map = {}
            technicians_list = []
            try:
                assigned_user_ids = list(report.assigned_users.values_list('id_user', flat=True))
                if assigned_user_ids:
                    base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
                    if base_url:
                        url = f"{base_url}/sigma/users/users/basic-user-list/by-ids"
                        headers = {}
                        # Pasar el mismo JWT recibido
                        auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or request.headers.get('Authorization')
                        if auth_header:
                            headers['Authorization'] = auth_header
                        try:
                            resp = requests.post(url, json={'ids': assigned_user_ids}, headers=headers, timeout=10)
                            if resp.status_code == 200:
                                payload = resp.json()
                                data = payload.get('data', []) or []
                                for u in data:
                                    uid = u.get('id')
                                    name = u.get('name') or ''
                                    fln = u.get('first_last_name') or ''
                                    sln = u.get('second_last_name') or ''
                                    full = ' '.join([p for p in [name, fln, sln] if p]).strip()
                                    technicians_map[uid] = full or str(uid)
                                    technicians_list.append(technicians_map[uid])
                            else:
                                # Fallback: map ids to string ids
                                for uid in assigned_user_ids:
                                    technicians_map[uid] = str(uid)
                        except Exception:
                            # En caso de error de red, mapear a ids crudos
                            for uid in assigned_user_ids:
                                technicians_map[uid] = str(uid)
            except Exception:
                technicians_map = {}
                technicians_list = []

            # Construir items de mantenimiento usando el nombre del técnico correspondiente (si existe en el mapping)
            for rel in getattr(report, 'maintenance_relations').all():
                m = rel.id_maintenance
                # Obtener id del técnico que realizó este mantenimiento
                try:
                    tech_id = getattr(getattr(rel, 'id_technician', None), 'id_user', None)
                except Exception:
                    tech_id = None
                technician_display = None
                if tech_id is not None:
                    technician_display = technicians_map.get(tech_id, str(tech_id))
                else:
                    technician_display = 'N/D'

                maintenance_items.append({
                    'name': getattr(m, 'name', 'N/D'),
                    'type': getattr(getattr(m, 'maintenance_type', None), 'name', 'N/D'),
                    'technician': technician_display,
                    'cost': getattr(rel, 'maintenance_cost', 'N/D'),
                })

            # Repuestos usados
            spare_parts = []
            for sp in getattr(report, 'spare_parts_used').all():
                total = float(sp.quantity_used) * float(sp.cost_at_time)
                spare_parts.append({
                    'name': getattr(sp, 'name', 'N/D'),
                    'brand': getattr(getattr(sp, 'spare_part_brand', None), 'name', 'N/D'),
                    'quantity': sp.quantity_used,
                    'unit_cost': sp.cost_at_time,
                    'total': total
                })

            # Construir el nombre completo del usuario que descarga usando el
            # mismo endpoint externo que usamos para los técnicos (no consultar
            # la tabla local de users, porque en esta BD no están los apellidos).
            downloader_user = None
            try:
                ru = getattr(request, 'user', None)
                if ru is not None:
                    user_id = getattr(ru, 'id_user', None) or getattr(ru, 'id', None) or getattr(ru, 'pk', None)

                    # 1) Intentar resolver desde technicians_map si el id está allí
                    if user_id and technicians_map:
                        try:
                            if user_id in technicians_map:
                                downloader_user = technicians_map.get(user_id)
                            else:
                                downloader_user = technicians_map.get(int(user_id), technicians_map.get(str(user_id)))
                        except Exception:
                            downloader_user = None

                    # 2) Si no se resolvió, llamar al servicio de autenticación externo
                    if not downloader_user and user_id:
                        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
                        if base_url:
                            url = f"{base_url}/sigma/users/users/basic-user-list/by-ids"
                            headers = {}
                            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or request.headers.get('Authorization')
                            if auth_header:
                                headers['Authorization'] = auth_header
                            try:
                                resp = requests.post(url, json={'ids': [user_id]}, headers=headers, timeout=10)
                                if resp.status_code == 200:
                                    payload = resp.json()
                                    data = payload.get('data', []) or []
                                    if data:
                                        u = data[0]
                                        name = u.get('name') or ''
                                        fln = u.get('first_last_name') or ''
                                        sln = u.get('second_last_name') or ''
                                        parts = [p for p in [name.strip(), fln.strip(), sln.strip()] if p]
                                        if parts:
                                            downloader_user = ' '.join(parts)
                            except Exception:
                                # ignore external service errors; fallback later
                                pass

                    # 3) Fallback final: intentar atributos en request.user
                    if not downloader_user:
                        given = (getattr(ru, 'name', None) or getattr(ru, 'first_name', None) or '').strip()
                        fln = (getattr(ru, 'first_last_name', None) or getattr(ru, 'last_name', None) or '').strip()
                        sln = (getattr(ru, 'second_last_name', None) or getattr(ru, 'secondLastName', None) or '').strip()
                        parts = [p for p in [given, fln, sln] if p]
                        if parts:
                            downloader_user = ' '.join(parts)
                        else:
                            downloader_user = str(getattr(ru, 'id_user', None) or getattr(ru, 'username', '') or ru)
            except Exception:
                downloader_user = None

            pdf_bytes = build_maintenance_report_pdf(
                report,
                maintenance_items,
                spare_parts,
                downloader_user,
                None,
                None,
                technicians_list
            )

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{pk}.pdf"'
            return response

        except MaintenanceReport.DoesNotExist:
            return Response({"success": False, "message": "Reporte no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error generando PDF del reporte {pk}: {str(e)}")
            return Response({"success": False, "message": "Error generando PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
