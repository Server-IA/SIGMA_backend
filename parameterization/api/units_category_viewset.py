from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from parameterization.models.units_category import UnitsCategory
from parameterization.serializers.units_category_serializers.units_category_create_serializer import UnitsCategoryCreateSerializer
from parameterization.serializers.units_category_serializers.units_category_list_serializer import UnitsCategoryListSerializer
from users.permissions import HasPermissionId


class UnitsCategoryViewSet(viewsets.ViewSet):
    # permission_classes = [HasPermissionId]  # Temporalmente deshabilitado para debug

    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
        Adaptado de FastAPI para Django REST Framework.
        """
        # Obtener el payload del JWT desde request.auth
        payload = getattr(request, "auth", None) or {}
        
        # DEBUG: Imprimir la estructura del JWT para verificar
        print("=== DEBUG JWT PAYLOAD ===")
        print(f"Payload completo: {payload}")
        print(f"Keys disponibles: {list(payload.keys())}")
        
        # Obtener roles del payload (soporta "rol" y "roles")
        user_roles = payload.get("rol") or payload.get("roles") or []
        print(f"User roles: {user_roles}")
        
        # Extraer todos los IDs de permisos de todos los roles
        permisos_usuario = []
        for rol in user_roles:
            # Obtener permisos del rol (soporta "permisos" y "permissions")
            perms = rol.get("permisos") or rol.get("permissions") or []
            print(f"Permisos del rol {rol.get('id', 'N/A')}: {perms}")
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permisos_usuario.append(perm.get("id"))
        
        print(f"Permisos extraídos: {permisos_usuario}")
        print(f"Permiso requerido: {required_permission_id}")
        print(f"¿Tiene permiso?: {required_permission_id in permisos_usuario}")
        print("=== FIN DEBUG ===")
        
        return required_permission_id in permisos_usuario

    def create(self, request):
        permission_id = 40  # units_categories.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear categorías de unidades de medida"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UnitsCategoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de métricas de medida creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 42  # units_categories.list
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar categorías de unidades de medida"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        """Consultar todas las categorías de métricas de medida"""
        categories = UnitsCategory.objects.all()
        if not categories.exists():
            return Response({
                "message": "No existen categorías de unidades de medida registradas",
                "data": []
            }, status=status.HTTP_200_OK)
        
        serializer = UnitsCategoryListSerializer(categories, many=True)
        return Response({
            "message": "Categorías de unidades de medida obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        permission_id = 41  # units_categories.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar categorías de unidades de medida"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        """Actualizar categoría de métricas de medida por ID (PUT)"""
        category = get_object_or_404(UnitsCategory, pk=pk)
        serializer = UnitsCategoryCreateSerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Categoría de métricas de medida actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
