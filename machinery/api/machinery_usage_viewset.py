from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from machinery.models.machinery_usage_sheet import MachineryUsageSheet
from machinery.serializers.machinery_serializers.machinery_usage_sheet_create_serializer import MachineryUsageSheetCreateSerializer
from machinery.serializers.machinery_serializers.machinery_usage_sheet_update_serializer import MachineryUsageSheetUpdateSerializer
from machinery.serializers.machinery_serializers.machinery_usage_sheet_detail_serializer import MachineryUsageSheetDetailSerializer
from django.shortcuts import get_object_or_404
import logging

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info, machinery_usage_snapshot

logger = logging.getLogger(__name__)


class MachineryUsageViewSet(viewsets.ModelViewSet):

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

    queryset = MachineryUsageSheet.objects.all()
    serializer_class = MachineryUsageSheetCreateSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='create')
    def create_machinery_usage(self, request):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 93  # machinery_usage_sheet.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear una ficha de uso de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            data = request.data.dict() if hasattr(request.data, 'getlist') else request.data
            serializer = self.get_serializer(data=data)

            if serializer.is_valid():
                usage = serializer.save()

                after = machinery_usage_snapshot(usage)

                # Auditoría 
                try:
                    # obtener actor info centralizada
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_usage_sheet") or after.get("id_machinery") or "")

                    AuditClient(request).create(
                        object_id=object_id,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_usage_sheet",
                    )
                except Exception as e:
                    # La auditoría no debe romper la creación
                    logging.warning("El servicio de auditoría ha fallado en create_machinery_tracker: %s", e)

                return Response({"success": True, "message": "Ficha de uso registrada exitosamente."}, status=status.HTTP_201_CREATED)

            return Response({"success": False, "message": "Error de validación", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error al registrar ficha de uso: {str(e)}")
            return Response({"success": False, "message": "Error al registrar la información de uso de la maquinaria", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    @action(detail=True, methods=['put', 'patch'], url_path='update')
    def update_machinery_usage(self, request, pk=None):
        """
        Actualiza la información de uso de una maquinaria (HU-MAQ-013).
        Requiere responsible_user y justification.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 94  # machinery_usage_sheet.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar una ficha de uso de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            usage_instance = get_object_or_404(MachineryUsageSheet, pk=pk)
            before_snapshot = machinery_usage_snapshot(usage_instance)

            serializer = MachineryUsageSheetUpdateSerializer(
                usage_instance,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                updated_instance = serializer.save()

                after = machinery_usage_snapshot(updated_instance)

                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))
                    object_id = str(after.get("id_usage_sheet") or after.get("id_machinery") or "")

                    # Emitir update a auditoría (AuditClient calculará diff)
                    AuditClient(request).update(
                        object_id=object_id,
                        before=before_snapshot,
                        after=after,
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="machinery",
                        submodule="machinery_usage_sheet",
                    )
                except Exception as e:
                    logging.warning("El servicio de auditoría ha fallado en update_specific_technical_sheet: %s", e)

                
                return Response({"success": True, "message": "Información de uso actualizada correctamente"}, status=status.HTTP_200_OK)

            return Response({"success": False, "message": "Error de validación al actualizar la información de uso", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except MachineryUsageSheet.DoesNotExist:
            return Response({"success": False, "message": "La ficha de uso no existe"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al actualizar la información de uso: {str(e)}")
            return Response({"success": False, "message": "Error al actualizar la información de uso de la maquinaria", "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'], url_path=r'by-machinery/(?P<machinery_id>[^/.]+)')
    def get_by_machinery(self, request, machinery_id=None):
        """
        HU-MAQ-009: Ver detalle de información de uso por id_machinery.
        Devuelve estructura legible para UI e incluye 'missing_fields'.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 95  # machinery_usage_sheet.retrieve

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para obtener una ficha de uso de la maquinaria."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = MachineryUsageSheet.objects.select_related(
                'usage_condition', 'distance_unit', 'tenancy_type'
            ).get(id_machinery_id=machinery_id)

            data = MachineryUsageSheetDetailSerializer(instance).data
            return Response({'success': True, 'data': data}, status=status.HTTP_200_OK)
        except MachineryUsageSheet.DoesNotExist:
            return Response({'success': False, 'message': 'La maquinaria no tiene ficha de uso registrada'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error obteniendo ficha de uso por maquinaria {machinery_id}: {str(e)}")
            return Response({'success': False, 'message': 'Error al obtener la ficha de uso', 'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)

