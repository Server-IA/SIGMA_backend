from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import EmployeeCharge, EmployeeDepartment, Statues
from parameterization.serializers.employee_charges_serializers.employee_charges_create_serializer import EmployeeChargeCreateSerializer
from parameterization.serializers.employee_charges_serializers.employee_charges_list_serializer import EmployeeChargeListSerializer
from users.permissions import HasPermissionId

# Auditoría
from audit_sdk import AuditClient
from machinery.utils.audit_helpers import get_actor_info
from parameterization.utils.audit_helpers import employee_charge_snapshot
import logging

logger = logging.getLogger(__name__)

class EmployeeChargeViewSet(viewsets.ViewSet):
    # permission_classes = [HasPermissionId]  # Temporalmente deshabilitado para usar check_permission

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

    def create(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 66  # employee_charges.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear cargos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EmployeeChargeCreateSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()

            # Auditoría
            try:
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).create(
                    object_id=str(getattr(instance, "id_employee_charge", None) or ""),
                    after=employee_charge_snapshot(instance),
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",
                    submodule="employee_charges",
                )
            except Exception as e:
                logger.error(f"Error al registrar auditoría para creación de cargo: {str(e)}")

            return Response({"message": "Cargo creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 67  # employee_charges.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar cargos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            charge = EmployeeCharge.objects.get(pk=pk)
        except EmployeeCharge.DoesNotExist:
            return Response({"error": "Cargo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeChargeCreateSerializer(charge, data=request.data, partial=True)
        if serializer.is_valid():

            before = employee_charge_snapshot(charge)

            instance = serializer.save()

            # Auditoría
            try:
                after = employee_charge_snapshot(instance)
                actor_id, actor_name, actor_role_name = get_actor_info(getattr(request, "user", None))

                AuditClient(request).update(
                    object_id=str(getattr(instance, "id_employee_charge", None) or ""),
                    before=before,
                    after=after,
                    actor_id=str(actor_id) if actor_id is not None else None,
                    actor_name=actor_name,
                    actor_role=actor_role_name,
                    permission_id=permission_id,
                    module="parameterization",
                    submodule="employee_charges",
                )
            except Exception as e:
                logger.error(f"Error al registrar auditoría para actualización de cargo: {str(e)}")
                
            return Response({"message": "Cargo actualizado exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'list/(?P<department_id>\d+)')
    def listar_por_departamento(self, request, department_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 68  # employee_charges.list_by_department
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar cargos por departamento"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not EmployeeDepartment.objects.filter(pk=department_id).exists():
            return Response({"detail": "Departamento no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        charges = EmployeeCharge.objects.filter(id_employee_department_id=department_id)
        serializer = EmployeeChargeListSerializer(charges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path=r'list/active/(?P<department_id>\d+)')
    def listar_activos_por_departamento(self, request, department_id=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 69  # employee_charges.list_active_by_department
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar cargos activos por departamento"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not EmployeeDepartment.objects.filter(pk=department_id).exists():
            return Response({"detail": "Departamento no encontrado."},
                            status=status.HTTP_404_NOT_FOUND)

        charges = EmployeeCharge.objects.filter(
            id_employee_department_id=department_id,
            id_statues_id=1
        )
        serializer = EmployeeChargeListSerializer(charges, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 70  # employee_charges.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de cargos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            charge = EmployeeCharge.objects.get(pk=pk)
        except EmployeeCharge.DoesNotExist:
            return Response({"error": "Cargo no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if charge.id_statues_id == 1:
            try:
                charge.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Cargo desactivado exitosamente"
        else:
            try:
                charge.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"},
                                status=status.HTTP_400_BAD_REQUEST)
            message = "Cargo activado exitosamente"

        charge.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)
