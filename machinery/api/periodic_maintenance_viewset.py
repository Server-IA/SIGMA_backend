from django.db import IntegrityError, transaction
from rest_framework import viewsets, mixins, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import Http404

from machinery.models import PeriodicMaintenanceScheduling
from machinery.serializers.machinery_serializers.periodic_maintenance_serializer import (
    PeriodicMaintenanceCreateUpdateSerializer,
    PeriodicMaintenanceListSerializer,
)


class PeriodicMaintenanceSchedulingViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD de mantenimientos periódicos (Paso 5).
    Filtro: ?machinery=<id>
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


    queryset = PeriodicMaintenanceScheduling.objects.select_related("maintenance", "machinery").all()

    # Solo para pruebas sin auth:
    def get_permissions(self):
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return PeriodicMaintenanceListSerializer
        return PeriodicMaintenanceCreateUpdateSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        machinery_id = self.request.query_params.get("machinery")
        if machinery_id:
            try:
                qs = qs.filter(machinery_id=int(machinery_id))
            except ValueError:
                return qs.none()

        return qs.order_by("-pk")

    def _not_found(self):
        return Response(
            {
                "success": False,
                "message": "Recurso no encontrado.",
                "errors": {"id": ["No existe el mantenimiento periódico solicitado."]},
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    
    def retrieve(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 96  # machinery_maintenance.retrieve

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para obtener un mantenimiento periódico."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()
        data = PeriodicMaintenanceListSerializer(instance).data
        return Response({"success": True, "message": "OK", "data": data}, status=status.HTTP_200_OK)

    # --- Respuestas normalizadas ---
    @transaction.atomic
    def create(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 97  # machinery_maintenance.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear un mantenimiento periódico."},
                status=status.HTTP_403_FORBIDDEN
            )


        ser = self.get_serializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
        except serializers.ValidationError as ve:
            return Response(
                {"success": False, "message": "Datos inválidos.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            instance = ser.save()
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "Registro duplicado.",
                    "errors": {"non_field_errors": ["Ya existe este mantenimiento para esta maquinaria."]},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Error inesperado.", "errors": {"detail": [str(e)]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": "Mantenimiento periódico añadido correctamente.",
                "data": PeriodicMaintenanceListSerializer(instance).data,
            },
            status=status.HTTP_201_CREATED,
        )
    @transaction.atomic
    def update(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 98  # machinery_maintenance.update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar un mantenimiento periódico."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        ser = self.get_serializer(instance, data=request.data, partial=False)
        try:
            ser.is_valid(raise_exception=True)
        except serializers.ValidationError as ve:
            return Response(
                {"success": False, "message": "Datos inválidos.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            instance = ser.save()
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "Registro duplicado.",
                    "errors": {"non_field_errors": ["Ya existe otro registro con esa combinación."]},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Error inesperado.", "errors": {"detail": [str(e)]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": "Mantenimiento periódico actualizado correctamente.",
                "data": PeriodicMaintenanceListSerializer(instance).data,
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 99  # machinery_maintenance.partial_update

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar parcialmente un mantenimiento periódico."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        ser = self.get_serializer(instance, data=request.data, partial=True)
        try:
            ser.is_valid(raise_exception=True)
        except serializers.ValidationError as ve:
            return Response(
                {"success": False, "message": "Datos inválidos.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            instance = ser.save()
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "Registro duplicado.",
                    "errors": {"non_field_errors": ["Ya existe otro registro con esa combinación."]},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Error inesperado.", "errors": {"detail": [str(e)]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": "Mantenimiento periódico actualizado correctamente.",
                "data": PeriodicMaintenanceListSerializer(instance).data,
            },
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 100  # machinery_maintenance.delete

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para eliminar un mantenimiento periódico."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        instance.delete()
        return Response(
            {"success": True, "message": "Mantenimiento periódico eliminado correctamente.", "data": None},
            status=status.HTTP_200_OK,
        )