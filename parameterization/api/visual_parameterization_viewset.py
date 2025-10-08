from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import VisualParameterization, Statues
from parameterization.serializers.visual_parameterization_serializers.visual_parameterization_create_serializer import VisualParameterizationCreateSerializer
from parameterization.serializers.visual_parameterization_serializers.visual_parameterization_list_serializer import VisualParameterizationListSerializer
from parameterization.serializers.visual_parameterization_serializers.visual_parameterization_update_serializer import VisualParameterizationUpdateSerializer
from users.permissions import HasPermissionId

class VisualParameterizationViewSet(viewsets.ViewSet):
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
        
        permission_id = 71  # visual_parameterization.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear parametrizaciones visuales"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = VisualParameterizationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Parametrización visual creada exitosamente",
                    "status": "success"
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    "message": f"Error al crear la parametrización visual: {str(e)}",
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
        
        permission_id = 72  # visual_parameterization.retrieve
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para ver parametrizaciones visuales"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response({
                "message": "Parametrización visual no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = VisualParameterizationListSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 73  # visual_parameterization.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar parametrizaciones visuales"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response({
                "message": "Parametrización visual no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = VisualParameterizationUpdateSerializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Parametrización visual actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la parametrización visual: {str(e)}",
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
        
        permission_id = 74  # visual_parameterization.partial_update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar parcialmente parametrizaciones visuales"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            instance = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response({
                "message": "Parametrización visual no encontrada",
                "status": "error"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = VisualParameterizationUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Parametrización visual actualizada exitosamente",
                    "status": "success"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    "message": f"Error al actualizar la parametrización visual: {str(e)}",
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                "message": "Datos de entrada inválidos",
                "errors": serializer.errors,
                "status": "error"
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list', authentication_classes=[], permission_classes=[])
    def listar_parametrizaciones(self, request):
        """
        Lista todas las parametrizaciones visuales sin requerir autenticación.
        Las parametrizaciones se ordenan por id_visual_parameterization de forma ascendente.
        """
        parametrizaciones = VisualParameterization.objects.all().order_by('id_visual_parameterization')
        serializer = VisualParameterizationListSerializer(parametrizaciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 76  # visual_parameterization.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de parametrizaciones visuales"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            parametrizacion = VisualParameterization.objects.get(pk=pk)
        except VisualParameterization.DoesNotExist:
            return Response(
                {"error": "Parametrización visual no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Se asume que 1 = Activo, 2 = Inactivo
        if parametrizacion.visual_parameterization_status_id == 1:
            try:
                parametrizacion.visual_parameterization_status = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response(
                    {"error": "El estado con id=2 no existe"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            message = "Parametrización visual desactivada exitosamente"
        else:
            try:
                parametrizacion.visual_parameterization_status = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response(
                    {"error": "El estado con id=1 no existe"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            message = "Parametrización visual activada exitosamente"

        parametrizacion.save(update_fields=['visual_parameterization_status'])
        return Response({"message": message}, status=status.HTTP_200_OK)
