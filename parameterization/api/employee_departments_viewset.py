from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from parameterization.models import EmployeeDepartment
from parameterization.serializers.employee_departments_serializers.employee_departments_create_serializer import EmployeeDepartmentCreateSerializer

class EmployeeDepartmentViewSet(viewsets.ViewSet):

    def create(self, request):
        serializer = EmployeeDepartmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Departamento creado exitosamente"},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)