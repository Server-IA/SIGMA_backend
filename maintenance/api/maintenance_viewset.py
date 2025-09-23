from django.db import IntegrityError, transaction
from django.http import Http404
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction, IntegrityError
from django.http import Http404
from django.db.models import Q

from maintenance.models import Maintenance
from maintenance.serializers.maintenance_serializer import MaintenanceSerializer
from maintenance.serializers.maintenance_list_serializer import MaintenanceListSerializer

class MaintenanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Maintenance.
    """
    queryset = Maintenance.objects.select_related("maintenance_type", "maintenance_status", "id_responsible_user")
    
    def get_serializer_class(self):
        """
        Usa el serializador de lista para listar y el detallado para el resto de acciones.
        """
        if self.action == 'list':
            return MaintenanceListSerializer
        return MaintenanceSerializer
        
    def get_queryset(self):
        """
        Retorna el queryset ordenado por fecha de registro descendente.
        """
        return super().get_queryset().order_by('-registration_date')

    # Helpers
    def _not_found(self):
        return Response(
            {"success": False, "message": "Recurso no encontrado.", "errors": {"id": ["No existe el mantenimiento solicitado."]}},
            status=status.HTTP_404_NOT_FOUND,
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
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

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
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