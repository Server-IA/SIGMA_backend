from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from parameterization.models import Models, Brands, Statues
from parameterization.serializers.models_serializers.models_create_serializer import ModelsCreateSerializer
from parameterization.serializers.models_serializers.models_list_serializer import ModelsListSerializer
from users.permissions import HasPermissionId


class ModelsViewSet(viewsets.ViewSet):
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
        
        permission_id = 56  # models.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear modelos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ModelsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Modelo creado exitosamente"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 57  # models.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar modelos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        model = get_object_or_404(Models, pk=pk)
        serializer = ModelsCreateSerializer(model, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Modelo actualizado exitosamente"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<brand_id>\d+)')
    def list_by_brand(self, request, brand_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 58  # models.list_by_brand
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar modelos por marca"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not Brands.objects.filter(pk=brand_id).exists():
            return Response({"detail": "Brands not found."}, status=status.HTTP_404_NOT_FOUND)
        modelos = Models.objects.filter(id_brand_id=brand_id)
        serializer = ModelsListSerializer(modelos, many=True)
        return Response({
            "message": "Modelos por marca obtenidos exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<brand_id>\d+)')
    def list_active_by_brand(self, request, brand_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 59  # models.list_active_by_brand
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar modelos activos por marca"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not Brands.objects.filter(pk=brand_id).exists():
            return Response({"detail": "Brands not found."}, status=status.HTTP_404_NOT_FOUND)
        modelos = Models.objects.filter(id_brand_id=brand_id, id_statues_id=1)
        return Response({
            "message": "Modelos activos por marca obtenidos exitosamente",
            "data": ModelsListSerializer(modelos, many=True).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 60  # models.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de modelos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        model = get_object_or_404(Models, pk=pk)
        if model.id_statues_id == 1:
            try:
                model.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            msg = "Modelo desactivado exitosamente"
        else:
            try:
                model.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            msg = "Modelo activado exitosamente"
        model.save(update_fields=['id_statues'])
        return Response({"message": msg}, status=status.HTTP_200_OK)

