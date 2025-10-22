from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models.types_category import TypesCategory
from parameterization.serializers.types_category_serializers.types_category_create_serializer import TypesCategoryCreateSerializer
from parameterization.serializers.types_category_serializers.types_category_list_serializer import TypesCategoryListSerializer
from users.permissions import HasPermissionId

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info
from parameterization.utils.audit_helpers import types_category_snapshot
import logging

logger = logging.getLogger(__name__)

class TypesCategoryViewSet(viewsets.ViewSet):
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
        
        permission_id = 32  # types_categories.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear categorías de tipo"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TypesCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()

            # Auditoría 
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).create(
                    object_id=str(getattr(instance, "id_types_categories", None) or getattr(instance, "id", None) or ""),
                    after=types_category_snapshot(instance),
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",               
                    submodule="types_categories",         
                )
            except Exception as e:
                logging.warning("El servicio de auditoría ha fallado en create_types_category: %s", e)

            return Response({"message": "Categoría de tipo creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 33  # types_categories.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar categorías de tipo"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            categoria = TypesCategory.objects.get(pk=pk)
        except TypesCategory.DoesNotExist:
            return Response({"error": "Categoría no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        serializer = TypesCategoryCreateSerializer(categoria, data=request.data, partial=True)
        if serializer.is_valid():

            before = types_category_snapshot(categoria)

            instance = serializer.save()

            # Auditoría 
            try:
                after = types_category_snapshot(instance)
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).update(
                    object_id=str(getattr(instance, "id_types_categories", None) or getattr(instance, "id", None) or ""),
                    before=before,
                    after=after,
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",
                    submodule="types_categories",
                )
            except Exception as e:
                logging.warning("El servicio de auditoría ha fallado en update_types_category: %s", e)

            return Response({"message": "Categoría de tipo actualizada exitosamente"},
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
        
        permission_id = 34  # types_categories.list
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar categorías de tipos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        categorias = TypesCategory.objects.all()
        serializer = TypesCategoryListSerializer(categorias, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
