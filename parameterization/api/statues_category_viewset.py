from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import StatuesCategory
from parameterization.serializers.statues_category_serializers.statues_category_create_serializer import StatuesCategoryCreateSerializer
from parameterization.serializers.statues_category_serializers.statues_category_list_serializer import StatuesCategoryListSerializer
from users.permissions import HasPermissionId

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info
from parameterization.utils.audit_helpers import statues_category_snapshot
import logging

logger = logging.getLogger(__name__)


class StatuesCategoryViewSet(viewsets.ViewSet):
    # permission_classes = [HasPermissionId]  # Temporalmente deshabilitado para usar check_permission

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

    def create(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 26  # statues_categories.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear categorías de estado"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StatuesCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()

            # Auditoría 
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).create(
                    object_id=str(getattr(instance, "id_statues_categories", None) or getattr(instance, "id", None) or ""),
                    after=statues_category_snapshot(instance),
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",               
                    submodule="statues_categories",         
                )
            except Exception as e:
                # Logueamos la falla de auditoría, pero NO rompemos la creación
                logging.warning("El servicio de auditoría ha fallado en create_statues_category: %s", e)

            return Response({"message": "Categoría de estado creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 27  # statues_categories.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar categorías de estado"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            categoria = StatuesCategory.objects.get(pk=pk)
        except StatuesCategory.DoesNotExist:
            return Response({"error": "Categoría no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = StatuesCategoryCreateSerializer(categoria, data=request.data, partial=True)
        if serializer.is_valid():

            before = statues_category_snapshot(categoria)

            instance = serializer.save()

            # Auditoría 
            try:
                after = statues_category_snapshot(instance)
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).update(
                    object_id=str(getattr(instance, "id_statues_categories", None) or getattr(instance, "id", None) or ""),
                    before=before,
                    after=after,
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",
                    submodule="statues_categories",
                )
            except Exception as e:
                logging.warning("El servicio de auditoría ha fallado en update_statues_category: %s", e)

            return Response({"message": "Categoría de estado actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_categorias(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 28  # statues_categories.list
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar categorías de estado"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        categorias = StatuesCategory.objects.all()
        serializer = StatuesCategoryListSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
