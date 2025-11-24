import json
from rest_framework import serializers
from payroll.models import TemporaryPayrollAdjustment, EmployeeNews

import pandas as pd
from datetime import datetime


class EmployeeBasicSerializer(serializers.Serializer):
    id_employee = serializers.IntegerField()
    document_number = serializers.CharField()

class UploadMassiveAdjustmentsSerializer(serializers.Serializer):
    """Serializer para validar el request de carga masiva"""
    
    file = serializers.FileField(
        required=True,
        error_messages={
            "required": "Debe adjuntar un archivo Excel para continuar.",
            "invalid": "El archivo enviado no es válido."
        }
    )

    start_date = serializers.DateField(
        required=True,
        format="%Y-%m-%d",
        error_messages={
            "required": "La fecha de inicio del periodo es requerida.",
            "invalid": "El formato de fecha de inicio es inválido. Use YYYY-MM-DD."
        }
    )
    end_date = serializers.DateField(
        required=True,
        format="%Y-%m-%d",
        error_messages={
            "required": "La fecha de fin del periodo es requerida.",
            "invalid": "El formato de fecha de fin es inválido. Use YYYY-MM-DD."
        }
    )
    employees = serializers.CharField(
        required=True,
        error_messages={
            'required': 'La lista de empleados es requerida.'
        }
    )

    def validate_employees(self, value):
        """ Parsear el JSON string y validar estructura"""
        try:
            # Parsear el string JSON
            employees_data = json.loads(value)
            
            # Validar que sea una lista
            if not isinstance(employees_data, list):
                raise serializers.ValidationError(
                    'employees debe ser una lista'
                )
            
            # Validar que no esté vacía
            if len(employees_data) == 0:
                raise serializers.ValidationError(
                    'Debe seleccionar al menos un empleado'
                )
            
            # Validar cada empleado con el serializer
            validated_employees = []
            for i, emp_data in enumerate(employees_data):
                emp_serializer = EmployeeBasicSerializer(data=emp_data)
                if not emp_serializer.is_valid():
                    raise serializers.ValidationError(
                        f'Empleado en posición {i} tiene datos inválidos: {emp_serializer.errors}'
                    )
                validated_employees.append(emp_serializer.validated_data)
            
            return validated_employees
            
        except json.JSONDecodeError as e:
            raise serializers.ValidationError(
                f'El formato de employees no es un JSON válido: {str(e)}'
            )
    
    def validate_file(self, value):
        """Validar que sea un archivo Excel válido"""
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError(
                'El archivo debe ser un Excel (.xlsx o .xls)'
            )
        
        # Validar que no esté vacío
        if value.size == 0:
            raise serializers.ValidationError(
                'No se permite cargar un archivo vacío.'
            )
        
        return value
    
    def validate(self, attrs):
        """Validaciones globales"""
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError(
                'fecha_desde debe ser menor o igual a fecha_hasta'
            )
        return attrs


class AdjustmentRowResultSerializer(serializers.Serializer):
    """Serializer para cada fila procesada del Excel"""
    
    employee_identification = serializers.CharField()
    employee_name = serializers.CharField()
    adjustment_name = serializers.CharField()
    adjustment_type = serializers.CharField()
    amount_type = serializers.CharField()
    amount_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    application_type = serializers.CharField()
    start_date_adjustment = serializers.CharField(allow_blank=True)
    end_date_adjustment = serializers.CharField(allow_blank=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    description = serializers.CharField()
    status = serializers.CharField()  # "Aceptado" o "Rechazado"
    reason_rejection = serializers.CharField(allow_blank=True)


class UploadMassiveAdjustmentsResponseSerializer(serializers.Serializer):
    """Serializer de respuesta completa"""
    batch_id = serializers.UUIDField() 
    total_rows = serializers.IntegerField()
    accepted_rows = serializers.IntegerField()
    rejected_rows = serializers.IntegerField()
    results = AdjustmentRowResultSerializer(many=True)
    temporary_adjustment_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class TemporaryAdjustmentSerializer(serializers.ModelSerializer):
    """Serializer para ajustes temporales"""
    
    employee_name = serializers.SerializerMethodField()
    employee_document = serializers.SerializerMethodField()
    
    class Meta:
        model = TemporaryPayrollAdjustment
        fields = [
            'id_temp_adjustment',
            'employee',
            'adjustment_name',
            'adjustment_type',
            'amount_type',
            'amount_value',
            'application_type',
            'start_date_adjustment',
            'end_date_adjustment',
            'amount',
            'description',
            'status',
            'created_at',
        ]
    
    def get_employee_name(self, obj):
        # Aquí puedes reutilizar la lógica de EmployeeListSerializer
        return f"{obj.employee.first_name} {obj.employee.last_name}"
    
    def get_employee_document(self, obj):
        return obj.employee.document_number
    
