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

from parameterization.models import Statues
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
from payroll.serializers.employee_contracts_serializers.employee_list_serializer import EmployeeListSerializer

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

    @action(detail=False, methods=['get'], url_path='list')
    def list_employees(self, request):
        """
        Lista empleados con filtros, ordenamiento y paginación.
        
        Query params:
        - search: Búsqueda por nombre o documento
        - search_type: "documento" o "nombre" (opcional, por defecto "nombre")
        - status: ID de estado (1=Activo, 2=Inactivo) (opcional)
        - ordering: Ordenamiento por columnas (document, name, status) con prefijo - para descendente
        - page: Número de página (por defecto 1)
        - page_size: Tamaño de página (10, 25, 50, 100, por defecto 25)
        
        Requiere permiso: 183
        """
        # Verificar autenticación
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verificar permiso
        required_permission = 183
        if not self.check_permission(request, required_permission):
            return Response(
                {"message": "No tiene permisos para acceder al listado de empleados."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Obtener parámetros de consulta
            search = request.query_params.get("search", "").strip()
            search_type = request.query_params.get("search_type", "nombre").strip().lower()
            status_filter = request.query_params.get("status")
            ordering = request.query_params.get("ordering", "").strip()
            page = request.query_params.get("page", "1")
            page_size = request.query_params.get("page_size", "25")

            # Validar search_type
            if search_type and search_type not in ["documento", "nombre"]:
                return Response(
                    {"message": "search_type debe ser 'documento' o 'nombre'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar status
            if status_filter:
                try:
                    status_filter = int(status_filter)
                    if status_filter not in [1, 2]:
                        return Response(
                            {"message": "status debe ser 1 (Activo) o 2 (Inactivo)."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                except ValueError:
                    return Response(
                        {"message": "status debe ser un número entero."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Validar page_size
            allowed_page_sizes = [10, 25, 50, 100]
            try:
                page_size = int(page_size)
                if page_size not in allowed_page_sizes:
                    return Response(
                        {"message": f"page_size debe ser uno de: {', '.join(map(str, allowed_page_sizes))}."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"message": "page_size debe ser un número entero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar page
            try:
                page = int(page)
                if page < 1:
                    return Response(
                        {"message": "page debe ser un número entero positivo."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                return Response(
                    {"message": "page debe ser un número entero positivo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Construir queryset base con optimizaciones
            queryset = Employee.objects.select_related(
                'id_employee_charge',
                'employee_status',
                'id_user'
            ).all()

            # Aplicar filtro de estado si se proporciona
            if status_filter:
                queryset = queryset.filter(employee_status_id=status_filter)

            # Obtener todos los empleados
            employees_list = list(queryset)

            # Obtener usuarios en batch una sola vez si es necesario (para búsqueda u ordenamiento)
            users_data = {}
            needs_user_data = bool(search) or ordering in ['document', '-document', 'name', '-name'] or not ordering
            if needs_user_data:
                user_ids = [emp.id_user_id for emp in employees_list if emp.id_user_id]
                if user_ids:
                    from service_requests.utils.external_user_helper import get_users_info_batch, get_user_display_name
                    users_data = get_users_info_batch(user_ids, request)

            # Aplicar filtro de búsqueda si existe
            if search:
                matching_employee_ids = set()
                search_lower = search.lower()
                
                for emp in employees_list:
                    if not emp.id_user_id or emp.id_user_id not in users_data:
                        continue
                    
                    user_data = users_data[emp.id_user_id]
                    
                    if search_type == "documento":
                        # Buscar por documento
                        doc_number = str(user_data.get('document_number', '')).strip()
                        if search_lower in doc_number.lower():
                            matching_employee_ids.add(emp.id_employee)
                    else:
                        # Buscar por nombre (por defecto)
                        name_parts = [
                            user_data.get('name', '').strip(),
                            user_data.get('first_last_name', '').strip(),
                            user_data.get('second_last_name', '').strip()
                        ]
                        full_name = ' '.join([p for p in name_parts if p]).lower()
                        if search_lower in full_name:
                            matching_employee_ids.add(emp.id_employee)
                
                # Filtrar empleados que coinciden
                employees_list = [emp for emp in employees_list if emp.id_employee in matching_employee_ids]

            # Ordenamiento
            if ordering:
                # Validar ordering
                allowed_orderings = ['document', '-document', 'name', '-name', 'status', '-status']
                if ordering not in allowed_orderings:
                    ordering = None

            if not ordering:
                # Ordenamiento por defecto: activos primero, luego inactivos, luego alfabético
                active_employees = [e for e in employees_list if e.employee_status_id == 1]
                inactive_employees = [e for e in employees_list if e.employee_status_id == 2]
                
                # Ordenar alfabéticamente por nombre
                if users_data:
                    from service_requests.utils.external_user_helper import get_user_display_name
                    
                    def get_sort_key(emp):
                        if not emp.id_user_id or emp.id_user_id not in users_data:
                            return ""
                        return get_user_display_name(users_data[emp.id_user_id]).lower()
                    
                    active_employees.sort(key=get_sort_key)
                    inactive_employees.sort(key=get_sort_key)
                
                employees_list = active_employees + inactive_employees
            else:
                # Ordenamiento por columna específica
                if ordering in ['document', '-document']:
                    # Ordenar por documento
                    def get_doc_sort_key(emp):
                        if not emp.id_user_id or emp.id_user_id not in users_data:
                            return ""
                        doc = str(users_data[emp.id_user_id].get('document_number', '')).lower()
                        return doc
                    
                    employees_list.sort(key=get_doc_sort_key, reverse=(ordering == '-document'))
                elif ordering in ['name', '-name']:
                    # Ordenar por nombre
                    from service_requests.utils.external_user_helper import get_user_display_name
                    
                    def get_name_sort_key(emp):
                        if not emp.id_user_id or emp.id_user_id not in users_data:
                            return ""
                        return get_user_display_name(users_data[emp.id_user_id]).lower()
                    
                    employees_list.sort(key=get_name_sort_key, reverse=(ordering == '-name'))
                elif ordering in ['status', '-status']:
                    # Ordenar por estado
                    employees_list.sort(key=lambda e: e.employee_status_id, reverse=(ordering == '-status'))

            # Paginación
            total = len(employees_list)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_employees = employees_list[start_index:end_index]

            # Serializar resultados (pasar usuarios_data para evitar llamadas adicionales)
            serializer = EmployeeListSerializer(
                paginated_employees,
                many=True,
                context={'request': request, 'users_data': users_data}
            )

            # Construir respuesta
            response_data = {
                "success": True,
                "data": serializer.data,
                "pagination": {
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                }
            }

            # Agregar mensaje si no hay resultados
            if total == 0:
                response_data["message"] = "No se encontraron empleados con los criterios seleccionados."

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error al listar empleados")
            return Response(
                {
                    "success": False,
                    "message": "Ocurrió un error al procesar la solicitud.",
                    "error": str(exc),
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
