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
        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()
        data = PeriodicMaintenanceListSerializer(instance).data
        return Response({"success": True, "message": "OK", "data": data}, status=status.HTTP_200_OK)

    # --- Respuestas normalizadas ---
    @transaction.atomic
    def create(self, request, *args, **kwargs):
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
        try:
            instance = self.get_object()
        except Http404:
            return self._not_found()

        instance.delete()
        return Response(
            {"success": True, "message": "Mantenimiento periódico eliminado correctamente.", "data": None},
            status=status.HTTP_200_OK,
        )