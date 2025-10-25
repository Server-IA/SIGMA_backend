from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction

from machinery.models import (
    ToleranceThresholds,
    OBDFaultMachinery,
    EventTypeMachinery,
    Machinery
)
from machinery.serializers.machinery_serializers.machinery_tolerance_thresholds_detail_serializer import (
    MachineryToleranceThresholdsDetailSerializer,
    ToleranceThresholdsDetailSerializer,
    OBDFaultMachineryDetailSerializer,
    EventTypeMachineryDetailSerializer
)
from machinery.serializers.machinery_serializers.machinery_tolerance_thresholds_create_serializer import (
    MachineryToleranceThresholdsCreateSerializer
)
from machinery.serializers.machinery_serializers.machinery_tolerance_thresholds_update_serializer import (
    MachineryToleranceThresholdsUpdateSerializer
)
# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import (
    get_actor_info,
    tolerance_thresholds_snapshot,
    obd_fault_machinery_snapshot,
    event_type_machinery_snapshot
)

class MachineryToleranceThresholdsViewSet(viewsets.ViewSet):

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

    @action(detail=False, methods=['post'], url_path='create')
    def create_tolerance_thresholds(self, request):
        """
        Crea configuraciones de tolerancia, fallos OBD y tipos de eventos para una maquinaria.

        Validaciones específicas:
        - El endpoint solo se puede usar una vez por maquinaria
        - Si ya existe algún registro en tolerance_thresholds, obd_fault_machinery o event_type_machinery
          para la maquinaria especificada, se rechaza la petición

        Campos requeridos:
        - id_machinery: ID de la maquinaria
        - tolerance_thresholds: Array de configuraciones de tolerancia (debe tener al menos 1 elemento)
        - obd_fault_machinery: Array de fallos OBD (opcional)
        - event_type_machinery: Array de tipos de eventos (opcional)

        Campos obligatorios en cada item:
        - tolerance_thresholds: id_parameter, alert_enabled
        - obd_fault_machinery: id_obd_fault, alert_enabled
        - event_type_machinery: id_event_type, alert_enabled, threshold (si id_event_type está presente)

        Validaciones específicas:
        - alert_enabled es OBLIGATORIO cuando se proporciona el ID principal
        - alert_enabled tiene valor por defecto True si no se especifica
        - tolerance_thresholds: parámetro ID no puede ser 1, 2, 4, 5, 13, 16, 17
        - event_type_machinery: threshold debe estar en rango del parámetro ID 17
        """

        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 164

        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear configuraciones de tolerancia de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = MachineryToleranceThresholdsCreateSerializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                id_machinery = serializer.validated_data['id_machinery']

                existing_tolerance = ToleranceThresholds.objects.filter(id_machinery=id_machinery).exists()
                existing_obd_fault = OBDFaultMachinery.objects.filter(id_machinery=id_machinery).exists()
                existing_event_type = EventTypeMachinery.objects.filter(id_machinery=id_machinery).exists()

                if existing_tolerance or existing_obd_fault or existing_event_type:
                    return Response(
                        {
                            "success": False,
                            "message": "Ya existen umbrales de tolerancia previas para esta maquinaria"
                        },
                        status=status.HTTP_409_CONFLICT
                    )

                result = serializer.save()

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    # Crear snapshot simplificado - solo id_machinery ya que object_id ya lo incluye
                    combined_after = {
                        "id_machinery": id_machinery.id_machinery,
                        "machinery_name": id_machinery.machinery_name
                    }

                    # Agregar snapshots de los registros creados
                    created_records = result['created_records']

                    # Snapshots detallados de cada tipo de registro
                    tolerance_snapshots = []
                    for threshold in created_records['tolerance_thresholds']:
                        tolerance_snapshots.append(tolerance_thresholds_snapshot(threshold))

                    obd_fault_snapshots = []
                    for obd_fault in created_records['obd_fault_machinery']:
                        obd_fault_snapshots.append(obd_fault_machinery_snapshot(obd_fault))

                    event_type_snapshots = []
                    for event_type in created_records['event_type_machinery']:
                        event_type_snapshots.append(event_type_machinery_snapshot(event_type))

                    # Combinar todos los snapshots
                    if tolerance_snapshots:
                        combined_after['tolerance_thresholds'] = tolerance_snapshots
                    if obd_fault_snapshots:
                        combined_after['obd_fault_machinery'] = obd_fault_snapshots
                    if event_type_snapshots:
                        combined_after['event_type_machinery'] = event_type_snapshots

                    AuditClient(request).create(
                        object_id=str(id_machinery.id_machinery),
                        after=combined_after,
                        actor_id=str(actor_id) if actor_id is not None else None,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=164,  # machinery.tolerance_thresholds.create
                        module="machinery",
                        submodule="tolerance_thresholds",
                    )
                except Exception as e:
                    # Si la auditoría falla, solo loguear warning pero no fallar la operación
                    import logging
                    logging.warning("El servicio de auditoría ha fallado en create_tolerance_thresholds: %s", e)

                return Response(
                    {
                        "success": True,
                        "message": "Umbrales de tolerancia creados exitosamente"
                    },
                    status=status.HTTP_201_CREATED
                )

            return Response(
                {
                    "success": False,
                    "message": "Error en los datos proporcionados",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error creating tolerance thresholds: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": f"Error al crear las configuraciones de tolerancia: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['patch'], url_path='update')
    def update_tolerance_thresholds(self, request):
        """
        Actualiza configuraciones de tolerancia, fallos OBD y tipos de eventos para una maquinaria.

        Funcionamiento:
        - Elimina todas las configuraciones existentes para la maquinaria
        - Crea las nuevas configuraciones con las mismas validaciones del endpoint create

        Query Parameters:
        - machinery_id: ID de la maquinaria (requerido)

        Campos requeridos en el JSON body:
        - tolerance_thresholds: Array de configuraciones de tolerancia (OBLIGATORIO, debe tener al menos 1 elemento)
        - obd_fault_machinery: Array de fallos OBD (opcional)
        - event_type_machinery: Array de tipos de eventos (opcional)

        Campos obligatorios en cada item:
        - tolerance_thresholds: id_parameter, alert_enabled
        - obd_fault_machinery: id_obd_fault, alert_enabled
        - event_type_machinery: id_event_type, alert_enabled, threshold

        Validaciones específicas:
        - alert_enabled es OBLIGATORIO cuando se proporciona el ID principal
        - tolerance_thresholds: parámetro ID no puede ser 1, 2, 4, 5, 13, 16, 17
        - event_type_machinery: threshold debe estar en rango del parámetro ID 17

        Permisos:
        - Requiere permiso ID 166 (machinery.tolerance_thresholds.update)
        """

        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not self.check_permission(request, 166):
            return Response(
                {"message": "No tiene permisos para actualizar configuraciones de tolerancia de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener el ID de maquinaria del query parameter
            machinery_id = request.query_params.get('machinery_id')

            if not machinery_id:
                return Response(
                    {
                        "success": False,
                        "message": "El parámetro 'machinery_id' es obligatorio"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que la maquinaria existe
            try:
                machinery = Machinery.objects.get(id_machinery=machinery_id)
            except Machinery.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": f"No se encontró la maquinaria con ID {machinery_id}"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verificar que existan configuraciones previas para actualizar
            existing_tolerance = ToleranceThresholds.objects.filter(id_machinery=machinery).exists()
            existing_obd_fault = OBDFaultMachinery.objects.filter(id_machinery=machinery).exists()
            existing_event_type = EventTypeMachinery.objects.filter(id_machinery=machinery).exists()

            if not (existing_tolerance or existing_obd_fault or existing_event_type):
                return Response(
                    {
                        "success": False,
                        "message": "No existen configuraciones previas para actualizar en esta maquinaria"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Crear serializer con contexto del machinery_id
            serializer = MachineryToleranceThresholdsUpdateSerializer(
                data=request.data,
                context={'machinery_id': machinery_id, 'request': request}
            )

            if serializer.is_valid():
                result = serializer.create(serializer.validated_data)

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    # Crear snapshot simplificado - solo id_machinery ya que object_id ya lo incluye
                    combined_after = {
                        "id_machinery": machinery.id_machinery,
                        "machinery_name": machinery.machinery_name
                    }

                    # Agregar snapshots de los registros actualizados
                    updated_records = result['updated_records']

                    # Snapshots detallados de cada tipo de registro
                    tolerance_snapshots = []
                    for threshold in updated_records['tolerance_thresholds']:
                        tolerance_snapshots.append(tolerance_thresholds_snapshot(threshold))

                    obd_fault_snapshots = []
                    for obd_fault in updated_records['obd_fault_machinery']:
                        obd_fault_snapshots.append(obd_fault_machinery_snapshot(obd_fault))

                    event_type_snapshots = []
                    for event_type in updated_records['event_type_machinery']:
                        event_type_snapshots.append(event_type_machinery_snapshot(event_type))

                    # Combinar todos los snapshots
                    if tolerance_snapshots:
                        combined_after['tolerance_thresholds'] = tolerance_snapshots
                    if obd_fault_snapshots:
                        combined_after['obd_fault_machinery'] = obd_fault_snapshots
                    if event_type_snapshots:
                        combined_after['event_type_machinery'] = event_type_snapshots

                    AuditClient(request).update(
                        object_id=str(machinery.id_machinery),
                        after=combined_after,
                        actor_id=str(actor_id) if actor_id is not None else None,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=166,  # machinery.tolerance_thresholds.update
                        module="machinery",
                        submodule="tolerance_thresholds",
                    )
                except Exception as e:
                    # Si la auditoría falla, solo loguear warning pero no fallar la operación
                    import logging
                    logging.warning("El servicio de auditoría ha fallado en update_tolerance_thresholds: %s", e)

                return Response(
                    {
                        "success": True,
                        "message": "Umbrales de tolerancia actualizados exitosamente"
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    "success": False,
                    "message": "Error en los datos proporcionados",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error al actualizar las configuraciones de tolerancia: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='detail')
    def get_tolerance_thresholds_detail(self, request):
        """
        Obtiene detalles completos de configuraciones de tolerancia por maquinaria.

        Query Parameters:
        - machinery_id: ID de la maquinaria (requerido)

        Returns:
            JSON con detalles completos incluyendo nombres de parámetros, códigos OBD,
            nombres de tipos de eventos y nombres de mantenimiento.

        Permisos:
        - Requiere permiso ID 165 (machinery.tolerance_thresholds.detail)
        """

        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not self.check_permission(request, 165):
            return Response(
                {"message": "No tiene permisos para ver detalles de configuraciones de tolerancia de maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener el ID de maquinaria del query parameter
            machinery_id = request.query_params.get('machinery_id')

            if not machinery_id:
                return Response(
                    {
                        "success": False,
                        "message": "El parámetro 'machinery_id' es obligatorio"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que la maquinaria existe
            try:
                machinery = Machinery.objects.get(id_machinery=machinery_id)
            except Machinery.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": f"No se encontró la maquinaria con ID {machinery_id}"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Obtener todos los registros relacionados
            tolerance_thresholds = ToleranceThresholds.objects.filter(id_machinery=machinery)
            obd_fault_machinery = OBDFaultMachinery.objects.filter(id_machinery=machinery)
            event_type_machinery = EventTypeMachinery.objects.filter(id_machinery=machinery)

            # Verificar que existan configuraciones para esta maquinaria
            total_configurations = tolerance_thresholds.count() + obd_fault_machinery.count() + event_type_machinery.count()

            if total_configurations == 0:
                return Response(
                    {
                        "success": False,
                        "message": f"No se encontraron configuraciones de tolerancia para la maquinaria con ID {machinery_id}"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serializar cada tipo de configuración por separado
            tolerance_serializer = ToleranceThresholdsDetailSerializer(tolerance_thresholds, many=True)
            obd_fault_serializer = OBDFaultMachineryDetailSerializer(obd_fault_machinery, many=True)
            event_type_serializer = EventTypeMachineryDetailSerializer(event_type_machinery, many=True)

            return Response(
                {
                    "success": True,
                    "message": "Detalles de configuraciones de tolerancia obtenidos exitosamente",
                    "data": {
                        "id_machinery": machinery.id_machinery,
                        "machinery_name": machinery.machinery_name,
                        "tolerance_thresholds": tolerance_serializer.data,
                        "obd_fault_machinery": obd_fault_serializer.data,
                        "event_type_machinery": event_type_serializer.data
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error al obtener los detalles de configuraciones de tolerancia: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )