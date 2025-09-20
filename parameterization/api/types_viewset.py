from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import Types, TypesCategory, Statues
from parameterization.serializers.types_serializers.types_create_serializer import TypesCreateSerializer
from parameterization.serializers.types_serializers.types_list_serializer import TypesListSerializer
from users.permissions import HasPermissionId


class TypesViewSet(viewsets.ViewSet):
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
        
        permission_id = 35  # types.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear tipos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TypesCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Tipo creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 36  # types.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar tipos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            tipo = Types.objects.get(pk=pk)
        except Types.DoesNotExist:
            return Response(
                {"error": "Tipo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TypesCreateSerializer(tipo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Tipo actualizado exitosamente"},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def listar_por_categoria(self, request, category_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 37  # types.list_by_category
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar tipos por categoría"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not TypesCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "TypesCategory not found."},
                            status=status.HTTP_404_NOT_FOUND)

        tipos = Types.objects.filter(id_types_categories_id=category_id)
        serializer = TypesListSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<category_id>\d+)')
    def listar_activos_por_categoria(self, request, category_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 38  # types.list_active_by_category
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar tipos activos por categoría"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not TypesCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "TypesCategory not found."},
                            status=status.HTTP_404_NOT_FOUND)
        tipos = Types.objects.filter(
            id_types_categories_id=category_id,
            id_statues_id=1
        )
        serializer = TypesListSerializer(tipos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 39  # types.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de tipos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            tipo = Types.objects.get(pk=pk)
        except Types.DoesNotExist:
            return Response(
                {"error": "Tipo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )

        if tipo.id_statues_id == 1:
            try:
                tipo.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Tipo desactivado exitosamente"
        else:
            try:
                tipo.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Tipo activado exitosamente"

        tipo.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)