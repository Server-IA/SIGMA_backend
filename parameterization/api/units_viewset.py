from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from parameterization.models import Statues
from parameterization.models.units import Units
from parameterization.serializers.units_serializers.units_create_serializer import UnitsCreateSerializer
from parameterization.serializers.units_serializers.units_list_serializer import UnitsListSerializer
from users.permissions import HasPermissionId


class UnitsViewSet(viewsets.ViewSet):
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
        
        permission_id = 88  # units.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear unidades"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UnitsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unidad creada exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 89  # units.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar unidades"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        unit = get_object_or_404(Units, pk=pk)
        serializer = UnitsCreateSerializer(unit, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Unidad actualizada exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def list_by_category(self, request, category_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 90  # units.list_by_category
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar unidades por categoría"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        units = Units.objects.filter(id_units_categories_id=category_id)
        if not units.exists():
            return Response({
                "message": "No existen unidades registradas para esta categoría",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = UnitsListSerializer(units, many=True)
        return Response({
            "message": "Unidades por categoría obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'active/(?P<category_id>\d+)')
    def list_active_by_category(self, request, category_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 91  # units.list_active_by_category
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar unidades activas por categoría"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        units = Units.objects.filter(id_units_categories_id=category_id, id_statues_id=1)
        if not units.exists():
            return Response({
                "message": "No existen unidades activas registradas para esta categoría",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = UnitsListSerializer(units, many=True)
        return Response({
            "message": "Unidades activas por categoría obtenidas exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 92  # units.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de unidades"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            unit = Units.objects.get(pk=pk)
        except Units.DoesNotExist:
            return Response(
                {"error": "Unidad no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        if unit.id_statues_id == 1:
            try:
                unit.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Unidad desactivada exitosamente"
        else:
            try:
                unit.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Unidad activada exitosamente"

        unit.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)
