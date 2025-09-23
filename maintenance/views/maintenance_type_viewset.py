from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from parameterization.models import Types
from maintenance.serializers.maintenance_type_serializer import MaintenanceTypeSerializer

class MaintenanceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = MaintenanceTypeSerializer

    def get_queryset(self):
        return Types.objects.filter(
            id_types_categories_id=1,  # categoría de “tipos de mantenimiento”
            id_statues_id=1,           # activos
        ).order_by("name")