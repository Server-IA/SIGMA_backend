from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging
from audit_sdk import AuditClient
from django.db import transaction
from django.utils import timezone
import os
import requests

from service_requests.models import ServiceRequest
from service_requests.serializers.service_request_serializers.pre_request_create_serializer import PreRequestCreateSerializer
from service_requests.serializers.service_request_serializers.list_service_request_serializer import ServiceRequestListSerializer
from service_requests.utils.audit_helpers import get_actor_info, service_request_snapshot
from django.db.models import Q

logger = logging.getLogger(__name__)

class ServiceRequestViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de solicitudes de servicio.
    """
    permission_classes = [IsAuthenticated]

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
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

    @action(detail=False, methods=["get"], url_path="list")
    def list_requests(self, request):
        
        try:
            can_view_all = self.check_permission(request, 149)

            qs = (
                ServiceRequest.objects
                .select_related(
                    "customer",
                    "payment_status",
                    "currency_unit_amount_paid",
                    "currency_unit_amount_to_pay",
                    "confirmation_user",
                    "completion_cancellation_user",
                    "request_status",
                    "id_responsible_user",
                )
            )

            if not can_view_all:
                qs = qs.filter(id_responsible_user=request.user)

            # Filtros
            # Estados por nombre o id
            status_names = request.query_params.get("status")
            if status_names:
                names = [s.strip() for s in status_names.split(",") if s.strip()]
                if names:
                    qs = qs.filter(request_status__name__in=names)

            status_ids = request.query_params.get("request_status_id")
            if status_ids:
                try:
                    ids = [int(s) for s in status_ids.split(",") if s.strip()]
                    if ids:
                        qs = qs.filter(request_status__id_statues__in=ids)
                except ValueError:
                    pass

            payment_names = request.query_params.get("payment_status")
            if payment_names:
                names = [s.strip() for s in payment_names.split(",") if s.strip()]
                if names:
                    qs = qs.filter(payment_status__name__in=names)

            payment_ids = request.query_params.get("payment_status_id")
            if payment_ids:
                try:
                    ids = [int(s) for s in payment_ids.split(",") if s.strip()]
                    if ids:
                        qs = qs.filter(payment_status__id_statues__in=ids)
                except ValueError:
                    pass

            date_from = request.query_params.get("date_from")
            if date_from:
                qs = qs.filter(scheduled_start_date__gte=date_from)

            date_to = request.query_params.get("date_to")
            if date_to:
                qs = qs.filter(scheduled_start_date__lte=date_to)

            search = request.query_params.get("search")
            if search:
                term = search.strip()
                if term:
                    qs = qs.filter(
                        Q(id_request__icontains=term)
                        | Q(customer__legal_entity_name__icontains=term)
                        | Q(customer__name__icontains=term)
                        | Q(customer__first_last_name__icontains=term)
                        | Q(customer__second_last_name__icontains=term)
                    )

            # Ordenamiento
            ordering = request.query_params.get("ordering", "-creation_date").strip()
            allowed = {
                "creation_date",
                "-creation_date",
                "scheduled_start_date",
                "-scheduled_start_date",
            }
            if ordering not in allowed:
                ordering = "-creation_date"
            qs = qs.order_by(ordering)

            # Paginación
            try:
                page = int(request.query_params.get("page", 1))
            except ValueError:
                page = 1
            try:
                limit = int(request.query_params.get("limit", 10))
            except ValueError:
                limit = 10
            page = max(page, 1)
            limit = max(min(limit, 100), 1)  # limitar a 100 por página

            total = qs.count()
            start = (page - 1) * limit
            end = start + limit
            page_qs = qs[start:end]

            serializer = ServiceRequestListSerializer(page_qs, many=True, context={"request": request})
            results = serializer.data

            response = {
                "success": True,
                "count": len(results),
                "total": total,
                "page": page,
                "limit": limit,
                "results": results,
            }
            if len(results) == 0:
                response["message"] = "No se encontraron solicitudes con los criterios seleccionados."

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listando solicitudes: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": "Ocurrió un error al listar las solicitudes",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="list-by-customer")
    def list_by_customer(self, request):
        
        try:
            customer_id = request.query_params.get("customer_id")
            if not customer_id:
                return Response({
                    "success": False,
                    "message": "El parámetro 'customer_id' es obligatorio."
                }, status=status.HTTP_400_BAD_REQUEST)

            qs = (
                ServiceRequest.objects
                .filter(customer_id=customer_id)
                .select_related(
                    "customer",
                    "payment_status",
                    "currency_unit_amount_paid",
                    "currency_unit_amount_to_pay",
                    "confirmation_user",
                    "completion_cancellation_user",
                    "request_status",
                    "id_responsible_user",
                )
                .order_by("-creation_date")
            )

            serializer = ServiceRequestListSerializer(qs, many=True, context={"request": request})
            results = serializer.data

            response = {
                "success": True,
                "count": len(results),
                "results": results,
            }
            if len(results) == 0:
                response["message"] = "No se encontraron solicitudes con los criterios seleccionados."

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listando solicitudes por cliente: {e}", exc_info=True)
            return Response({
                "success": False,
                "message": "Ocurrió un error al listar las solicitudes por cliente",
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def create_pre_request(self, request):
        
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 145
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear pre-solicitudes de servicio"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = PreRequestCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                with transaction.atomic():
                    service_request = serializer.save()

                    # Auditoría
                    try:
                        actor_id, actor_name, actor_role_name = get_actor_info(request.user)

                        AuditClient(request).create(
                            object_id=str(service_request.id_request),
                            after=service_request_snapshot(service_request),
                            actor_id=actor_id,
                            actor_name=actor_name,
                            actor_role=actor_role_name,
                            permission_id=permission_id,
                            module="requests",
                            submodule="requests",
                        )
                    except Exception as e:
                        logger.warning("El servicio de auditoría ha fallado en create_pre_request: %s", str(e))
                    
                    # Enviar notificación a usuarios con permiso 148
                    try:
                        notif_title = "Nueva pre solicitud creada"
                        notif_message = f"Se creó una pre solicitud con ID {service_request.id_request}."
                        notif_type = "pre_request_creation"
                        notif_body = {
                            "title": notif_title,
                            "message": notif_message,
                            "type": notif_type,
                            "user_id": request.user.id
                        }
                        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
                        if base_url:
                            url = f"{base_url}/users/users/notifications/send-to-permission/?permission_id=148"
                            headers = {}
                            auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (request.headers.get('Authorization') if hasattr(request, 'headers') else None)
                            if auth_header:
                                headers['Authorization'] = auth_header
                            try:
                                resp = requests.post(url, json=notif_body, headers=headers, timeout=10)
                                if resp.status_code != 200:
                                    logger.warning(f"No se pudo enviar la notificación: {resp.text}")
                            except Exception as notif_exc:
                                logger.warning(f"Error enviando notificación de pre-solicitud: {notif_exc}")
                    except Exception as notif_outer_exc:
                        logger.warning(f"Error general en notificación de pre-solicitud: {notif_outer_exc}")

                return Response({
                    'success': True,
                    'message': 'Pre-solicitud creada exitosamente',
                    'id_request': service_request.id_request
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Error en la validación de datos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error inesperado al crear pre-solicitud: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Ocurrió un error inesperado al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
