from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import UserVisualParameterization
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_create_serializer import UserVisualParameterizationCreateSerializer
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_list_serializer import UserVisualParameterizationListSerializer
from parameterization.serializers.user_visual_parameterization_serializers.user_visual_parameterization_update_serializer import UserVisualParameterizationUpdateSerializer
from users.permissions import HasPermissionId

class UserVisualParameterizationViewSet(viewsets.ViewSet):
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
        
        permission_id = 122  # user_visual_parameterization.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear asignaciones de parametrización visual"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserVisualParameterizationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Asignación de parametrización visual al usuario creada exitosamente",
                    "status": "success"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    "message": f"Error al crear la asignación: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 123  # user_visual_parameterization.retrieve
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para ver asignaciones de parametrización visual"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = UserVisualParameterization.objects.get(pk=pk)
        except UserVisualParameterization.DoesNotExist:
            return Response({
                "message": "Asignación no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = UserVisualParameterizationListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 124  # user_visual_parameterization.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar asignaciones de parametrización visual"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = UserVisualParameterization.objects.get(pk=pk)
        except UserVisualParameterization.DoesNotExist:
            return Response({
                "message": "Asignación no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserVisualParameterizationUpdateSerializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Asignación actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la asignación: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 125  # user_visual_parameterization.partial_update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar parcialmente asignaciones de parametrización visual"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = UserVisualParameterization.objects.get(pk=pk)
        except UserVisualParameterization.DoesNotExist:
            return Response({
                "message": "Asignación no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserVisualParameterizationUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Asignación actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la asignación: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_asignaciones(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 126  # user_visual_parameterization.list
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar asignaciones de parametrización visual"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        asignaciones = UserVisualParameterization.objects.all()
        serializer = UserVisualParameterizationListSerializer(asignaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)