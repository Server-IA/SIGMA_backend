from rest_framework import serializers
from parameterization.models import EmployeeDepartment

class EmployeeDepartmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDepartment
        fields = [
            'id_employee_department',
            'name',
            'description',
        ]