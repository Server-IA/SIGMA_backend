from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from machinery.models.machinery_usage_sheet import MachineryUsageSheet
from machinery.serializers.machinery_serializers.machinery_usage_sheet_create_serializer import MachineryUsageSheetCreateSerializer
import logging


logger = logging.getLogger(__name__)


class MachineryUsageViewSet(viewsets.ModelViewSet):

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

    queryset = MachineryUsageSheet.objects.all()
    serializer_class = MachineryUsageSheetCreateSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=['post'], url_path='create')
    def create_machinery_usage(self, request):

        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 93  # machinery_usage_sheet.create

        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar maquinaria"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            data = request.data.dict() if hasattr(request.data, 'getlist') else request.data
            serializer = self.get_serializer(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response({"success": True, "message": "Ficha de uso registrada exitosamente."}, status=status.HTTP_201_CREATED)

            return Response({"success": False, "message": "Error de validación", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error al registrar ficha de uso: {str(e)}")
            return Response({"success": False, "message": "Error al registrar la información de uso de la maquinaria", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


