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
from service_requests.serializers.service_request_serializers.service_request_complete_serializer import ServiceRequestCompleteSerializer
from service_requests.models import RequestMachineryUser
from parameterization.models.statues import Statues
from machinery.models.machinery import Machinery
from users.models import User
from service_requests.serializers.service_request_serializers.service_request_detail_serializer import ServiceRequestDetailSerializer
from service_requests.serializers.service_request_serializers.list_service_request_serializer import ServiceRequestListSerializer
from service_requests.serializers.service_request_serializers.pre_request_update_serializer import PreRequestUpdateSerializer
from service_requests.utils.audit_helpers import (
    get_actor_info, 
    service_request_snapshot, 
    service_request_related_models_snapshot
)
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
        
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """
        Obtiene los detalles completos de una solicitud de servicio por su ID.
        """
        try:
            # Verificar si el usuario tiene permiso para ver los detalles
            if not self.check_permission(request, 154):  # Reemplazar con el ID de permiso adecuado
                return Response(
                    {"error": "No tiene permiso para ver los detalles de la solicitud"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                # Obtener la solicitud
                service_request = ServiceRequest.objects.get(id_request=pk)
                
                # Serializar los datos de la solicitud
                serializer = ServiceRequestDetailSerializer(service_request, context={'request': request})
                
                # Devolver los datos serializados
                return Response(serializer.data)
                
            except ServiceRequest.DoesNotExist:
                return Response(
                    {"error": "No se encontró la solicitud de servicio solicitada"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Error al obtener los detalles de la solicitud: {str(e)}")
            return Response(
                {"error": "Ocurrió un error al procesar la solicitud"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"], url_path="list")
    def list_requests(self, request):
        
        try:
            # Manejo explícito de usuario no autenticado (consistente con otros endpoints)
            if not request.user.is_authenticated:
                return Response({
                    "message": "Usuario no autenticado"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Verificación de permiso para listar todas las solicitudes
            if not self.check_permission(request, 149):
                return Response({
                    "message": "No tiene permisos para listar solicitudes"
                }, status=status.HTTP_403_FORBIDDEN)

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

            serializer = ServiceRequestListSerializer(qs, many=True, context={"request": request})
            results = serializer.data

            response = {
                "success": True,
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

    @action(detail=True, methods=['patch'], url_path='confirm')
    def confirm(self, request, pk=None):
        """
        Confirma una solicitud de servicio.
        Requiere permiso con ID 150.
        """
        permission_id = 150
        try:
            # Verificar autenticación
            if not request.user.is_authenticated:
                return Response(
                    {"message": "Usuario no autenticado"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Verificar permiso
            if not self.check_permission(request, permission_id):
                return Response(
                    {"message": "No tiene permiso para confirmar solicitudes de servicio"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener la instancia de la solicitud
            try:
                service_request = ServiceRequest.objects.get(id_request=pk)
                
                # Validar que el estado actual sea 19 (Pendiente de confirmación)
                if service_request.request_status_id != 19:
                    try:
                        status_19 = Statues.objects.get(id_statues=19)
                        status_name = status_19.name
                    except Statues.DoesNotExist:
                        status_name = "Pendiente de confirmación"
                    
                    return Response(
                        {"message": f"La solicitud no está en estado '{status_name}' o ya fue confirmada"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
            except ServiceRequest.DoesNotExist:
                return Response(
                    {"message": "La solicitud especificada no existe"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validar y procesar la confirmación
            serializer = PreRequestUpdateSerializer(
                instance=service_request,
                data=request.data,
                context={'request': request}
            )
            
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener snapshots antes de la actualización
            before_request = service_request_snapshot(service_request)
            before_related = service_request_related_models_snapshot(service_request)
            
            # Confirmar la solicitud
            with transaction.atomic():
                # Tomar instantánea ANTES de los cambios
                before_request = service_request_snapshot(service_request)
                before_related = service_request_related_models_snapshot(service_request)
                
                # Actualizar la solicitud con los datos validados
                updated_request = serializer.save()
                
                # Tomar instantánea DESPUÉS de los cambios
                after_request = service_request_snapshot(updated_request)
                after_related = service_request_related_models_snapshot(updated_request)
                
                # Aplicar lógica de confirmación
                updated_request.request_status_id = 20  # Estado "En revisión"
                confirmation_time = timezone.now()
                updated_request.confirmation_datetime = confirmation_time
                
                # Asignar el usuario de confirmación
                try:
                    user_instance = User.objects.get(id_user=request.user.id)
                    updated_request.confirmation_user = user_instance
                    confirmation_user_id = user_instance.id_user
                except (User.DoesNotExist, AttributeError) as e:
                    logger.warning(f"User not found in database: {str(e)}")
                    updated_request.confirmation_user = None
                    confirmation_user_id = None
                
                # Forzar la actualización de la fecha de modificación
                updated_request.modification_date = confirmation_time
                updated_request.save(update_fields=[
                    'modification_date', 
                    'request_status_id', 
                    'confirmation_datetime', 
                    'confirmation_user'
                ])
                
                # Enviar notificación de confirmación
                self._send_confirmation_notification(updated_request, request)
                
                # Obtener los datos actualizados después de guardar
                updated_request.refresh_from_db()
                
                # Registrar evento de auditoría con cambios detallados
                try:
                    actor_id, actor_name, actor_role = get_actor_info(request.user)
                    after_request = service_request_snapshot(updated_request)
                    after_related = service_request_related_models_snapshot(updated_request)
                    
                    # Asegurarse de que los campos de confirmación se incluyan en el before_request
                    before_request['confirmation_datetime'] = None
                    before_request['confirmation_user_id'] = None
                    
                    # Actualizar after_request con los valores reales
                    after_request['confirmation_datetime'] = str(confirmation_time) if confirmation_time else None
                    after_request['confirmation_user_id'] = confirmation_user_id
                    
                    # Calcular cambios detallados
                    changes = {
                        'changed': {},
                        'created': {},
                        'removed': {}
                    }
                    
                    # Comparar cambios en la solicitud
                    for field in before_request:
                        if before_request[field] != after_request.get(field):
                            changes['changed'][field] = {
                                'from': before_request[field],
                                'to': after_request[field]
                            }
                    
                    # Comparar cambios en modelos relacionados
                    if before_related != after_related:
                        # Comparar ubicación
                        if before_related.get('location') != after_related.get('location'):
                            if before_related.get('location') and after_related.get('location'):
                                # Actualización de ubicación
                                location_changes = {}
                                for field in before_related['location']:
                                    if before_related['location'][field] != after_related['location'].get(field):
                                        location_changes[field] = {
                                            'from': before_related['location'][field],
                                            'to': after_related['location'].get(field)
                                        }
                                if location_changes:
                                    changes['changed']['location'] = location_changes
                            elif after_related.get('location'):
                                # Nueva ubicación
                                changes['created']['location'] = after_related['location']
                            
                        # Comparar maquinaria y operarios
                        before_machinery = {mu['id_request_machinery_user']: mu 
                                         for mu in before_related.get('machinery_users', [])}
                        after_machinery = {mu['id_request_machinery_user']: mu 
                                        for mu in after_related.get('machinery_users', [])}
                        
                        # Encontrar cambios en maquinaria/operarios
                        for mu_id, mu_data in after_machinery.items():
                            if mu_id in before_machinery:
                                # Actualización
                                mu_changes = {}
                                for field in mu_data:
                                    if before_machinery[mu_id].get(field) != mu_data.get(field):
                                        mu_changes[field] = {
                                            'from': before_machinery[mu_id].get(field),
                                            'to': mu_data.get(field)
                                        }
                                if mu_changes:
                                    if 'machinery_users' not in changes['changed']:
                                        changes['changed']['machinery_users'] = {}
                                    changes['changed']['machinery_users'][str(mu_id)] = mu_changes
                            else:
                                # Nuevo registro
                                if 'machinery_users' not in changes['created']:
                                    changes['created']['machinery_users'] = []
                                changes['created']['machinery_users'].append(mu_data)
                        
                        # Verificar eliminaciones (aunque no debería haber en este flujo)
                        for mu_id in set(before_machinery.keys()) - set(after_machinery.keys()):
                            if 'machinery_users' not in changes['removed']:
                                changes['removed']['machinery_users'] = []
                            changes['removed']['machinery_users'].append(before_machinery[mu_id])
                    
                    # Inicializar estructura de cambios
                    diff_changes = {}

                    # Procesar cambios en la solicitud principal
                    if changes.get('changed'):
                        for field, change in changes['changed'].items():
                            if field not in ['location', 'machinery_users'] and 'to' in change:
                                diff_changes[field] = {
                                    'from': change.get('from'),  # Usar el valor anterior real
                                    'to': change['to']
                                }
                    
                    # Incluir campos de pago
                    payment_fields = [
                        'payment_method', 'payment_status', 'amount_paid',
                        'currency_unit_amount_paid', 'amount_to_pay', 'currency_unit_amount_to_pay'
                    ]
                    for field in payment_fields:
                        if field in after_request and after_request[field] is not None:
                            diff_changes[field] = {
                                'from': before_request.get(field),
                                'to': after_request[field]
                            }
                    
                    # Incluir todos los campos de location
                    location = getattr(updated_request, 'request_location', None)
                    if location:
                        location_fields = [
                            'id_request_location', 'country', 'department', 'city_id',
                            'place_name', 'latitude', 'longitude', 'area', 'area_unit_id',
                            'altitude', 'altitude_unit_id'
                        ]
                        for field in location_fields:
                            if hasattr(location, field):
                                field_name = f'location_{field}'
                                field_value = getattr(location, field, None)
                                # Si es una relación, obtener solo el ID
                                if field.endswith('_id') and field_value is None:
                                    # Intentar obtener el ID del objeto relacionado
                                    rel_field = field.replace('_id', '')
                                    if hasattr(location, rel_field):
                                        rel_obj = getattr(location, rel_field)
                                        if rel_obj is not None:
                                            field_value = rel_obj.id if hasattr(rel_obj, 'id') else None
                                
                                diff_changes[field_name] = {
                                    'from': None,  # Siempre null para nuevos registros
                                    'to': field_value
                                }
                    
                    # Procesar maquinaria/operarios
                    if 'machinery_users' in after_related:
                        for idx, mu in enumerate(after_related['machinery_users'], 1):
                            if not isinstance(mu, dict):
                                continue
                            for field in [
                                'machinery_id', 'user_id', 'soil_type_id', 'texture_id', 
                                'humidity_level', 'implementation_id', 'depth', 'slope', 'work_duration'
                            ]:
                                if field in mu:
                                    diff_changes[f'machinery_{idx}_{field}'] = {
                                        'from': None,  # Siempre null para nuevos registros
                                        'to': mu[field]
                                    }
                    
                    # Crear before y after basados en el diff
                    before_data = {}
                    after_data = {}
                    
                    for field, change in diff_changes.items():
                        before_data[field] = change['from']
                        after_data[field] = change['to']
                    
                    # Registrar auditoría con before y after
                    AuditClient(request).update(
                        object_id=str(updated_request.id_request),
                        before=before_data or None,
                        after=after_data,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role,
                        permission_id=permission_id,
                        module='requests',
                        submodule='requests'
                    )
                        
                except Exception as audit_error:
                    logger.error(f"Error en auditoría al confirmar solicitud: {str(audit_error)}", exc_info=True)
                
                return Response(
                    {"message": "Solicitud confirmada exitosamente"},
                    status=status.HTTP_200_OK
                )
            
        except Exception as e:
            logger.error(f"Error al confirmar la solicitud: {str(e)}", exc_info=True)
            return Response(
                {"error": "Ocurrió un error al confirmar la solicitud"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _send_confirmation_notification(self, service_request, request=None):
        """
        Envía una notificación de confirmación de pre-solicitud por correo electrónico.
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

            url = f"{auth_service_url.rstrip('/')}/users/users/notifications/send-presolicitud-confirmation/"
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

            # Formatear fechas
            start_date = service_request.scheduled_start_date.strftime('%d/%m/%Y') if service_request.scheduled_start_date else "fecha no especificada"
            end_date = service_request.scheduled_end_date.strftime('%d/%m/%Y') if service_request.scheduled_end_date else "fecha no especificada"
            
            payload = {
                "email": email,
                "client_name": client_name,
                "message": (
                    "Su pre-solicitud ha sido confirmada correctamente. "
                    f"Fecha de inicio: {start_date}, Fecha de finalización: {end_date}."
                ),
                "request_code": service_request.id_request
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"Error al enviar notificación de confirmación: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error inesperado al enviar notificación de confirmación: {str(e)}", exc_info=True)

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Finaliza una solicitud de servicio.
        
        Reglas:
        - Requiere permiso ID 152.
        - Solo se puede finalizar si la solicitud está en estado EN PROCESO (id=21).
        - No se puede finalizar si está CANCELADA (id=23).
        - Al finalizar, cambia el estado de la solicitud a FINALIZADA (id=22).
        - Cambia el estado de la maquinaria asociada a DISPONIBLE (id=4).
        - Registra fecha/hora automáticamente (timezone.now()), observaciones y usuario de finalización.
        - Envía notificación por correo al cliente.
        
        Body esperado:
        {
            "completion_cancellation_observations": "Trabajo completado satisfactoriamente"  # Obligatorio
        }
        """
        # Autenticación
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Permiso
        permission_id = 152
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para finalizar solicitudes"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Buscar la solicitud por su PK (id_request)
        service_request = get_object_or_404(ServiceRequest, pk=pk)

        # Serializar y validar
        serializer = ServiceRequestCompleteSerializer(
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
                # Aplicar datos de finalización (fecha, hora, observaciones, usuario)
                serializer.save()

                # Cambiar estado de la solicitud a FINALIZADA (ID 22)
                completed_status_id = 22
                completed_status = get_object_or_404(Statues, pk=completed_status_id)
                service_request.request_status = completed_status
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
                    logger.warning("El servicio de auditoría ha fallado en complete: %s", str(audit_exc))

        except Exception as e:
            logger.error(
                f"Error inesperado al finalizar solicitud: {str(e)}", 
                exc_info=True
            )
            return Response({
                'success': False,
                'message': 'Ocurrió un error inesperado al procesar la finalización',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Enviar notificación de finalización por correo
        self._send_completion_notification(service_request, request)

        # Respuesta de éxito
        return Response({
            'success': True,
            'message': f"Solicitud finalizada exitosamente. Código: {service_request.id_request}.",
            'id_request': service_request.id_request
        }, status=status.HTTP_200_OK)

    def _send_completion_notification(self, service_request, request=None):
        """
        Envía una notificación de finalización por correo electrónico al cliente.
        Similar a _send_cancellation_notification pero con endpoint diferente.
        """
        try:
            customer = service_request.customer
            if not customer:
                logger.warning("No se pudo enviar notificación de finalización: la solicitud no tiene cliente asociado")
                return

            # Obtener información del usuario (mismo patrón que cancelación)
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
                logger.warning("No se pudo enviar notificación de finalización: no hay dirección de correo disponible")
                return

            # Enviar notificación
            auth_service_url = os.getenv('AUTH_SERVICE_URL')
            if not auth_service_url:
                logger.warning("No se pudo enviar notificación de finalización: AUTH_SERVICE_URL no está configurado")
                return

            url = f"{auth_service_url.rstrip('/')}/users/users/notifications/send-solicitud-completed/"
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

            # Construir mensaje con observaciones y fecha de finalización
            observations = service_request.completion_cancellation_observations or "Sin observaciones adicionales"
            completion_datetime = service_request.completion_cancellation_datetime
            
            if completion_datetime:
                completion_date_formatted = completion_datetime.strftime('%d/%m/%Y a las %H:%M')
                message = f"{observations}. Fecha de finalización: {completion_date_formatted}."
            else:
                message = observations

            payload = {
                "email": email,
                "client_name": client_name,
                "message": message,
                "request_code": service_request.id_request
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"Error al enviar notificación de finalización: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error inesperado al enviar notificación de finalización: {str(e)}", exc_info=True)

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
