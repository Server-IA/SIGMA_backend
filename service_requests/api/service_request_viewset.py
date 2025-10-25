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
from service_requests.serializers.service_request_serializers.service_request_report_serializer import ServiceRequestReportSerializer
from service_requests.utils.audit_helpers import (
    get_actor_info, 
    service_request_snapshot, 
    service_request_related_models_snapshot
)
from django.db.models import Q, Max

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
        El ID debe estar en formato: SOL-YYYY-XXXX (ejemplo: SOL-2025-0072)
        """
        try:
            # Verificar si el usuario tiene permiso para ver los detalles
            if not self.check_permission(request, 154):  # Reemplazar con el ID de permiso adecuado
                return Response(
                    {"error": "No tiene permiso para ver los detalles de la solicitud"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validar el formato del ID (SOL-YYYY-XXXX)
            import re
            if not re.match(r'^SOL-\d{4}-\d{4}$', str(pk)):
                return Response(
                    {"error": "Formato de ID inválido. Debe ser SOL-YYYY-XXXX (ejemplo: SOL-2025-0072)"},
                    status=status.HTTP_400_BAD_REQUEST
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

        permission_id = 146
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

    @action(detail=False, methods=['post'])
    def create_request(self, request):
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 151
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear solicitudes de servicio"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Usar PreRequestUpdateSerializer para validar los datos de entrada
            serializer = PreRequestUpdateSerializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                with transaction.atomic():
                    # Crear la ubicación primero usando el serializer de ubicación
                    from service_requests.serializers.service_request_serializers.pre_request_update_serializer import RequestLocationUpdateSerializer

                    location_data = serializer.validated_data.pop('location')
                    machinery_users_data = serializer.validated_data.pop('machinery_users', [])

                    # Obtener usuario responsable
                    if request and hasattr(request, 'user') and request.user.is_authenticated:
                        try:
                            user = User.objects.get(id_user=request.user.id)
                            responsible_user = user
                        except User.DoesNotExist:
                            return Response(
                                {"message": "Usuario responsable no encontrado"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    else:
                        return Response(
                            {"message": "Usuario no autenticado"},
                            status=status.HTTP_401_UNAUTHORIZED
                        )

                    # Generar ID usando la misma lógica que PreRequestCreateSerializer
                    current_year = timezone.now().year
                    max_request = ServiceRequest.objects.filter(
                        id_request__startswith=f'SOL-{current_year}'
                    ).aggregate(Max('id_request'))

                    if max_request['id_request__max']:
                        last_number = int(max_request['id_request__max'].split('-')[-1])
                        new_number = last_number + 1
                    else:
                        new_number = 1

                    request_id = f'SOL-{current_year}-{new_number:04d}'

                    # Crear estado 20 (En revisión)
                    status_20 = Statues.objects.get(id_statues=20)

                    # Crear la solicitud de servicio
                    service_request = ServiceRequest.objects.create(
                        id_request=request_id,
                        customer=serializer.validated_data['customer'],
                        request_detail=serializer.validated_data['request_detail'],
                        scheduled_start_date=serializer.validated_data['scheduled_start_date'],
                        scheduled_end_date=serializer.validated_data['scheduled_end_date'],
                        payment_method=serializer.validated_data.get('payment_method'),
                        payment_status=serializer.validated_data.get('payment_status'),
                        amount_paid=serializer.validated_data.get('amount_paid'),
                        currency_unit_amount_paid=serializer.validated_data.get('currency_unit_amount_paid'),
                        amount_to_pay=serializer.validated_data.get('amount_to_pay'),
                        currency_unit_amount_to_pay=serializer.validated_data.get('currency_unit_amount_to_pay'),
                        request_status=status_20,
                        id_responsible_user=responsible_user
                    )

                    # Crear ubicación
                    from service_requests.models import RequestLocation
                    RequestLocation.objects.create(
                        request=service_request,
                        **location_data
                    )

                    # Crear asignaciones de máquinas y operarios
                    from service_requests.models import RequestMachineryUser
                    for item in machinery_users_data:
                        RequestMachineryUser.objects.create(
                            request=service_request,
                            machinery_id=item['machinery_id'],
                            user_id=item['user_id'],
                            soil_type=item.get('soil_type'),
                            texture=item.get('texture'),
                            humidity_level=item.get('humidity_level'),
                            implementation=item.get('implementation'),
                            depth=item.get('depth'),
                            slope=item.get('slope'),
                            work_duration=item.get('work_duration')
                        )

                    # Auditoría
                    try:
                        actor_id, actor_name, actor_role_name = get_actor_info(request.user)

                        # Crear snapshot completo incluyendo modelos relacionados
                        main_snapshot = service_request_snapshot(service_request)
                        related_snapshot = service_request_related_models_snapshot(service_request)

                        # Combinar snapshots
                        combined_after = {**main_snapshot}
                        if related_snapshot.get('location'):
                            combined_after['location'] = related_snapshot['location']
                        if related_snapshot.get('machinery_users'):
                            combined_after['machinery_users'] = related_snapshot['machinery_users']

                        AuditClient(request).create(
                            object_id=str(service_request.id_request),
                            after=combined_after,
                            actor_id=actor_id,
                            actor_name=actor_name,
                            actor_role=actor_role_name,
                            permission_id=permission_id,
                            module="requests",
                            submodule="requests",
                        )
                    except Exception as e:
                        logger.warning("El servicio de auditoría ha fallado en create_request: %s", str(e))

                    # Enviar notificación de creación de solicitud
                    self._send_request_created_notification(service_request, request)

                    return Response({
                        'success': True,
                        'message': 'Solicitud creada exitosamente',
                        'id_request': service_request.id_request
                    }, status=status.HTTP_201_CREATED)

            return Response({
                'success': False,
                'message': 'Error en la validación de datos',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error inesperado al crear solicitud: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Ocurrió un error inesperado al procesar la solicitud',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'], url_path='update_request')
    def update_request(self, request, pk=None):
        """
        Actualiza parcialmente (PATCH) una solicitud usando `PreRequestUpdateSerializer`.
        Reglas:
        - Requiere permiso ID 155.
        - Solo se puede actualizar si la solicitud está en estado 20.
        """
        try:
            # Autenticación
            if not request.user.is_authenticated:
                return Response({"message": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

            # Permisos
            permission_id = 155
            if not self.check_permission(request, permission_id):
                return Response({"message": "No tiene permisos para actualizar solicitudes"}, status=status.HTTP_403_FORBIDDEN)

            # Obtener la solicitud
            service_request = get_object_or_404(ServiceRequest, pk=pk)

            # Validar estado 20
            if service_request.request_status_id != 20:
                try:
                    status_20 = Statues.objects.get(id_statues=20)
                    status_name = status_20.name
                except Statues.DoesNotExist:
                    status_name = "Estado requerido"
                return Response({
                    "message": f"La solicitud debe estar en estado '{status_name}' para poder actualizarse"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Serializador de actualización parcial
            serializer = PreRequestUpdateSerializer(
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

            # Obtener snapshots antes de la actualización
            before_request = service_request_snapshot(service_request)
            before_related = service_request_related_models_snapshot(service_request)
            
            # Guardar cambios
            with transaction.atomic():
                # Actualizar la solicitud con los datos validados
                updated_request = serializer.save()
                
                # Tomar instantánea DESPUÉS de los cambios
                after_request = service_request_snapshot(updated_request)
                after_related = service_request_related_models_snapshot(updated_request)
                
                # Registrar evento de auditoría con cambios detallados
                try:
                    actor_id, actor_name, actor_role = get_actor_info(request.user)
                    
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
                                    changes['created']['machinery_users'] = {}
                                changes['created']['machinery_users'][str(mu_id)] = mu_data
                        
                        # Verificar si se eliminó alguna maquinaria/operario
                        for mu_id in before_machinery:
                            if mu_id not in after_machinery:
                                if 'machinery_users' not in changes['removed']:
                                    changes['removed']['machinery_users'] = {}
                                changes['removed']['machinery_users'][str(mu_id)] = before_machinery[mu_id]
                    
                    # Inicializar estructura de cambios
                    diff_changes = {}

                    # Procesar cambios en la solicitud principal
                    if changes.get('changed'):
                        for field, change in changes['changed'].items():
                            if field not in ['location', 'machinery_users'] and 'to' in change:
                                diff_changes[field] = {
                                    'from': change.get('from'),
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
                                    'from': before_related.get('location', {}).get(field) if before_related.get('location') else None,
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
                                        'from': None,  # Siempre null para actualizaciones
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
                        
                except Exception as e:
                    logger.error(f"Error en auditoría al actualizar solicitud: {str(e)}", exc_info=True)

            return Response({
                'success': True,
                'message': 'solicitud actualizada exitosamente',
                'id_request': updated_request.id_request
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error actualizando solicitud: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Ocurrió un error al actualizar la solicitud',
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

    def _send_request_created_notification(self, service_request, request=None):
        """
        Envía una notificación cuando se crea una nueva solicitud de servicio.
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

            url = f"{auth_service_url.rstrip('/')}/users/users/notifications/send-solicitud-created/"
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

            payload = {
                "email": email,
                "client_name": client_name,
                "message": "Tu solicitud ha sido creada exitosamente y está siendo procesada.",
                "request_code": service_request.id_request
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"Error al enviar notificación de creación de solicitud: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error inesperado al enviar notificación de creación de solicitud: {str(e)}", exc_info=True)

    @action(detail=False, methods=['get'], url_path='generate-report')
    def generate_report(self, request):
        """
        Genera un reporte de solicitudes de servicio en formato Excel.
        
        Query parameters:
        - customer_id: ID del cliente (opcional)
        - request_status: ID del estado de la solicitud (opcional)
        - date_from: Fecha de inicio de registro (YYYY-MM-DD) (opcional)
        - date_to: Fecha de fin de registro (YYYY-MM-DD) (opcional)
        - payment_method: Código del método de pago (opcional)
        - scheduled_start_date_from: Fecha de inicio programada desde (YYYY-MM-DD) (opcional)
        - scheduled_start_date_to: Fecha de inicio programada hasta (YYYY-MM-DD) (opcional)
        """
        try:
            # 1. Verificar autenticación
            if not request.user.is_authenticated:
                return Response({
                    "success": False,
                    "message": "Usuario no autenticado"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # 2. Verificar permiso para generar reportes
            if not self.check_permission(request, 163):  # request.download_report
                return Response({
                    "success": False,
                    "message": "No tiene permisos para generar reportes"
                }, status=status.HTTP_403_FORBIDDEN)

            # 3. Validar parámetros de entrada
            serializer = ServiceRequestReportSerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Parámetros inválidos",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            customer_id = validated_data.get('customer_id')
            request_status_id = validated_data.get('request_status')
            date_from = validated_data.get('date_from')
            date_to = validated_data.get('date_to')
            payment_method_code = validated_data.get('payment_method', '').strip()
            scheduled_start_date_from = validated_data.get('scheduled_start_date_from')
            scheduled_start_date_to = validated_data.get('scheduled_start_date_to')

            # 4. Construir queryset base con optimizaciones
            queryset = ServiceRequest.objects.select_related(
                'customer', 'customer__type_document_id', 'customer__person_type',
                'request_status', 'payment_status', 'payment_method',
                'request_location', 'request_location__area_unit', 'request_location__altitude_unit'
            ).prefetch_related(
                'machinery_users__machinery',
                'machinery_users__user'
            )

            # 5. Aplicar filtros según parámetros
            if customer_id:
                queryset = queryset.filter(customer_id=customer_id)
            
            if request_status_id:
                queryset = queryset.filter(request_status_id=request_status_id)
            
            if date_from:
                queryset = queryset.filter(creation_date__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(creation_date__date__lte=date_to)
            
            if payment_method_code:
                queryset = queryset.filter(payment_method__code=payment_method_code)
            
            if scheduled_start_date_from:
                queryset = queryset.filter(scheduled_start_date__gte=scheduled_start_date_from)
            
            if scheduled_start_date_to:
                queryset = queryset.filter(scheduled_start_date__lte=scheduled_start_date_to)

            # 6. Verificar permisos de usuario (solo sus solicitudes vs todas)
            has_list_all_permission = self.check_permission(request, 149)  # service_requests.list
            has_list_own_permission = self.check_permission(request, 164)  # request.list_own
            
            if has_list_own_permission and not has_list_all_permission:
                # Usuario solo puede ver sus propias solicitudes
                user_id = getattr(request.user, 'id_user', None) or getattr(request.user, 'id', None) or getattr(request.user, 'user_id', None)
                if user_id:
                    queryset = queryset.filter(customer__id_user_id=user_id)
            elif not has_list_all_permission and not has_list_own_permission:
                # Usuario no tiene permisos para ver solicitudes
                return Response({
                    "success": False,
                    "message": "No tiene permisos para ver solicitudes"
                }, status=status.HTTP_403_FORBIDDEN)

            # 7. Verificar si hay resultados
            if not queryset.exists():
                return Response({
                    "success": True,
                    "message": "No se encontraron resultados para los criterios aplicados"
                }, status=status.HTTP_200_OK)

            # 8. Recolectar IDs de usuarios únicos (operarios y clientes)
            user_ids = set()
            for request_obj in queryset:
                # Recolectar IDs de operarios
                for machinery_user in request_obj.machinery_users.all():
                    if machinery_user.user and machinery_user.user.id_user:
                        user_ids.add(machinery_user.user.id_user)
                
                # Recolectar IDs de clientes que tienen id_user
                if request_obj.customer and request_obj.customer.id_user_id:
                    user_ids.add(request_obj.customer.id_user_id)
            
            # 9. Obtener información de usuarios en batch
            from service_requests.utils.external_user_helper import get_users_info_batch
            user_data_map = get_users_info_batch(list(user_ids), request)

            # 10. Generar reporte en formato Excel
            from service_requests.utils.report_generator import generate_excel_report
            
            report_content = generate_excel_report(queryset, user_data_map)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            file_extension = 'xlsx'

            # 11. Preparar respuesta
            from django.http import HttpResponse
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Construir nombre del archivo
            if customer_id:
                # Si se filtró por customer_id, obtener nombre del cliente
                customer = queryset.first().customer if queryset.exists() else None
                if customer:
                    # Obtener nombre del cliente (preferir datos externos si existen)
                    customer_name = ""
                    if customer.id_user_id and customer.id_user_id in user_data_map:
                        external_user = user_data_map[customer.id_user_id]
                        # Construir nombre completo desde datos externos
                        name_parts = []
                        name = external_user.get('name', '').strip()
                        first_last_name = external_user.get('first_last_name', '').strip()
                        second_last_name = external_user.get('second_last_name', '').strip()
                        
                        if name:
                            name_parts.append(name)
                        if first_last_name:
                            name_parts.append(first_last_name)
                        if second_last_name:
                            name_parts.append(second_last_name)
                        
                        customer_name = '_'.join(name_parts) if name_parts else ""
                    else:
                        # Si no hay datos externos, usar datos de la tabla customers
                        name_parts = []
                        if customer.name:
                            name_parts.append(customer.name)
                        if customer.first_last_name:
                            name_parts.append(customer.first_last_name)
                        if customer.second_last_name:
                            name_parts.append(customer.second_last_name)
                        
                        customer_name = '_'.join(name_parts) if name_parts else ""
                    
                    # Limpiar nombre para usar en archivo (remover caracteres especiales)
                    import re
                    customer_name = re.sub(r'[^\w\s-]', '', customer_name).strip()
                    customer_name = re.sub(r'[-\s]+', '_', customer_name)
                    
                    filename = f'RF_{timestamp}_{customer_name}.{file_extension}'
                else:
                    filename = f'RF_{timestamp}.{file_extension}'
            else:
                filename = f'RF_{timestamp}.{file_extension}'
            
            response = HttpResponse(report_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Log de generación de reporte
            user_id = getattr(request.user, 'id_user', None) or getattr(request.user, 'id', None) or getattr(request.user, 'user_id', None) or 'unknown'
            logger.info(f"Reporte Excel generado por usuario {user_id} - {len(queryset)} registros")
            
            return response

        except Exception as e:
            logger.error(f"Error generando reporte: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": "Error interno generando el reporte"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)