from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from machinery.models.machinery_tracker_sheet import MachineryTrackerSheet
from machinery.serializers.machinery_serializers.machinery_tracker_sheet_create_serializer import MachineryTrackerSheetCreateSerializer
from machinery.serializers.machinery_serializers.machinery_tracker_sheet_update_serializer import MachineryTrackerSheetUpdateSerializer
from machinery.serializers.machinery_serializers.machinery_tracker_detail_serializer import MachineryTrackerDetailSerializer

from django.shortcuts import get_object_or_404
import logging

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, machinery_tracker_snapshot


logger = logging.getLogger(__name__)

class MachineryTrackerViewSet(viewsets.ModelViewSet):
    """
    ViewSet para manejar el modelo MachineryTracker.
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

    queryset = MachineryTrackerSheet.objects.all()
    serializer_class = MachineryTrackerSheetCreateSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='create')
    def create_machinery_tracker(self, request):
        """
        Crea un registro de MachineryTracker
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 87  # machinery_tracker.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear una ficha de seguimiento de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            data = request.data.dict() if hasattr(request.data, 'getlist') else request.data

            # Verificar si ya existe un tracker para esta maquinaria
            machinery_id = data.get('id_machinery')
            if machinery_id and MachineryTrackerSheet.objects.filter(id_machinery_id=machinery_id).exists():
                return Response(
                    {
                        "success": False,
                        "message": "Error al crear la ficha tecnica de seguimiento de la maquinaria",
                        "details": "Esta maquinaria ya tiene una ficha tecnica de seguimiento asociada."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                # guardar
                tracker = serializer.save()

                # --- Auditoría ---
                try:
                    # obtener actor info centralizada
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    after = machinery_tracker_snapshot(tracker)
                    object_id = str(after.get("id_tracker_sheet") or after.get("id_machinery") or "")

                    AuditClient(request).create(
                        object_id=object_id,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_tracker_sheet",
                    )
                except Exception as e:
                    # La auditoría no debe romper la creación
                    logging.warning("El servicio de auditoría ha fallado en create_machinery_tracker: %s", e)

                return Response(
                    {
                        "success": True,
                        "message": "Ficha tecnica de seguimiento de la maquinaria creado exitosamente"
                    },
                    status=status.HTTP_201_CREATED
                )

            # validación fallida
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            error_message = str(e)
            # Extraer el mensaje de error específico si está en el formato de validación
            if hasattr(e, 'detail') and isinstance(e.detail, dict) and 'id_machinery' in e.detail:
                error_message = str(e.detail['id_machinery'][0])

            logger.error(f"Error al crear la ficha tecnica de seguimiento de la maquinaria: {error_message}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear la ficha tecnica de seguimiento de la maquinaria",
                    "details": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    @action(detail=True, methods=['put'], url_path='update')
    def update_machinery_tracker(self, request, pk=None):
        """
        Actualiza una ficha técnica de seguimiento de la maquinaria.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 88  # machinery_tracker.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar la ficha de seguimiento de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )


        try:
            tracker_instance = get_object_or_404(MachineryTrackerSheet, pk=pk)

            before = machinery_tracker_snapshot(tracker_instance)

            serializer = MachineryTrackerSheetUpdateSerializer(
                tracker_instance,
                data=request.data,
                partial=True,  
                context={'request': request}
            )

            if serializer.is_valid():
                updated_instance = serializer.save()

                after = machinery_tracker_snapshot(updated_instance)

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_tracker_sheet") or after.get("id_machinery") or "")

                    AuditClient(request).update(
                        object_id=object_id,
                        before=before,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_tracker_sheet",
                    )
                except Exception as e:
                    logging.warning(
                        "El servicio de auditoría ha fallado en update_machinery_general_sheet: %s", e
                    )
                
                return Response(
                    {
                        "success": True,
                        "message": "Ficha técnica de seguimiento actualizada correctamente"
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {
                    "success": False,
                    "message": "Error de validación al actualizar la ficha técnica",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except MachineryTrackerSheet.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "La ficha técnica de seguimiento no existe",
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al actualizar la ficha técnica: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al actualizar la ficha técnica de seguimiento de la maquinaria",
                    "details": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='by-machinery/(?P<machinery_id>[^/.]+)')
    def get_detail_by_machinery(self, request, machinery_id=None):
        """
        Obtiene el detalle del tracker de maquinaria basado en el ID de la maquinaria.
        """
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 89  # machinery_tracker.retrieve

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para ver la ficha de seguimiento de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Buscar la ficha por el ID de la maquinaria
            tracker_instance = MachineryTrackerSheet.objects.get(id_machinery_id=machinery_id)
            serializer = MachineryTrackerDetailSerializer(tracker_instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except MachineryTrackerSheet.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "No se encontró ficha técnica para la maquinaria especificada"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al obtener el detalle: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener el detalle de la maquinaria",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )