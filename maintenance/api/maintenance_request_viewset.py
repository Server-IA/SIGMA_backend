from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.serializers.maintenance_request_serializers.maintenance_request_create_serializer import (
    MaintenanceRequestCreateSerializer,
)
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_from_request_create_serializer import (
    MaintenanceSchedulingFromRequestCreateSerializer,
)
from maintenance.serializers.maintenance_request_serializers.maintenance_request_reject_serializer import (
    MaintenanceRequestRejectSerializer,
)
from maintenance.models import MaintenanceRequest
from django.shortcuts import get_object_or_404
from maintenance.models.maintenance_request import MaintenanceRequest
from maintenance.serializers.maintenance_request_serializers.maintenance_request_create_serializer import MaintenanceRequestCreateSerializer
from maintenance.serializers.maintenance_request_serializers.maintenance_request_list_serializer import MaintenanceRequestListSerializer
from maintenance.serializers.manteinace_scheduling_serializers.maintenance_scheduling_from_request_create_serializer import MaintenanceSchedulingFromRequestCreateSerializer
from maintenance.serializers.maintenance_request_serializers.maintenance_request_detail_serializer import MaintenanceRequestDetailSerializer
from maintenance.serializers.maintenance_request_serializers.maintenance_request_from_service_serializer import MaintenanceRequestFromServiceSerializer
from service_requests.models.service_request import ServiceRequest

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, build_meta_with_machinery_id
from maintenance.utils.audit_helpers import maintenance_request_snapshot, maintenance_scheduling_snapshot

logger = logging.getLogger(__name__)


class MaintenanceRequestViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar la creación de solicitudes de mantenimiento manuales.
    """
    def check_permission(self, request, required_permission_id: int):
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []

        permisos_usuario = []
        for rol in user_roles:
            perms = rol.get("permisos") or rol.get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))

        return required_permission_id in permisos_usuario

    @action(detail=True, methods=["get"], url_path="detail")
    def retrieve_request_detail(self, request, pk=None):
        """
        Obtiene el detalle completo de una solicitud de mantenimiento.
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 123
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para consultar la solicitud de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            instance = MaintenanceRequest.objects.select_related(
                "id_machinery",
                "maintenance_type",
                "priority",
                "request_status",
                "id_responsible_user",
            ).get(pk=pk)

            serializer = MaintenanceRequestDetailSerializer(instance)
            return Response(
                {
                    "success": True,
                    "message": "Detalle de la solicitud obtenido exitosamente",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except MaintenanceRequest.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "No se encontró la solicitud de mantenimiento con el ID proporcionado.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Error al obtener detalle de solicitud {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener el detalle de la solicitud",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"], url_path="list")
    def list_requests(self, request):
        """
        Lista todas las solicitudes de mantenimiento (manuales y automáticas).
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 124
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar las solicitudes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            requests = (
                MaintenanceRequest.objects.select_related(
                    "id_machinery",
                    "maintenance_type",
                    "priority",
                    "request_status",
                    "id_responsible_user",
                )
                .all()
                .order_by("-registration_date")
            )

            serializer = MaintenanceRequestListSerializer(requests, many=True)
            return Response(
                {
                    "success": True,
                    "message": "Lista de solicitudes de mantenimiento obtenida exitosamente",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error al listar solicitudes de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener la lista de solicitudes de mantenimiento",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="create")
    def create_request(self, request):
        """
        Crea una solicitud de mantenimiento manual.
        Requiere permiso ID 116 (ajustar si es diferente en tu parametrización de permisos).
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 119
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para registrar solicitudes de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            serializer = MaintenanceRequestCreateSerializer(data=request.data, context={"request": request})
            if serializer.is_valid():
                instance = serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).create(
                        object_id=str(getattr(instance, "id_maintenance_request", "")),
                        after=maintenance_request_snapshot(instance),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="maintenance",
                        submodule="maintenance_request",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en create_maintenance_request: %s", e)


                return Response(
                    {
                        "success": True,
                        "message": "Solicitud de mantenimiento registrada exitosamente",
                        "data": {"id_maintenance_request": instance.id_maintenance_request},
                    },
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception as e:
            logger.error(f"Error creando solicitud de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear la solicitud de mantenimiento",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="schedule")
    def schedule_from_request(self, request, pk=None):
        """
        Programa un mantenimiento a partir de una solicitud existente (pk).
        Requiere permiso ID 117.
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 120
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para programar mantenimientos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Inyectar el ID de la solicitud desde la URL en el payload del serializer
            data = request.data.copy()
            data["id_maintenance_request"] = pk

            serializer = MaintenanceSchedulingFromRequestCreateSerializer(
                data=data,
                context={"request": request},
            )

            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "message": "Error de validación",
                        "details": serializer.errors,
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            scheduling = serializer.save()

            # Auditoría: 
            try:
                after = maintenance_scheduling_snapshot(scheduling)
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).create(
                    object_id=str(getattr(scheduling, "id_maintenance_scheduling", "") or ""),
                    after=after,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="maintenance",
                    submodule="maintenance_request",
                    meta=build_meta_with_machinery_id(before=None, after=after),
                )
            except Exception as e:
                logging.warning("El servicio de auditoría ha fallado en schedule_from_request: %s", e)
                

            return Response(
                {
                    "success": True,
                    "message": "Mantenimiento programado exitosamente desde la solicitud",
                    "data": {
                        "id_maintenance_scheduling": scheduling.id_maintenance_scheduling,
                        "id_maintenance_request": pk,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            logger.error(f"Error programando mantenimiento desde solicitud {pk}: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al programar el mantenimiento",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="from-service-request")
    def create_from_service_request(self, request, pk=None):
        """
        Crea solicitudes de mantenimiento a partir de una solicitud de servicio.
        
        Este endpoint crea una solicitud de mantenimiento por cada maquinaria con alertas
        en la solicitud de servicio especificada.
        
        Parámetros:
        - pk: ID de la solicitud de servicio (service_requests.id_request)
        
        Solo requiere autenticación, no requiere permisos especiales.
        """
        # Verificar autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Obtener la solicitud de servicio
            try:
                service_request = ServiceRequest.objects.get(
                    id_request=pk,
                    request_status_id=21  # Verificar que el estado sea 21
                )
            except ServiceRequest.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Solicitud de servicio no encontrada o no tiene el estado requerido (21)"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si ya existen solicitudes de mantenimiento para esta solicitud de servicio
            existing_requests = MaintenanceRequest.objects.filter(
                description__icontains=f"SR-{pk}"
            )
            
            if existing_requests.exists():
                return Response(
                    {
                        "success": False,
                        "message": "Ya existen solicitudes de mantenimiento para esta solicitud de servicio"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Usar el serializer para crear las solicitudes de mantenimiento
            serializer = MaintenanceRequestFromServiceSerializer(
                data={},
                context={
                    'request': request,
                    'service_request': service_request
                }
            )
            
            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "message": "Error en los datos de la solicitud",
                        "errors": serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear las solicitudes de mantenimiento
            maintenance_requests = serializer.save()
            
            if not maintenance_requests:
                return Response(
                    {
                        "success": True,
                        "message": "No se encontraron máquinas con alertas para generar solicitudes de mantenimiento"
                    },
                    status=status.HTTP_200_OK
                )
            
            # Registrar en auditoría
            try:
                actor_id = request.user.id if request.user.is_authenticated else None
                actor_name = f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated else "Sistema"
                actor_role = request.user.rol if hasattr(request.user, 'rol') else None
                actor_role_name = actor_role.name if actor_role else "Sistema"
                
                for req in maintenance_requests:
                    AuditClient(request).create(
                        object_id=str(req.id_maintenance_request),
                        actor_id=str(actor_id) if actor_id is not None else None,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        module="maintenance",
                        submodule="maintenance_request",
                        meta={
                            "action": "create_from_service",
                            "service_request_id": pk,
                            "machinery_id": str(req.id_machinery_id),
                            "maintenance_type": str(req.maintenance_type_id) if req.maintenance_type_id else None,
                            "priority": str(req.priority_id) if req.priority_id else None
                        }
                    )
            except Exception as e:
                logger.warning(f"Error en el registro de auditoría: {str(e)}")
            
            return Response(
                {
                    "success": True,
                    "message": f"Se crearon {len(maintenance_requests)} solicitudes de mantenimiento correctamente",
                    "data": {
                        "count": len(maintenance_requests),
                        "requests": [{
                            "id": req.id_maintenance_request,
                            "machinery_id": req.id_machinery_id,
                            "description": req.description
                        } for req in maintenance_requests]
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error al crear solicitudes de mantenimiento desde servicio: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al procesar la solicitud",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"], url_path="reject")
    def reject_request(self, request, pk=None):
        """
        Rechaza una solicitud de mantenimiento.
        - Permiso requerido: 122
        - No permite rechazar solicitudes ya aceptadas (id=11) o ya rechazadas (id=12).
        - La justificación es obligatoria.
        """
        # Autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permisos (ajustar el ID de permiso según corresponda)
        permission_id = 122
        if not self.check_permission(request, permission_id):
            return Response(
                {
                    "success": False,
                    "message": "No tiene permisos para rechazar solicitudes de mantenimiento.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Obtener la instancia de la solicitud
            instance = get_object_or_404(MaintenanceRequest, id_maintenance_request=pk)

            before = maintenance_request_snapshot(instance)

            # Validar y procesar el rechazo
            serializer = MaintenanceRequestRejectSerializer(
                data=request.data,
                context={"request": request, "instance": instance}
            )

            if not serializer.is_valid():
                return Response(
                    {
                        "success": False,
                        "message": "Error de validación",
                        "details": serializer.errors,
                    },
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )

            instance = serializer.save()

            # Auditoría 
            try:
                after = maintenance_request_snapshot(instance)
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).update(
                    object_id=str(getattr(instance, "id_maintenance_request", "") or(pk or "")),
                    before=before,
                    after=after,
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="maintenance",
                    submodule="maintenance_request",
                    meta=build_meta_with_machinery_id(before=before, after=after),
                )
            except Exception as e:
                logger.warning("El servicio de auditoría ha fallado en reject_request: %s", e)

            return Response(
                {
                    "success": True,
                    "message": "Solicitud de mantenimiento rechazada exitosamente",
                    "data": {"id_maintenance_request": instance.id_maintenance_request},
                },
                status=status.HTTP_200_OK,
            )

        except MaintenanceRequest.DoesNotExist:
            return Response(
                {"success": False, "message": "Solicitud de mantenimiento no encontrada"},
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.error(f"Error rechazando solicitud de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al rechazar la solicitud de mantenimiento",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
