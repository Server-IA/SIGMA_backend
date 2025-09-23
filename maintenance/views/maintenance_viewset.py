from django.db import IntegrityError, transaction
from django.http import Http404
from rest_framework import viewsets, mixins, status, serializers
from rest_framework.permissions import AllowAny  # <- temporal
from rest_framework.response import Response

from maintenance.models import Maintenance
from maintenance.serializers.maintenance_serializer import (
    MaintenanceSerializer,
    MaintenanceListSerializer,
)

# ---- TEMPORAL: quitar en contexto de auth ----
from django.contrib.auth import get_user_model
FAKE_USER_ID = 1
# ------------------------------------------------


class MaintenanceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD de Maintenance.
    Filtros soportados (query params):
        - ?maintenance_type=<id>
        - ?maintenance_status=<id>
    """

    queryset = (
        Maintenance.objects.select_related(
            "maintenance_type",
            "maintenance_type__id_statues",
            "maintenance_status",         
            "id_responsible_user",
        )
        .all()
        .order_by("-id_maintenance")
    )

    # permission_classes = [IsAuthenticated]  # <- habilitar cuando haya auth 
    permission_classes = [AllowAny]  # <- temporal para pruebas

    def get_serializer_class(self):
        if self.action == "list":
            return MaintenanceListSerializer
        return MaintenanceSerializer

    # ---- TEMPORAL: usuario “fake” mientras no hay auth ----
    def _actor_user(self):
        u = getattr(self.request, "user", None)
        if u and getattr(u, "is_authenticated", False):
            return u
        User = get_user_model()
        try:
            return User.objects.get(pk=FAKE_USER_ID)
        except User.DoesNotExist:
            return User.objects.create(
                username="dev",
                email="dev@example.com",
                is_staff=True,
                is_active=True,
            )

    # ---------- Filtros ----------
    def get_queryset(self):
        qs = super().get_queryset()
        mt = self.request.query_params.get("maintenance_type")
        ms = self.request.query_params.get("maintenance_status")
        if mt:
            try:
                qs = qs.filter(maintenance_type_id=int(mt))
            except ValueError:
                qs = qs.none()
        if ms:
            try:
                qs = qs.filter(maintenance_status_id=int(ms))
            except ValueError:
                qs = qs.none()
        return qs

    # ---------- Helpers ----------
    def _not_found(self):
        return Response(
            {
                "success": False,
                "message": "Recurso no encontrado.",
                "errors": {"id": ["No existe el mantenimiento solicitado."]},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # ---------- Hooks ----------
    def perform_create(self, serializer):
        serializer.save(id_responsible_user=self._actor_user())  # TEMP

    def perform_update(self, serializer):
        serializer.save(id_responsible_user=self._actor_user())  # TEMP

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
            self.perform_create(ser)
        except serializers.ValidationError as ve:
            return Response(
                {"success": False, "message": "Datos inválidos.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "Conflicto de datos.",
                    "errors": {"detail": ["Registro duplicado o restricción violada."]},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Error inesperado.", "errors": {"detail": [str(e)]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        headers = self.get_success_headers(ser.data)
        return Response(
            {"success": True, "message": "Mantenimiento creado correctamente.", "data": ser.data},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()
        data = self.get_serializer(instance).data
        return Response({"success": True, "message": "OK", "data": data}, status=status.HTTP_200_OK)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        ser = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            ser.is_valid(raise_exception=True)
            self.perform_update(ser)
        except serializers.ValidationError as ve:
            return Response(
                {"success": False, "message": "Datos inválidos.", "errors": ve.detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "Conflicto de datos.",
                    "errors": {"detail": ["Registro duplicado o restricción violada."]},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": "Error inesperado.", "errors": {"detail": [str(e)]}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {"success": True, "message": "Mantenimiento actualizado correctamente.", "data": ser.data},
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        try:
            instance.delete()
        except IntegrityError:
            return Response(
                {
                    "success": False,
                    "message": "No se puede eliminar.",
                    "errors": {"detail": ["Existen referencias a este mantenimiento."]},
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {"success": True, "message": "Mantenimiento eliminado correctamente.", "data": None},
            status=status.HTTP_200_OK,
        )