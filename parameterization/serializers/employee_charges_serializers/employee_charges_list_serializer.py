from rest_framework import serializers
from parameterization.models import EmployeeCharge

class EmployeeChargeListSerializer(serializers.ModelSerializer):
    estado = serializers.CharField(source='id_statues.name', read_only=True)
    departamento = serializers.CharField(source='id_employee_department.name', read_only=True)

    class Meta:
        model = EmployeeCharge
        fields = [
            'id_employee_charge',
            'name',
            'description',
            'departamento',
            'estado',
        ]
