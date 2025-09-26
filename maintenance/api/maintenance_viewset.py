from django.db import IntegrityError, transaction
from django.http import Http404
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction, IntegrityError
from django.http import Http404
from django.db.models import Q
from parameterization.models import Statues

from maintenance.models import Maintenance
from maintenance.serializers.maintenance_serializer import MaintenanceSerializer
from maintenance.serializers.maintenance_list_serializer import MaintenanceListSerializer

class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Maintenance.
    """

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

    queryset = Maintenance.objects.select_related("maintenance_type", "maintenance_status", "id_responsible_user")
    
    def get_serializer_class(self):
        """
        Usa el serializador de lista para listar y el detallado para el resto de acciones.
        """
        if self.action == 'list' or self.action == 'active':
            return MaintenanceListSerializer
        return MaintenanceSerializer
        
    def get_queryset(self):
        """
        Retorna el queryset ordenado por fecha de registro descendente.
        """
        return super().get_queryset().order_by('-registration_date')

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Lista todos los mantenimientos activos.
        """

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 106  # maintenance.list_active

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            active_status = Statues.objects.get(pk=1)  # Asumiendo que 1 es el ID para estado activo
            queryset = self.get_queryset().filter(maintenance_status=active_status)
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "message": "Mantenimientos activos listados correctamente.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Statues.DoesNotExist:
            return Response(
                {"success": False, "message": "Estado activo no encontrado.", "errors": {"detail": ["El estado activo no está configurado correctamente."]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Helpers
    def _not_found(self):
        return Response(
            {"success": False, "message": "Recurso no encontrado.", "errors": {"id": ["No existe el mantenimiento solicitado."]}},
            status=status.HTTP_404_NOT_FOUND,
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 107  # maintenance.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )


        ser = self.get_serializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
            self.perform_create(ser)
        except serializers.ValidationError as ve:
            return Response({"success": False, "message": "Datos inválidos.", "errors": ve.detail},
                            status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({"success": False, "message": "Conflicto de datos.", "errors": {"detail": ["Registro duplicado o restricción violada."]}},
                            status=status.HTTP_409_CONFLICT)
        except Exception as e:
            return Response({"success": False, "message": "Error inesperado.", "errors": {"detail": [str(e)]}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = self.get_success_headers(ser.data)
        return Response({"success": True, "message": "Mantenimiento creado correctamente."},
                        status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 108  # maintenance.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        
            return Response({
                "success": True,
                "message": "Mantenimiento actualizado correctamente."
            }, status=status.HTTP_200_OK)
    
        except Http404:
            return self._not_found()
        except Exception as e:
            if hasattr(e, 'detail'):
                return Response({
                    "errors": {
                        "detail": [str(e.detail)] if isinstance(e.detail, str) else e.detail
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            elif hasattr(e, 'get_full_details'):
                return Response({
                    "errors": {
                        "detail": [str(msg) for msg in e.detail]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "errors": {
                        "detail": [str(e)]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Toggle maintenance status between active (1) and inactive (2).
        """
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 109  # maintenance.toggle

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )


        maintenance = self.get_object()
        
        try:
            if maintenance.maintenance_status_id == 1:
                maintenance.maintenance_status = Statues.objects.get(pk=2)
                message = "Mantenimiento desactivado exitosamente"
            else:
                maintenance.maintenance_status = Statues.objects.get(pk=1)
                message = "Mantenimiento activado exitosamente"
                
            maintenance.save(update_fields=['maintenance_status'])
            return Response({"success": True, "message": message}, status=status.HTTP_200_OK)
            
        except Statues.DoesNotExist:
            return Response(
                {"success": False, "message": "Estado no válido."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Error al cambiar el estado.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 110  # maintenance.delete

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        try:
            instance.delete()
        except IntegrityError:
            return Response({"success": False, "message": "No se puede eliminar.", "errors": {"detail": ["Existen referencias a este mantenimiento."]}},
                            status=status.HTTP_409_CONFLICT)
        return Response({"success": True, "message": "Mantenimiento eliminado correctamente.", "data": None},
                        status=status.HTTP_200_OK)