from rest_framework import serializers
from parameterization.models import EmployeeDepartments

class EmployeeDepartmentsListSerializer(serializers.ModelSerializer):
    status_display=serializers.SerializerMethodField()

    class Meta:
        model=EmployeeDepartments
        fields=['id','name','description','status_display']

    def get_status_display(self,obj):
        return "Activo" if obj.status else "Inactivo"
