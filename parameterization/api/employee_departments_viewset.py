from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import EmployeeDepartment, Statues
from parameterization.serializers.employee_departments_serializers.employee_departments_create_serializer import EmployeeDepartmentCreateSerializer
from parameterization.serializers.employee_departments_serializers.employee_departments_list_serializer import EmployeeDepartmentListSerializer
from django.shortcuts import get_object_or_404

class EmployeeDepartmentViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = EmployeeDepartmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Departamento creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
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
        departments = EmployeeDepartment.objects.all()
        serializer = EmployeeDepartmentListSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='list/active')
    def listar_activos(self, request):
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