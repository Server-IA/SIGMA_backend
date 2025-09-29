from rest_framework import serializers
from parameterization.models import EmployeeDepartment

class EmployeeDepartmentListSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='id_statues.name', read_only=True)
    class Meta:
        model = EmployeeDepartment
        fields = [
            'id_employee_department',
            'name',
            'description',
            'id_statues',
            'estado'
        ]