from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import logging

from maintenance.models import MaintenanceSpareParts
from maintenance.serializers.maintenance_spare_parts_serializers import (
    MaintenanceSparePartsCreateSerializer,
    MaintenanceSparePartsListSerializer
)

logger = logging.getLogger(__name__)


class MaintenanceSparePartsViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de repuestos de mantenimiento.
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

    @action(detail=False, methods=['post'], url_path='create')
    def create_spare_part(self, request):
        """
        Crea un nuevo repuesto de mantenimiento.
        
        Campos requeridos:
        - spare_part_brand: ID de la marca (debe pertenecer a categoría 4)
        - name: Nombre del repuesto
        - spare_parts_cost: Precio por parte
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 132  # maintenance_spare_parts.create
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear repuestos de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            serializer = MaintenanceSparePartsCreateSerializer(
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                instance = serializer.save()
                return Response(
                    {
                        "success": True,
                        "message": "Repuesto de mantenimiento creado exitosamente",
                        "data": {
                            "id_maintenance_spare_parts": instance.id_maintenance_spare_parts,
                            "name": instance.name,
                            "spare_parts_cost": instance.spare_parts_cost
                        }
                    },
                    status=status.HTTP_201_CREATED
                )
                
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error creando repuesto de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el repuesto de mantenimiento",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='list')
    def list_spare_parts(self, request):
        """
        Lista todos los repuestos de mantenimiento con información de marcas.
        
        Incluye:
        - Información básica del repuesto
        - Información de la marca y su categoría
        - Costo total calculado
        """
        
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Permisos deshabilitados temporalmente
        permission_id = 133  # maintenance_spare_parts.list
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar repuestos de mantenimiento."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            queryset = MaintenanceSpareParts.objects.select_related(
                'spare_part_brand',
                'spare_part_brand__id_brands_categories'
            ).all().order_by('-registration_date')
            
            serializer = MaintenanceSparePartsListSerializer(queryset, many=True)
            
            return Response(
                {
                    "success": True,
                    "message": "Lista de repuestos de mantenimiento obtenida exitosamente",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Error listando repuestos de mantenimiento: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": "Error al obtener la lista de repuestos de mantenimiento",
                    "details": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
