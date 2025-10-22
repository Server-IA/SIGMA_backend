from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import Brands, BrandsCategory, Statues
from parameterization.serializers.brands_serializers.brands_create_serializer import BrandsCreateSerializer
from parameterization.serializers.brands_serializers.brands_list_serializer import BrandsListSerializer
from django.shortcuts import get_object_or_404
from users.permissions import HasPermissionId

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info
from parameterization.utils.audit_helpers import brands_snapshot
import logging

logger = logging.getLogger(__name__)

class BrandsViewSet(viewsets.ViewSet):
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
        
        permission_id = 51  # brands.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear marcas"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BrandsCreateSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()

            # Auditoría
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).create(
                    object_id=str(getattr(instance, "id_brands", None) or getattr(instance, "id", None) or ""),
                    after=brands_snapshot(instance),
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",               
                    submodule="brands",         
                )
            except Exception as e:
                logging.warning("El servicio de auditoría ha fallado en create_brands: %s", e)

            return Response({"message": "Marca creada exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 52  # brands.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar marcas"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        brand = get_object_or_404(Brands, pk=pk)

        serializer = BrandsCreateSerializer(brand, data=request.data, partial=True)
        if serializer.is_valid():
            before = brands_snapshot(brand)

            instance = serializer.save()

            # Auditoría
            try:
                after = brands_snapshot(instance)
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).update(
                    object_id=str(getattr(instance, "id_brands", None) or getattr(instance, "id", None) or ""),
                    before=before,
                    after=after,
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",               
                    submodule="brands",         
                )
            except Exception as e:
                logging.warning("El servicio de auditoría ha fallado en update_brands: %s", e)

            return Response({"message": "Marca actualizada exitosamente"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<category_id>\d+)')
    def list_by_category(self, request, category_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 53  # brands.list_by_category
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar marcas por categoría"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not BrandsCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "BrandsCategory not found."}, status=status.HTTP_404_NOT_FOUND)

        brands = Brands.objects.filter(id_brands_categories_id=category_id)
        serializer = BrandsListSerializer(brands, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<category_id>\d+)')
    def list_active_by_category(self, request, category_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 54  # brands.list_active_by_category
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar marcas activas por categoría"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not BrandsCategory.objects.filter(pk=category_id).exists():
            return Response({"detail": "BrandsCategory not found."}, status=status.HTTP_404_NOT_FOUND)
        marcas = Brands.objects.filter(id_brands_categories_id=category_id, id_statues_id=1)
        if not marcas.exists():
            return Response({
                "message": "No existen marcas activas registradas para esta categoría",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = BrandsListSerializer(marcas, many=True)
        return Response({
            "message": "Marcas activas por categoría obtenidas exitosamente",
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
        
        permission_id = 55  # brands.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de marcas"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        brand = get_object_or_404(Brands, pk=pk)

        if brand.id_statues_id == 1:
            try:
                brand.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            message = "Marca desactivada exitosamente"
        else:
            try:
                brand.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            message = "Marca activada exitosamente"

        brand.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)


