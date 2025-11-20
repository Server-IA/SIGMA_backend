from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
import logging
from audit_sdk import AuditClient
from datetime import datetime

from payroll.serializers.established_contracts_serializers.established_contract_serializer import (
    EstablishedContractCreateSerializer
)
from payroll.serializers.established_contracts_serializers.established_contract_update_serializer import (
    EstablishedContractUpdateSerializer
)
from payroll.serializers.established_contracts_serializers.established_contract_detail_serializer import (
    EstablishedContractDetailSerializer
)
from payroll.serializers.established_contracts_serializers.established_contract_list_serializer import (
    EstablishedContractListSerializer
)
from payroll.models.established_contract import EstablishedContract
from payroll.utils.audit_helpers import get_actor_info, contract_snapshot
from payroll.utils.contract_document_generator import ContractDocumentGenerator
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

logger = logging.getLogger(__name__)

class EstablishedContractViewSet(viewsets.ViewSet):
    """
    ViewSet para manejar las operaciones de contratos establecidos.
    """
    
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

    @action(detail=False, methods=['get'], url_path='list')
    def list_established_contracts(self, request):
        """
        Lista todos los contratos establecidos.
        
        Requiere permiso: 177 (established_contract.list)
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso
        required_permission = 177
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para listar contratos"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener todos los contratos con sus relaciones optimizadas
            queryset = EstablishedContract.objects.select_related(
                'contract_type',
                'established_contract_status'
            ).all()
            
            # Serializar los datos
            serializer = EstablishedContractListSerializer(queryset, many=True, context={'request': request})
            
            return Response({
                "success": True,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error al listar contratos: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud",
                    "error": str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='detail')
    def retrieve_contract_detail(self, request, pk=None):
        """
        Obtiene el detalle completo de un contrato establecido.
        
        Requiere permiso: 175 (established_contract.retrieve)
        
        Parámetros:
        - pk: contract_code del contrato a consultar
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso
        required_permission = 175
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar este contrato"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener el contrato con sus relaciones
            instance = EstablishedContract.objects.select_related(
                'contract_type',
                'workday_type',
                'work_mode_type',
                'currency_type',
                'established_contract_status'
            ).prefetch_related(
                'contract_payments',
                'contract_payments__id_day_of_week',
                'established_deductions',
                'established_increases'
            ).get(contract_code=pk)
            
            # Serializar los datos
            serializer = EstablishedContractDetailSerializer(instance)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except EstablishedContract.DoesNotExist:
            return Response(
                {"message": "No se encontró el contrato especificado"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al obtener el detalle del contrato: {str(e)}", exc_info=True)
            return Response(
                {"message": "Ocurrió un error al procesar la solicitud"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='create_established_contract')
    def create_established_contract(self, request):
        """
        Crea un nuevo contrato establecido.
        
        Requiere permiso: 174 (established_contract.create)
        
        Campos obligatorios:
        - id_employee_charge: ID del cargo del empleado
        - contract_type: ID del tipo de contrato (debe pertenecer a la categoría 15)
        - start_date: Fecha de inicio del contrato
        - payment_frequency_type: Frecuencia de pago (diario, semanal, quincenal, mensual)
        - salary_base: Salario base (decimal mayor a 0)
        
        Campos condicionales:
        - Si cumulative_vacation es True, start_cumulative_vacation es obligatorio
        - Los campos de deducciones e incrementos deben tener fechas dentro del rango del contrato
        """
        try:
            # Verificar que el usuario esté autenticado
            if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
                return Response(
                    {"message": "Usuario no autenticado"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            permission_id = 174  # established_contract.create

            # Verificar permiso
            if not self.check_permission(request, permission_id):
                return Response(
                    {"message": "No tiene permisos para crear un contrato establecido."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Obtener datos del usuario para auditoría
            actor_id, actor_name, actor_role_name = get_actor_info(request.user)

            # Validar y crear el contrato
            serializer = EstablishedContractCreateSerializer(
                data=request.data,
                context={'request': request}
            )

            if serializer.is_valid():
                with transaction.atomic():
                    # Crear el contrato
                    contract = serializer.save()
                    
                    # Auditoría
                    try:
                        AuditClient(request).create(
                            object_id=str(contract.contract_code),
                            after=contract_snapshot(contract),
                            actor_id=actor_id,
                            actor_name=actor_name,
                            actor_role=actor_role_name,
                            permission_id=permission_id,
                            module="payroll",
                            submodule="established_contract",
                        )
                    except Exception as e:
                        logger.warning(
                            "El servicio de auditoría ha fallado en create_established_contract: %s", e
                        )
                    
                    return Response(
                        {
                            "success": True,
                            "message": "Contrato creado exitosamente",
                            "contract_code": contract.contract_code
                        },
                        status=status.HTTP_201_CREATED
                    )
            
            return Response(
                {
                    "success": False,
                    "message": "Error al crear el contrato",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            logger.error("Error al crear contrato: %s", str(e), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Error interno del servidor al procesar la solicitud",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['put'], url_path='update_established_contract')
    def update_established_contract(self, request, pk=None):
        """
        Actualiza un contrato establecido existente.

        Requiere permiso: 176 (established_contract.update)
        """
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 176 

        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar este contrato."},
                status=status.HTTP_403_FORBIDDEN
            )

        instance = get_object_or_404(EstablishedContract, contract_code=pk)

        serializer = EstablishedContractUpdateSerializer(
            instance,
            data=request.data,
            partial=False,
            context={'request': request}
        )

        if serializer.is_valid():
            try:
                with transaction.atomic():
                    before_snapshot = contract_snapshot(instance)
                    updated_contract = serializer.save()
                    after_snapshot = contract_snapshot(updated_contract)

                    try:
                        actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                        AuditClient(request).update(
                            object_id=str(updated_contract.contract_code),
                            before=before_snapshot,
                            after=after_snapshot,
                            actor_id=actor_id,
                            actor_name=actor_name,
                            actor_role=actor_role_name,
                            permission_id=permission_id,
                            module="payroll",
                            submodule="established_contract",
                        )
                    except Exception as audit_exc:
                        logger.warning(
                            "El servicio de auditoría ha fallado en update_established_contract: %s",
                            audit_exc
                        )

                    return Response(
                        {
                            "success": True,
                            "message": "Contrato actualizado exitosamente",
                            "contract_code": updated_contract.contract_code
                        },
                        status=status.HTTP_200_OK
                    )
            except Exception as e:
                logger.error("Error al actualizar contrato: %s", str(e), exc_info=True)
                return Response(
                    {
                        "success": False,
                        "message": "Error al actualizar el contrato",
                        "error": str(e)
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {
                "success": False,
                "message": "Error de validación al actualizar el contrato",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        """
        Activa/Inactiva un contrato establecido (1 Activo, 2 Inactivo) mediante toggle.
        
        Requiere permiso: 179 (established_contract.toggle_status)
        """
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 179
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para activar/desactivar contratos."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            contract = EstablishedContract.objects.get(contract_code=pk)

            try:
                from parameterization.models import Statues
                before_status_id = getattr(contract, 'established_contract_status_id', None)
                if before_status_id == 1:
                    new_status = Statues.objects.get(pk=2)
                    new_status_id = 2
                    message = "Contrato inactivado exitosamente"
                else:
                    new_status = Statues.objects.get(pk=1)
                    new_status_id = 1
                    message = "Contrato activado exitosamente"

                contract.established_contract_status = new_status
                contract.save(update_fields=['established_contract_status'])

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                    AuditClient(request).update(
                        object_id=str(contract.contract_code),
                        before={"established_contract_status": before_status_id},
                        after={"established_contract_status": new_status_id},
                        actor_id=actor_id,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=permission_id,
                        module="payroll",
                        submodule="established_contract",
                    )
                except Exception as e:
                    logger.warning("El servicio de auditoría ha fallado en toggle_status_contract: %s", str(e))

                return Response({"success": True, "message": message}, status=status.HTTP_200_OK)

            except Statues.DoesNotExist:
                return Response(
                    {"success": False, "message": "Estado no válido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except EstablishedContract.DoesNotExist:
            return Response(
                {"success": False, "message": "Contrato no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al cambiar el estado del contrato: {str(e)}", exc_info=True)
            return Response(
                {"success": False, "message": "Error al cambiar el estado del contrato.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @transaction.atomic
    def destroy(self, request, pk=None):
        """
        Elimina un contrato establecido junto con sus relaciones:
        - EstablishedDeduction
        - EstablishedIncrease
        - ContractPaymentsEstablishedContract
        
        Requiere permiso: 178 (established_contract.delete)
        """
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        permission_id = 178  # established_contract.delete
        if not self.check_permission(request, permission_id):
            return Response(
                {"success": False, "message": "No tiene permisos para eliminar contratos."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            contract = EstablishedContract.objects.select_related(
                'established_contract_status'
            ).prefetch_related(
                'established_deductions',
                'established_increases',
                'contract_payments'
            ).get(contract_code=pk)
        except EstablishedContract.DoesNotExist:
            return Response(
                {"success": False, "message": "Contrato no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Capturar snapshot antes de eliminar para auditoría
        before = contract_snapshot(contract)

        try:
            # Eliminar relaciones primero (aunque tienen PROTECT, las eliminamos manualmente)
            # Eliminar deducciones
            contract.established_deductions.all().delete()
            
            # Eliminar incrementos
            contract.established_increases.all().delete()
            
            # Eliminar pagos del contrato
            contract.contract_payments.all().delete()
            
            # Eliminar el contrato
            contract_code = contract.contract_code
            contract.delete()

            # Auditoría
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                AuditClient(request).delete(
                    object_id=str(contract_code),
                    before=before,
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="payroll",
                    submodule="established_contract",
                )
            except Exception as e:
                logger.warning("El servicio de auditoría ha fallado en delete_contract: %s", str(e))

            return Response({
                "success": True,
                "code": 200,
                "message": "Contrato eliminado correctamente junto con sus relaciones.",
                "data": None
            }, status=status.HTTP_200_OK)

        except IntegrityError as e:
            logger.error(f"Error de integridad al eliminar contrato: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "code": 409,
                "message": "No se puede eliminar el contrato porque tiene referencias asociadas.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_409_CONFLICT)

        except Exception as e:
            logger.error(f"Error al eliminar el contrato: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "code": 500,
                "message": "Error al eliminar el contrato.",
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='download')
    def download_contract(self, request, pk=None):
        """
        Descarga un contrato establecido en formato PDF o DOCX.
        
        Requiere permiso: 180 (established_contract.download)
        
        Parámetros:
        - pk: contract_code del contrato a descargar
        - file_type: query param opcional ('pdf' o 'docx'), default: 'pdf'
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verificar permiso
        required_permission = 180
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos o el contrato seleccionado no se encuentra disponible para descarga."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Obtener formato desde query params (default: pdf)
            # Se usa 'file_type' en lugar de 'format' para evitar conflictos con DRF
            file_format = request.query_params.get('file_type', 'pdf').lower()
            if file_format not in ['pdf', 'docx']:
                return Response(
                    {"message": "Formato inválido. Formatos permitidos: pdf, docx"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener el contrato con sus relaciones optimizadas
            try:
                contract = EstablishedContract.objects.select_related(
                    'contract_type',
                    'workday_type',
                    'work_mode_type',
                    'currency_type',
                    'established_contract_status',
                    'id_employee_charge'
                ).prefetch_related(
                    'contract_payments',
                    'contract_payments__id_day_of_week',
                    'established_deductions',
                    'established_deductions__deduction_type',
                    'established_increases',
                    'established_increases__increase_type'
                ).get(contract_code=pk)
            except EstablishedContract.DoesNotExist:
                return Response(
                    {"message": "No tiene permisos o el contrato seleccionado no se encuentra disponible para descarga."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Obtener información del usuario que descarga
            downloader_user = None
            actor_id = None
            actor_name = None
            actor_role_name = None
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                downloader_user = actor_name
            except Exception:
                downloader_user = None

            # Generar documento
            if file_format == 'pdf':
                document_bytes = ContractDocumentGenerator.generate_pdf(
                    contract,
                    downloader_user=downloader_user,
                    logo_path=None
                )
                content_type = 'application/pdf'
                file_extension = 'pdf'
            else:  # docx
                document_bytes = ContractDocumentGenerator.generate_docx(
                    contract,
                    downloader_user=downloader_user,
                    logo_path=None
                )
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                file_extension = 'docx'

            # Generar nombre del archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"contrato_{contract.contract_code}_{timestamp}.{file_extension}"

            # Registrar descarga en historial (auditoría)
            try:
                download_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                # Usar contract_snapshot para el after y agregar metadata de descarga
                contract_data = contract_snapshot(contract)
                contract_data['download_info'] = {
                    'action': 'download',
                    'file_format': file_extension.upper(),
                    'downloaded_by': actor_name or 'Sistema',
                    'download_timestamp': download_timestamp,
                    'filename': filename
                }
                AuditClient(request).create(
                    object_id=str(contract.contract_code),
                    after=contract_data,
                    actor_id=actor_id or 'Sistema',
                    actor_name=actor_name or 'Sistema',
                    actor_role=actor_role_name or 'Usuario',
                    permission_id=required_permission,
                    module="payroll",
                    submodule="established_contract",
                )
                logger.info(f"Descarga de contrato {contract.contract_code} registrada en historial")
            except Exception as audit_exc:
                logger.warning(
                    "El servicio de auditoría ha fallado al registrar descarga del contrato %s: %s",
                    contract.contract_code,
                    str(audit_exc)
                )

            # Crear respuesta HTTP
            response = HttpResponse(document_bytes, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(document_bytes)

            return response

        except Exception as e:
            logger.error(f"Error al generar documento del contrato {pk}: {str(e)}", exc_info=True)
            return Response(
                {"message": "Error al generar el documento del contrato."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
