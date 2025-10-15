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
from service_requests.utils.audit_helpers import get_actor_info, service_request_snapshot, service_request_cancel_snapshot
from service_requests.serializers.service_request_serializers.service_request_cancel_serializer import ServiceRequestCancelSerializer
from service_requests.models import RequestMachineryUser
from parameterization.models.statues import Statues
from machinery.models.machinery import Machinery

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

    @action(detail=False, methods=['post'])
    def create_pre_request(self, request):
        """
        Crea una nueva pre-solicitud de servicio.
        """
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

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancela una solicitud de servicio.
        Reglas:
        - Requiere permiso ID 153.
        - Solo se puede cancelar si la solicitud está en estado PENDIENTE (id=20).
        - No se puede cancelar si ya está ACEPTADA (id=22) o CANCELADA (id=23).
        - Al cancelar, cambia el estado de la solicitud a CANCELADO (id=23) y
          la maquinaria asociada a DISPONIBLE (id=4).
        - Registra observaciones, fecha y usuario de cancelación.
        """
        # Autenticación
        if not request.user.is_authenticated:
            return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        permission_id = 153
        if not self.check_permission(request, permission_id):
            return Response({"message": "No tiene permisos para cancelar solicitudes"}, status=status.HTTP_403_FORBIDDEN)

        # Buscar la solicitud por su PK (id_request)
        service_request = get_object_or_404(ServiceRequest, pk=pk)

        serializer = ServiceRequestCancelSerializer(
            instance=service_request,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Error en la validación de datos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():

                # Aplicar datos de cancelación (observaciones, fecha, usuario)
                serializer.save()

                # Cambiar estado de la solicitud a CANCELADO (23)
                cancel_status = get_object_or_404(Statues, pk=23)
                service_request.request_status = cancel_status
                service_request.save(update_fields=['request_status'])

                # Cambiar estado de la maquinaria asociada a DISPONIBLE (4)
                available_status = get_object_or_404(Statues, pk=4)
                # Obtener maquinarias vinculadas a la solicitud
                rms = RequestMachineryUser.objects.filter(request=service_request).select_related('machinery')
                machinery_ids = [rm.machinery_id for rm in rms]
                if machinery_ids:
                    # Usar el campo _id para actualizar el FK en bulk
                    Machinery.objects.filter(pk__in=machinery_ids).update(machinery_operational_status_id=available_status.pk)

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    machinery_statuses = [
                        {"id_machinery": mid, "machinery_operational_status_id": 4}
                        for mid in machinery_ids
                    ] if machinery_ids else []
                    AuditClient(request).create(
                        object_id=str(service_request.id_request),
                        after=service_request_cancel_snapshot(service_request, machinery_statuses=machinery_statuses),
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="requests",
                        submodule="requests",
                    )
                except Exception as audit_exc:
                    logger.warning("El servicio de auditoría ha fallado en cancel: %s", str(audit_exc))

        except Exception as e:
            logger.error(f"Error inesperado al cancelar solicitud: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Ocurrió un error inesperado al procesar la cancelación',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Enviar notificación de cancelación por correo
        self._send_cancellation_notification(service_request, serializer.validated_data.get('observations', ''), request)

        # Respuesta de éxito
        return Response({
            'success': True,
            'message': f"Solicitud cancelada exitosamente. Código: {service_request.id_request}.",
            'id_request': service_request.id_request
        }, status=status.HTTP_200_OK)

    def _get_user_info(self, user_id, request=None):
        """
        Obtiene la información básica del usuario desde el servicio de autenticación.
        Retorna un diccionario con 'email' y 'name' si es exitoso, None en caso de error.
        """
        try:
            auth_service_url = os.getenv('AUTH_SERVICE_URL')
            if not auth_service_url:
                logger.warning("AUTH_SERVICE_URL no está configurado")
                return None

            url = f"{auth_service_url.rstrip('/')}/users/users/basic-user-list/by-ids"
            headers = {
                'Content-Type': 'application/json'
            }

            # Use same authentication logic as CustomerDetailSerializer
            if request is not None:
                auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                    request.headers.get('Authorization') if hasattr(request, 'headers') else None
                )
                if auth_header:
                    headers['Authorization'] = auth_header

            response = requests.post(
                url,
                json={"ids": [user_id]},
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get('success') and response_data.get('data'):
                    users = response_data['data']
                    if users and isinstance(users, list) and len(users) > 0:
                        user_data = users[0]  # Tomar el primer usuario de la respuesta
                        # Concatenate name fields for client_name
                        full_name = f"{user_data.get('name', '')} {user_data.get('first_last_name', '')} {user_data.get('second_last_name', '')}".strip()
                        return {
                            'email': user_data.get('email'),
                            'name': full_name
                        }

        except Exception as e:
            logger.error(f"Error al obtener información del usuario {user_id}: {str(e)}", exc_info=True)

        return None

    def _send_cancellation_notification(self, service_request, reason, request=None):
        """
        Envía una notificación de cancelación por correo electrónico.
        """
        try:
            customer = service_request.customer
            if not customer:
                logger.warning("No se pudo enviar notificación: la solicitud no tiene cliente asociado")
                return

            # Obtener información del usuario
            if hasattr(customer, 'id_user') and customer.id_user:
                user_info = self._get_user_info(customer.id_user.pk, request)
            else:
                user_info = None

            # Preparar datos para la notificación
            email = None
            client_name = "Cliente"

            if user_info and user_info.get('email'):
                # Case 1: Customer has id_user - use data from API
                email = user_info['email']
                client_name = user_info.get('name', 'Cliente')
            else:
                # Case 2: Customer has id_user = null - use data from customer model
                if hasattr(customer, 'email') and customer.email:
                    email = customer.email
                    # Concatenate name fields from customer model
                    name_parts = [customer.name, customer.first_last_name, customer.second_last_name]
                    client_name = ' '.join(part for part in name_parts if part).strip() or "Cliente"
                else:
                    # Try to get any available data from customer model as fallback
                    if any([customer.name, customer.first_last_name, customer.second_last_name]):
                        name_parts = [customer.name, customer.first_last_name, customer.second_last_name]
                        client_name = ' '.join(part for part in name_parts if part).strip() or "Cliente"

            if not email:
                logger.warning("No se pudo enviar notificación: no hay dirección de correo disponible")
                return

            # Enviar notificación
            auth_service_url = os.getenv('AUTH_SERVICE_URL')
            if not auth_service_url:
                logger.warning("No se pudo enviar notificación: AUTH_SERVICE_URL no está configurado")
                return

            url = f"{auth_service_url.rstrip('/')}/users/users/notifications/send-cancellation/"
            headers = {
                'Content-Type': 'application/json'
            }

            # Use same authentication logic as user data API call
            if request is not None:
                auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
                    request.headers.get('Authorization') if hasattr(request, 'headers') else None
                )
                if auth_header:
                    headers['Authorization'] = auth_header

            # Use completion_cancellation_observations from service_request as reason
            reason_text = service_request.completion_cancellation_observations or reason or "No se especificó una razón"

            payload = {
                "email": email,
                "client_name": client_name,
                "reason": reason_text,
                "request_code": service_request.id_request
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"Error al enviar notificación de cancelación: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error inesperado al enviar notificación de cancelación: {str(e)}", exc_info=True)
