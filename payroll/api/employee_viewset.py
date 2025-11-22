import logging
import os

import requests
from audit_sdk import AuditClient
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from parameterization.models import Statues, Types
from payroll.models import Employee, EmployeeContract, EmployeeNews
from payroll.utils.audit_helpers import get_actor_info, employee_with_contract_snapshot
from users.models import User
from payroll.serializers.employee_contracts_serializers.employee_contract_detail_serializer import (
    EmployeeContractDetailSerializer,
)
from payroll.serializers.employee_contracts_serializers.employee_with_contract_serializer import (
    EmployeeWithContractCreateSerializer,
)
from payroll.serializers.employee_contracts_serializers.employee_update_serializer import EmployeeUpdateSerializer
from payroll.serializers.employee_contracts_serializers.employee_contract_history_serializer import (
    EmployeeContractHistorySerializer,
)
from payroll.serializers.employee_contracts_serializers.employee_contract_detail_history_serializer import (
    EmployeeContractDetailHistorySerializer,
)
from payroll.serializers.employee_contracts_serializers.employee_contract_terminate_serializer import (
    EmployeeContractTerminateSerializer,
)

logger = logging.getLogger(__name__)


class EmployeeViewSet(viewsets.ViewSet):
    """Gestiona la creación de empleados junto con su contrato asociado."""

    def check_permission(self, request, required_permission_id: int) -> bool:
        payload = getattr(request, "auth", None) or {}
        user_roles = payload.get("rol") or payload.get("roles") or []

        permission_ids = []
        for rol in user_roles:
            perms = (rol or {}).get("permisos") or (rol or {}).get("permissions") or []
            for perm in perms:
                if isinstance(perm, dict) and "id" in perm:
                    permission_ids.append(perm.get("id"))

        return required_permission_id in permission_ids

    @action(detail=True, methods=["get"], url_path="employee_contract_detail")
    def employee_contract_detail(self, request, pk=None):
        """Devuelve el detalle completo de un contrato de empleado."""

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 181
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar contratos de empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            contract = (
                EmployeeContract.objects.select_related(
                    "id_employee_charge",
                    "id_employee_department",
                    "id_employee",
                    "contract_type",
                    "workday_type",
                    "work_mode_type",
                    "currency_type",
                    "contract_status",
                    "id_responsible_user",
                )
                .prefetch_related(
                    "contract_payments",
                    "contract_payments__id_day_of_week",
                    "employee_contract_deductions",
                    "employee_contract_deductions__deduction_type",
                    "employee_contract_increases",
                    "employee_contract_increases__increase_type",
                )
                .get(contract_code=pk)
            )
        except EmployeeContract.DoesNotExist:
            return Response(
                {"message": "No se encontró el contrato de empleado especificado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error("Error al obtener detalle de contrato de empleado", exc_info=True)
            return Response(
                {
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = EmployeeContractDetailSerializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="toggle-status")
    def toggle_status(self, request, pk=None):
        """Activa o desactiva un empleado y sincroniza la información relacionada."""

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        permission_id = 10
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para activar/desactivar empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            employee = Employee.objects.select_related("employee_status", "id_user").get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {"message": "Empleado no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        responsible_user = self._get_responsible_user(request)
        if responsible_user is None:
            return Response(
                {"message": "No se pudo determinar el usuario responsable autenticado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not employee.id_user_id:
            return Response(
                {"message": "El empleado no tiene un usuario asociado para sincronizar su estado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        observation = (request.data or {}).get("observation")
        if observation is not None:
            observation = str(observation).strip()

        is_active = employee.employee_status_id == 1
        if is_active:
            target_status_id = 2
            news_type = "DESACTIVACION_EMPLEADO"
            external_status = 3
            success_message = "Empleado desactivado exitosamente."
            requires_contract_update = True
        else:
            target_status_id = 1
            news_type = "ACTIVACION_EMPLEADO"
            external_status = 4
            success_message = "Empleado activado exitosamente."
            requires_contract_update = False

        if is_active and not observation:
            return Response(
                {"message": "El campo observation es obligatorio al desactivar al empleado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        observation_value = observation if observation else None

        try:
            target_status = Statues.objects.get(pk=target_status_id)
        except Statues.DoesNotExist:
            return Response(
                {"message": f"No se encontró el estado {target_status_id} para empleados."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        latest_contract = None
        contract_before_status = None
        contract_after_status = None
        contract_status_to_assign = None

        if requires_contract_update:
            try:
                contract_status_to_assign = Statues.objects.get(pk=29)
            except Statues.DoesNotExist:
                return Response(
                    {"message": "No se encontró el estado 29 para el contrato del empleado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            before_employee_status = employee.employee_status_id

            employee.employee_status = target_status
            employee.modification_date = timezone.now()
            employee.save(update_fields=["employee_status", "modification_date"])

            if requires_contract_update and contract_status_to_assign:
                latest_contract = (
                    EmployeeContract.objects.select_for_update()
                    .filter(id_employee=employee)
                    .order_by("-creation_date")
                    .first()
                )
                if not latest_contract:
                    transaction.set_rollback(True)
                    return Response(
                        {"message": "El empleado no tiene contratos para actualizar."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                contract_before_status = latest_contract.contract_status_id
                latest_contract.contract_status = contract_status_to_assign
                latest_contract.save(update_fields=["contract_status"])
                contract_after_status = contract_status_to_assign.id_statues

            EmployeeNews.objects.create(
                id_employee=employee,
                observation=observation_value,
                news_type=news_type,
                id_responsible_user=responsible_user,
            )

        try:
            self._change_external_user_status(request, employee.id_user_id, external_status)
        except Exception as exc:
            logger.error("Error al sincronizar el estado del usuario externo: %s", str(exc), exc_info=True)
            return Response(
                {
                    "message": "No se pudo actualizar el estado en el servicio de autenticación.",
                    "error": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            actor_id, actor_name, actor_role_name = get_actor_info(request.user)
            AuditClient(request).update(
                object_id=str(employee.id_employee),
                before={"employee_status": before_employee_status},
                after={"employee_status": target_status_id},
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role_name,
                permission_id=permission_id,
                module="payroll",
                submodule="employee_contract",
            )

            if requires_contract_update and latest_contract:
                AuditClient(request).update(
                    object_id=str(latest_contract.contract_code),
                    before={"contract_status": contract_before_status},
                    after={"contract_status": contract_after_status},
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="payroll",
                    submodule="employee_contract",
                )
        except Exception as audit_exc:
            logger.warning("El servicio de auditoría falló en toggle_status: %s", str(audit_exc))

        return Response({"message": success_message}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="latest_employee_contract")
    def latest_employee_contract(self, request, pk=None):
        """Devuelve el contrato más reciente asociado a un empleado."""

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 181
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar contratos de empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            contract = (
                EmployeeContract.objects.filter(id_employee_id=pk)
                .select_related(
                    "id_employee_charge",
                    "id_employee_department",
                    "id_employee",
                    "contract_type",
                    "workday_type",
                    "work_mode_type",
                    "currency_type",
                    "contract_status",
                    "id_responsible_user",
                )
                .prefetch_related(
                    "contract_payments",
                    "contract_payments__id_day_of_week",
                    "employee_contract_deductions",
                    "employee_contract_deductions__deduction_type",
                    "employee_contract_increases",
                    "employee_contract_increases__increase_type",
                )
                .order_by("-creation_date")
                .first()
            )
        except Exception as exc:
            logger.error("Error al obtener el contrato más reciente del empleado", exc_info=True)
            return Response(
                {
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not contract:
            return Response(
                {"message": "El empleado no tiene contratos registrados."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = EmployeeContractDetailSerializer(contract)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        required_permission = 3

        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para crear empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = EmployeeWithContractCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = serializer.save()
        except DRFValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Error al crear empleado y contrato")
            return Response(
                {
                    "message": "Ocurrió un error al crear el empleado con su contrato.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        employee_id = result.get("employee_id")
        contract_code = result.get("contract_code")

        employee_instance = None
        contract_instance = None
        if employee_id:
            employee_instance = Employee.objects.filter(pk=employee_id).first()
        if contract_code:
            contract_instance = EmployeeContract.objects.filter(contract_code=contract_code).first()

        try:
            actor_id, actor_name, actor_role_name = get_actor_info(request.user)
            AuditClient(request).create(
                object_id=str(employee_id or ""),
                after=employee_with_contract_snapshot(employee_instance, contract_instance),
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role_name,
                permission_id=required_permission,
                module="payroll",
                submodule="employee_contract",
            )
        except Exception as audit_exc:
            logger.warning("El servicio de auditoría falló en create_employee: %s", str(audit_exc))

        return Response(
            {
                "message": "Empleado y contrato creados exitosamente.",
                "data": result,
            },
            status=status.HTTP_201_CREATED,
        )

    def _get_responsible_user(self, request):
        user_id = getattr(request.user, "id", None)
        if not user_id:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    @action(detail=True, methods=['patch'], url_path='update-employee')
    def update_employee(self, request, pk=None):
        """
        Actualiza la información básica de un empleado.
        Permite actualizar el email (validando unicidad) y el cargo.
        Crea un registro en EmployeeNews para auditoría.
        Requiere autenticación y permiso con ID 4.
        """
        # Check authentication
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check permission
        if not self.check_permission(request, 4):
            return Response(
                {"message": "No tiene permisos para actualizar empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {"message": "Empleado no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get responsible user
        responsible_user = self._get_responsible_user(request)
        if not responsible_user:
            return Response(
                {"message": "No se pudo determinar el usuario responsable."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create serializer with context for audit
        serializer = EmployeeUpdateSerializer(
            instance=employee,
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Create before snapshot
                before = employee_with_contract_snapshot(employee=employee)
                
                # Save employee updates
                employee = serializer.save()
                
                # Create after snapshot with updated data
                after = employee_with_contract_snapshot(employee=employee)

                # Create EmployeeNews entry
                observation = serializer.validated_data.get('observation')
                if observation:
                    EmployeeNews.objects.create(
                        id_employee=employee,
                        observation=observation,
                        news_type='ACTUALIZACION_EMPLEADO',
                        id_responsible_user=responsible_user
                    )

                # Auditoría
                try:
                    actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                    AuditClient(request).update(
                        object_id=str(getattr(employee, "id_employee", None) or ""),
                        before=before,
                        after=after,
                        actor_id=str(actor_id) if actor_id is not None else None,
                        actor_name=actor_name,
                        actor_role=actor_role_name,
                        permission_id=4,
                        module="payroll",
                        submodule="employee",
                    )
                except Exception as e:
                    logger.error(f"Error al registrar auditoría para actualización de empleado: {str(e)}")

            return Response(
                {"message": "Empleado actualizado exitosamente."},
                status=status.HTTP_200_OK
            )

        except Exception as exc:
            logger.exception("Error al actualizar empleado")
            return Response(
                {
                    "message": "Ocurrió un error al actualizar el empleado.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="contract-history")
    def contract_history(self, request, pk=None):
        """
        Devuelve el historial de contratos de un empleado.
        Solo muestra la última versión de cada contract_code.
        
        Requiere permiso: 184 (employee.contract_history)
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 184
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar el historial de contratos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Verificar que el empleado existe
            employee = Employee.objects.get(pk=pk)
        except Employee.DoesNotExist:
            return Response(
                {"message": "Empleado no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            # Obtener todos los contratos del empleado ordenados por contract_code descendente
            all_contracts = (
                EmployeeContract.objects.filter(id_employee_id=pk)
                .select_related("contract_status", "id_responsible_user")
                .order_by("-contract_code")
            )

            # Agrupar por base del contract_code y obtener solo la última versión
            # Formato: CON-YYYY-NNNN-VV
            # Base: CON-YYYY-NNNN (todo excepto los últimos 3 caracteres: -VV)
            contracts_by_base = {}
            
            for contract in all_contracts:
                contract_code = contract.contract_code
                
                # Extraer la base del código (todo excepto los últimos 3 caracteres: -VV)
                # Ejemplo: CON-2025-0001-03 -> base: CON-2025-0001
                if len(contract_code) >= 3:
                    # Buscar el último guion antes de la versión
                    last_dash_index = contract_code.rfind('-')
                    if last_dash_index > 0:
                        base_code = contract_code[:last_dash_index]
                    else:
                        # Si no hay guion, usar el código completo
                        base_code = contract_code
                else:
                    base_code = contract_code
                
                # Si no tenemos esta base o esta versión es más reciente, guardarla
                if base_code not in contracts_by_base:
                    contracts_by_base[base_code] = contract
                else:
                    # Comparar versiones (los últimos 2 dígitos después del último guion)
                    current_version = self._extract_version(contract_code)
                    existing_version = self._extract_version(contracts_by_base[base_code].contract_code)
                    
                    if current_version > existing_version:
                        contracts_by_base[base_code] = contract

            # Convertir el diccionario a lista y ordenar por creation_date descendente
            latest_contracts = list(contracts_by_base.values())
            latest_contracts.sort(key=lambda x: x.creation_date, reverse=True)

            # Serializar los contratos
            serializer = EmployeeContractHistorySerializer(
                latest_contracts, many=True, context={"request": request}
            )

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.error("Error al obtener historial de contratos: %s", str(exc), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _extract_version(self, contract_code: str) -> int:
        """
        Extrae el número de versión del contract_code.
        Formato esperado: CON-YYYY-NNNN-VV
        Retorna el número de versión como entero, o 0 si no se puede extraer.
        """
        try:
            last_dash_index = contract_code.rfind('-')
            if last_dash_index > 0 and last_dash_index < len(contract_code) - 1:
                version_str = contract_code[last_dash_index + 1:]
                return int(version_str)
        except (ValueError, IndexError):
            pass
        return 0

    def _extract_base_code(self, contract_code: str) -> str:
        """
        Extrae la base del contract_code (primeros 3 segmentos).
        Formato esperado: CON-YYYY-NNNN-VV
        Retorna: CON-YYYY-NNNN
        """
        try:
            # Dividir por guiones
            parts = contract_code.split('-')
            if len(parts) >= 3:
                # Tomar los primeros 3 segmentos
                return '-'.join(parts[:3])
            return contract_code
        except Exception:
            return contract_code

    @action(detail=False, methods=["get"], url_path="contract-detail-history")
    def contract_detail_history(self, request):
        """
        Devuelve el historial completo de un contrato específico.
        Muestra todas las versiones del contrato con la misma base (primeros 3 segmentos).
        
        Parámetros de consulta:
        - contract_code: Código del contrato (ej: CON-2025-0001-05)
        
        Requiere permiso: 184 (employee.contract_detail_history)
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 184
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para consultar el historial del contrato."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Obtener el contract_code de los parámetros de consulta
        contract_code = request.query_params.get('contract_code', '').strip()
        
        if not contract_code:
            return Response(
                {
                    "success": False,
                    "message": "El parámetro 'contract_code' es requerido."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verificar que el contrato existe
            try:
                requested_contract = EmployeeContract.objects.get(contract_code=contract_code)
            except EmployeeContract.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Contrato no encontrado."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Extraer la base del código (primeros 3 segmentos)
            base_code = self._extract_base_code(contract_code)
            
            # Buscar todos los contratos con la misma base
            all_contracts = (
                EmployeeContract.objects.filter(contract_code__startswith=f"{base_code}-")
                .select_related("contract_status", "id_responsible_user")
                .order_by("contract_code")  # Ordenar por código para mantener orden de versión
            )

            if not all_contracts.exists():
                return Response(
                    {
                        "success": False,
                        "message": "No se encontraron versiones del contrato."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Convertir a lista y ordenar por versión
            contracts_list = list(all_contracts)
            contracts_list.sort(key=lambda x: self._extract_version(x.contract_code))

            # Identificar el último contrato (mayor versión)
            latest_contract = contracts_list[-1] if contracts_list else None

            # Serializar los contratos pasando el último contrato para la lógica especial
            serializer = EmployeeContractDetailHistorySerializer(
                contracts_list,
                many=True,
                context={"request": request, "latest_contract": latest_contract}
            )

            return Response(
                {
                    "success": True,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.error("Error al obtener historial del contrato: %s", str(exc), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @transaction.atomic
    @action(detail=True, methods=["post"], url_path="terminate-contract")
    def terminate_contract(self, request, pk=None):
        """
        Finaliza un contrato de empleado.
        
        Cambia el estado del contrato a 29 (Finalizado), actualiza el motivo de finalización,
        crea una novedad opcional y cambia el estado del empleado a 2 (Inactivo).
        
        Requiere permiso: 185 (employee.terminate_contract)
        
        URL: POST /employees/{contract_code}/terminate-contract/
        
        Campos requeridos en el body:
        - contract_termination_reason: ID del motivo de finalización (debe pertenecer a categoría 20)
        
        Campos opcionales en el body:
        - observation: Observación para la novedad del empleado
        """
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"success": False, "message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        required_permission = 185
        if not self.check_permission(request, required_permission):
            return Response(
                {"success": False, "message": "No tiene permisos para finalizar contratos."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # El contract_code viene en la URL como pk
        contract_code = pk

        if not contract_code:
            return Response(
                {
                    "success": False,
                    "message": "El código del contrato es requerido en la URL."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validar datos de entrada
        serializer = EmployeeContractTerminateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "message": "Error de validación",
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Obtener el contrato
            try:
                contract = EmployeeContract.objects.select_related(
                    'id_employee',
                    'contract_status',
                    'contract_termination_reason'
                ).get(contract_code=contract_code)
            except EmployeeContract.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "Contrato no encontrado."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Validar que el contrato no esté ya finalizado
            if contract.contract_status_id == 29:
                return Response(
                    {
                        "success": False,
                        "message": "El contrato ya está finalizado y no puede ser finalizado nuevamente."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Obtener el empleado
            employee = contract.id_employee
            if not employee:
                return Response(
                    {
                        "success": False,
                        "message": "El contrato no tiene un empleado asociado."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Obtener el estado finalizado (29)
            try:
                finished_status = Statues.objects.get(pk=29)
            except Statues.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "No se encontró el estado 29 (Finalizado) en el sistema."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Obtener el estado inactivo del empleado (2)
            try:
                inactive_employee_status = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "No se encontró el estado 2 (Inactivo) para empleados en el sistema."
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Obtener el motivo de finalización
            termination_reason_id = serializer.validated_data['contract_termination_reason']
            try:
                termination_reason = Types.objects.select_related('id_types_categories').get(pk=termination_reason_id)
            except Types.DoesNotExist:
                return Response(
                    {
                        "success": False,
                        "message": "El motivo de finalización no existe."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Obtener el usuario responsable
            responsible_user = self._get_responsible_user(request)
            if not responsible_user:
                return Response(
                    {
                        "success": False,
                        "message": "No se pudo determinar el usuario responsable."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Realizar todas las actualizaciones en una transacción
            with transaction.atomic():
                # 1. Actualizar el contrato: estado a 29 y motivo de finalización
                contract.contract_status = finished_status
                contract.contract_termination_reason = termination_reason
                contract.save(update_fields=['contract_status', 'contract_termination_reason'])

                # 2. Actualizar el estado del empleado a 2 (Inactivo)
                employee.employee_status = inactive_employee_status
                employee.modification_date = timezone.now()
                employee.save(update_fields=['employee_status', 'modification_date'])

                # 3. Crear novedad (siempre se crea, con o sin observación adicional)
                observation_from_json = serializer.validated_data.get('observation')
                
                # Construir la observación completa: motivo + observación del JSON (separados por coma)
                termination_reason_name = termination_reason.name if termination_reason else "Sin motivo especificado"
                observation_parts = [f"Motivo: {termination_reason_name}"]
                
                if observation_from_json:
                    observation_parts.append(observation_from_json)
                
                final_observation = ", ".join(observation_parts)
                
                EmployeeNews.objects.create(
                    id_employee=employee,
                    observation=final_observation,
                    news_type='FINALIZACION_CONTRATO',
                    id_responsible_user=responsible_user
                )

            # Registrar auditoría
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(request.user)
                AuditClient(request).update(
                    object_id=str(contract.contract_code),
                    before={"contract_status": contract.contract_status_id},
                    after={"contract_status": 29, "contract_termination_reason": termination_reason_id},
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=required_permission,
                    module="payroll",
                    submodule="employee_contract",
                )

                # Auditoría para el cambio de estado del empleado
                AuditClient(request).update(
                    object_id=str(employee.id_employee),
                    before={"employee_status": employee.employee_status_id},
                    after={"employee_status": 2},
                    actor_id=actor_id,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=required_permission,
                    module="payroll",
                    submodule="employee",
                )
            except Exception as audit_exc:
                logger.warning("El servicio de auditoría falló en terminate_contract: %s", str(audit_exc))

            return Response(
                {
                    "success": True,
                    "message": "Contrato finalizado exitosamente."
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:
            logger.error("Error al finalizar contrato: %s", str(exc), exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al finalizar el contrato.",
                    "error": str(exc)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _change_external_user_status(self, request, user_id: int, new_status: int):
        base_url = (os.getenv("AUTH_SERVICE_URL") or "").rstrip("/")
        if not base_url:
            raise ValueError("AUTH_SERVICE_URL no está configurado")

        url = f"{base_url}/users/users/change-user-status/"
        headers = {}
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header:
            headers["Authorization"] = auth_header

        response = requests.post(
            url,
            json={"user_id": user_id, "new_status": new_status},
            headers=headers,
            timeout=15,
        )
        if response.status_code not in (200, 201, 204):
            raise ValueError(
                f"Servicio externo respondió {response.status_code}: {response.text}"
            )
