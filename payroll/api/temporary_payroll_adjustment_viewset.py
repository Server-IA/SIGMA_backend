from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError

from payroll.serializers.temporary_payroll_adjustment.upload_massive_adjustments_serializer import (
    UploadMassiveAdjustmentsSerializer,
    UploadMassiveAdjustmentsResponseSerializer,
)
from payroll.services.massive_adjustment_service import MassiveAdjustmentService
import logging

logger = logging.getLogger(__name__)

class TemporaryPayrollAdjustmentViewSet(viewsets.ModelViewSet):
    """ViewSet para ajustes temporales de nómina"""
    
    def check_permission(self, request, required_permission_id: int):
        """
        Verifica si el usuario tiene el permiso (por ID).
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

    
    @action(detail=False, methods=["post"], url_path="upload")
    def upload_massive_adjustments(self, request):
        """
        Carga masiva de ajustes desde archivo Excel.

        Request (multipart/form-data):
        - file: Archivo Excel con ajustes
        - fecha_desde: Fecha inicio del periodo (YYYY-MM-DD)
        - fecha_hasta: Fecha fin del periodo (YYYY-MM-DD)
        - empleados_ids: Lista de IDs de empleados seleccionados

        Validaciones:
        - Archivo debe ser Excel (.xlsx o .xls)
        - Estructura con columnas requeridas
        - Empleado debe existir y estar en la lista seleccionada
        - Novedad debe estar parametrizada
        - Fechas dentro del rango
        - Porcentajes no mayores al 100%

        Respuesta incluye:
        - Resultados fila por fila (Aceptado/Rechazado)
        - IDs de ajustes temporales creados

        Requiere permiso: 188 (payroll.massive_payroll)
        """
        # Verificar autenticación
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verificar permiso
        required_permission = 188
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para la gestión de nómina masiva."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        try:
            # 1. Validar request
            serializer = UploadMassiveAdjustmentsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 2. Procesar archivo
            service = MassiveAdjustmentService(
                file=serializer.validated_data['file'],
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                employees_ids=serializer.validated_data['employees'],
                user=request.user
            )

            
            results = service.process()
            
            # 3. Serializar respuesta
            response_serializer = UploadMassiveAdjustmentsResponseSerializer(results)
            
            # 4. Determinar mensaje según resultados
            if results['rejected_rows'] == 0:
                message = "Ajustes masivos cargados exitosamente y aplicados a la nómina masiva."
                success = True
            elif results['accepted_rows'] == 0:
                message = "Todas las filas fueron rechazadas. Revise los errores."
                success = False
            else:
                message = f"Carga parcial: {results['accepted_rows']} aceptadas, {results['rejected_rows']} rechazadas."
                success = True
            
            return Response(
                {
                    "success": success,
                    "message": message,
                    "data": response_serializer.data,
                },
                status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST,
            )
        
        except DRFValidationError as exc:
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": exc.detail
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        except Exception as exc:
            logger.exception("Error en carga masiva de ajustes")
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )