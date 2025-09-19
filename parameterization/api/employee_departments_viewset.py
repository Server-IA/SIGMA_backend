from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import EmployeeDepartment, Statues
from parameterization.serializers.employee_departments_serializers.employee_departments_create_serializer import EmployeeDepartmentCreateSerializer
from parameterization.serializers.employee_departments_serializers.employee_departments_list_serializer import EmployeeDepartmentListSerializer
from django.shortcuts import get_object_or_404
from users.permissions import HasPermissionId

class EmployeeDepartmentViewSet(viewsets.ViewSet):
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
        
        permission_id = 106  # employee_departments.create
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para crear departamentos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EmployeeDepartmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Departamento creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 107  # employee_departments.update
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para actualizar departamentos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            department = EmployeeDepartment.objects.get(pk=pk)
        except EmployeeDepartment.DoesNotExist:
            return Response({"error": "Departamento no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeDepartmentCreateSerializer(department, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Departamento actualizado exitosamente"},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='list')
    def listar_departamentos(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 108  # employee_departments.list
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar departamentos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        departments = EmployeeDepartment.objects.all()
        serializer = EmployeeDepartmentListSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='list/active')
    def listar_activos(self, request):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 109  # employee_departments.list_active
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para listar departamentos activos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        departments = EmployeeDepartment.objects.filter(id_statues_id=1)
        if not departments.exists():
            return Response({
                "message": "No existen departamentos activos registrados",
                "data": []
            }, status=status.HTTP_200_OK)
        serializer = EmployeeDepartmentListSerializer(departments, many=True)
        return Response({
            "message": "Departamentos activos obtenidos exitosamente",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        # Verificar que el usuario esté autenticado
        if not getattr(request, 'user', None) or not getattr(request.user, 'is_authenticated', False):
            return Response(
                {"message": "Usuario no autenticado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        permission_id = 110  # employee_departments.toggle_status
        
        # Verificar permiso usando la función check_permission
        if not self.check_permission(request, permission_id):
            return Response(
                {"message": "No tiene permisos para alternar estado de departamentos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        department = get_object_or_404(EmployeeDepartment, pk=pk)

        if department.id_statues_id == 1:
            try:
                department.id_statues = Statues.objects.get(pk=2)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=2 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            message = "Departamento desactivado exitosamente"
        else:
            try:
                department.id_statues = Statues.objects.get(pk=1)
            except Statues.DoesNotExist:
                return Response({"error": "El estado con id=1 no existe"}, status=status.HTTP_400_BAD_REQUEST)
            message = "Departamento activado exitosamente"

        department.save(update_fields=['id_statues'])
        return Response({"message": message}, status=status.HTTP_200_OK)