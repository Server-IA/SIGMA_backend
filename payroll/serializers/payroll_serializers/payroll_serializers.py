from rest_framework import serializers
from django.db.models import Q
from datetime import date, datetime, timedelta
import re
from django.utils import timezone
from django.db import transaction
from payroll.models import (
    Payroll, Employee, EmployeeContract, PayrollDeduction, 
    PayrollIncrease, EmployeeContractDeduction, EmployeeContractIncrease,
    DaysOfWeek
)

class PayrollCreateSerializer(serializers.ModelSerializer):
    id_employee = serializers.IntegerField(write_only=True)
    contract_code = serializers.CharField(write_only=True)
    additional_deductions = serializers.ListField(
        child=serializers.DictField(), 
        required=False, 
        default=[]
    )
    additional_increases = serializers.ListField(
        child=serializers.DictField(), 
        required=False, 
        default=[]
    )
    
    class Meta:
        model = Payroll
        fields = [
            'id_employee', 
            'contract_code',
            'start_date', 
            'end_date',
            'time_worked',
            'total_deductions',
            'total_increments',
            'net_pay',
            'base_salary',
            'additional_deductions',
            'additional_increases'
        ]
        read_only_fields = [
            'time_worked', 'total_deductions', 'total_increments', 
            'net_pay', 'base_salary'
        ]
    
    def validate_id_employee(self, value):
        try:
            employee = Employee.objects.get(id_employee=value, employee_status_id=1)
            return employee
        except Employee.DoesNotExist:
            raise serializers.ValidationError("Employee does not exist or is not active")
            
    def get_latest_contract_version(self, base_code):
        match = re.match(r'^(.*?)(-\d{2})?$', base_code)
        if not match:
            raise serializers.ValidationError("Invalid contract code format")
            
        base = match.group(1)
        contracts = EmployeeContract.objects.filter(
            contract_code__startswith=f"{base}-"
        ).order_by('-contract_code')
        
        if not contracts.exists():
            raise serializers.ValidationError("No valid contract found with the provided code")
            
        return contracts.first()
        
    def validate_contract_code(self, value):
        contract = self.get_latest_contract_version(value)
        self.contract = contract
        return value
        
    def calculate_working_days(self, contract, start_date, end_date):
        if contract.salary_type == 'Mensual fijo':
            return (end_date - start_date).days + 1  # Total days in range
        
        # Get the days of week for this contract
        days_of_week = list(contract.days_of_week.values_list('id_day_of_week', flat=True))
        if not days_of_week:
            return 0
            
        # Calculate working days in the date range
        delta = timedelta(days=1)
        current_date = start_date
        working_days = 0
        
        while current_date <= end_date:
            if current_date.weekday() + 1 in days_of_week:  # weekday() returns 0=Monday, 6=Sunday
                working_days += 1
            current_date += delta
            
        return working_days

    def calculate_time_worked(self, contract, start_date, end_date):
        working_days = self.calculate_working_days(contract, start_date, end_date)
        
        if contract.salary_type == 'Por horas':
            return working_days * (contract.working_hours or 0)
        elif contract.salary_type == 'Por días':
            return working_days
        elif contract.salary_type == 'Mensual fijo':
            return working_days / 30.0  # Convert to months
        return 0

    def calculate_amount(self, item, base_amount, is_percentage=True):
        amount = item.get('amount', 1.0) or 1.0
        if is_percentage:
            return (item['amount_value'] * (base_amount / 100.0)) * amount
        return item['amount_value'] * amount

    def process_deductions_increases(self, items, base_amount, application_type, is_percentage):
        total = 0
        results = []
        
        for item in items:
            if (item.get('start_date') and item['start_date'] > self.end_date) or \
               (item.get('end_date') and item['end_date'] < self.start_date):
                continue
                
            amount = self.calculate_amount(item, base_amount, is_percentage)
            total += amount
            
            result = item.copy()
            result['calculated_amount'] = amount
            result['application_type'] = application_type
            results.append(result)
            
        return total, results
    
    def validate_additional_items(self, items, item_type):
        if not items:
            return items
            
        valid_application_types = ['SalarioBase', 'SalarioFinal']
        valid_amount_types = ['Porcentaje', 'fijo']
        
        for item in items:
            # Validate required fields
            if 'type' not in item:
                raise serializers.ValidationError({"type": f"El tipo de {item_type} es requerido"})
                
            if 'amount_type' not in item:
                raise serializers.ValidationError({"amount_type": f"El tipo de monto para {item_type} es requerido"})
                
            if 'amount_value' not in item:
                raise serializers.ValidationError({"amount_value": f"El valor del monto para {item_type} es requerido"})
                
            if 'application_type' not in item:
                raise serializers.ValidationError({"application_type": f"El tipo de aplicación para {item_type} es requerido"})
            
            # Validate amount types
            if item['amount_type'] not in valid_amount_types:
                raise serializers.ValidationError({
                    "amount_type": f"Tipo de monto inválido. Debe ser uno de: {', '.join(valid_amount_types)}"
                })
                
            # Validate application types
            if item.get('application_type') not in valid_application_types:
                raise serializers.ValidationError({
                    "application_type": f"Tipo de aplicación inválido. Debe ser uno de: {', '.join(valid_application_types)}"
                })
                
            # Validate amount_value is not negative
            if item['amount_value'] < 0:
                raise serializers.ValidationError({"amount_value": "El valor no puede ser negativo"})
                
            # Validate amount is not negative if provided
            if 'amount' in item and item['amount'] is not None and item['amount'] < 0:
                raise serializers.ValidationError({"amount": "El monto no puede ser negativo"})
                
            # Validate percentage amount doesn't exceed 100
            if item['amount_type'] == 'Porcentaje' and item['amount_value'] > 100:
                raise serializers.ValidationError({
                    "amount_value": "El valor no puede ser mayor a 100 cuando el tipo es porcentaje"
                })
                
            # Set default amount if not provided
            if 'amount' not in item or item['amount'] is None:
                item['amount'] = 1.0
                
        return items
        
    def validate(self, data):
        # Basic validation
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError({"end_date": "La fecha de fin debe ser posterior a la fecha de inicio"})
            
        # Validate additional deductions and increases
        if 'additional_deductions' in data:
            data['additional_deductions'] = self.validate_additional_items(
                data['additional_deductions'], 'deducción'
            )
            
        if 'additional_increases' in data:
            data['additional_increases'] = self.validate_additional_items(
                data['additional_increases'], 'incremento'
            )
            
        # Validate no date range overlap with existing payrolls for the same contract (any version)
        if hasattr(self, 'contract') and self.contract:
            # Get base contract code without version (everything before the last hyphen)
            contract_code_parts = self.contract.contract_code.rsplit('-', 1)
            base_contract_code = contract_code_parts[0] if len(contract_code_parts) > 1 else self.contract.contract_code
            
            # Find all versions of this contract
            overlapping_payrolls = Payroll.objects.filter(
                id_employee_contract__contract_code__startswith=f"{base_contract_code}-",
                id_employee=data['id_employee'],
                start_date__lt=data['end_date'],
                end_date__gt=data['start_date']
            )
            
            # If updating, exclude current payroll from the check
            if self.instance:
                overlapping_payrolls = overlapping_payrolls.exclude(id_payroll=self.instance.id_payroll)
                
            if overlapping_payrolls.exists():
                # Get the overlapping payroll for error message
                overlap = overlapping_payrolls.first()
                raise serializers.ValidationError({
                    "date_range": (
                        f"El rango de fechas se cruza con una nómina existente para este contrato. "
                        f"Conflicto con nómina {overlap.id_payroll} ({overlap.start_date} - {overlap.end_date})"
                    )
                })

        contract = self.contract
        if not contract:
            raise serializers.ValidationError({"contract": "No valid contract found"})

        # Validate date range is within contract dates
        if (data['start_date'] < contract.start_date or 
            (contract.end_date and data['end_date'] > contract.end_date)):
            raise serializers.ValidationError({
                "date_range": f"Date range must be within contract dates ({contract.start_date} - {contract.end_date or 'Ongoing'})"
            })

        # Store for use in create method
        self.start_date = data['start_date']
        self.end_date = data['end_date']
        self.contract = contract

        # Calculate base salary and time worked
        time_worked = self.calculate_time_worked(contract, data['start_date'], data['end_date'])
        base_salary_calculated = contract.salary_base * time_worked

        # Process contract deductions and increases
        contract_deductions = contract.employee_contract_deductions.filter(
            Q(start_date_deduction__isnull=True) | Q(start_date_deduction__lte=self.end_date),
            Q(end_date_deductions__isnull=True) | Q(end_date_deductions__gte=self.start_date)
        )
        
        contract_increases = contract.employee_contract_increases.filter(
            Q(start_date_increase__isnull=True) | Q(start_date_increase__lte=self.end_date),
            Q(end_date_increase__isnull=True) | Q(end_date_increase__gte=self.start_date)
        )

        # Process SalarioBase calculations
        base_deductions = [{
            'type': d.deduction_type_id,
            'amount_type': d.amount_type,
            'amount_value': d.amount_value,
            'amount': d.amount or 1.0,
            'description': d.description,
            'start_date': d.start_date_deduction,
            'end_date': d.end_date_deductions
        } for d in contract_deductions if d.application_deduction_type == 'SalarioBase'] + \
        [d for d in data.get('additional_deductions', []) if d.get('application_deduction_type') == 'SalarioBase']
        
        base_increases = [{
            'type': i.increase_type_id,
            'amount_type': i.amount_type,
            'amount_value': i.amount_value,
            'amount': i.amount or 1.0,
            'description': i.description,
            'start_date': i.start_date_increase,
            'end_date': i.end_date_increase
        } for i in contract_increases if i.application_increase_type == 'SalarioBase'] + \
        [i for i in data.get('additional_increases', []) if i.get('application_increase_type') == 'SalarioBase']

        # Calculate base amounts
        total_base_deductions, base_deduction_results = self.process_deductions_increases(
            base_deductions, base_salary_calculated, 'SalarioBase', True
        )
        
        total_base_increases, base_increase_results = self.process_deductions_increases(
            base_increases, base_salary_calculated, 'SalarioBase', True
        )

        net_pay_salary_base = (base_salary_calculated + total_base_increases) - total_base_deductions

        # Process SalarioFinal calculations
        final_deductions = [{
            'type': d.deduction_type_id,
            'amount_type': d.amount_type,
            'amount_value': d.amount_value,
            'amount': d.amount or 1.0,
            'description': d.description,
            'start_date': d.start_date_deduction,
            'end_date': d.end_date_deductions
        } for d in contract_deductions if d.application_deduction_type == 'SalarioFinal'] + \
        [d for d in data.get('additional_deductions', []) if d.get('application_deduction_type') == 'SalarioFinal']
        
        final_increases = [{
            'type': i.increase_type_id,
            'amount_type': i.amount_type,
            'amount_value': i.amount_value,
            'amount': i.amount or 1.0,
            'description': i.description,
            'start_date': i.start_date_increase,
            'end_date': i.end_date_increase
        } for i in contract_increases if i.application_increase_type == 'SalarioFinal'] + \
        [i for i in data.get('additional_increases', []) if i.get('application_increase_type') == 'SalarioFinal']

        total_final_deductions, final_deduction_results = self.process_deductions_increases(
            final_deductions, net_pay_salary_base, 'SalarioFinal', True
        )
        
        total_final_increases, final_increase_results = self.process_deductions_increases(
            final_increases, net_pay_salary_base, 'SalarioFinal', True
        )

        # Calculate final amounts
        net_pay_salary_final = (net_pay_salary_base + total_final_increases) - total_final_deductions
        total_deductions = total_base_deductions + total_final_deductions
        total_increases = total_base_increases + total_final_increases

        # Final validation
        if net_pay_salary_final < 0:
            raise serializers.ValidationError({
                "net_pay": "Net pay cannot be negative. Please adjust deductions or increases."
            })

        # Store calculation results for create method
        self.calculation_results = {
            'time_worked': time_worked,
            'base_salary_calculated': base_salary_calculated,
            'net_pay': net_pay_salary_final,
            'total_deductions': total_deductions,
            'total_increases': total_increases,
            'base_deduction_results': base_deduction_results,
            'base_increase_results': base_increase_results,
            'final_deduction_results': final_deduction_results,
            'final_increase_results': final_increase_results,
            'contract_deductions': list(contract_deductions),
            'contract_increases': list(contract_increases)
        }

        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # Remove fields not in the Payroll model
        contract_code = validated_data.pop('contract_code', None)
        additional_deductions = validated_data.pop('additional_deductions', [])
        additional_increases = validated_data.pop('additional_increases', [])

        # Get the authenticated user
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            raise serializers.ValidationError({"user": "Authentication credentials were not provided."})

        # Create the payroll
        payroll = Payroll.objects.create(
            **validated_data,
            id_employee_contract=self.contract,
            creation_date=timezone.now(),
            id_responsible_user=request.user,
            time_worked=self.calculation_results['time_worked'],
            base_salary=self.contract.salary_base,
            total_deductions=self.calculation_results['total_deductions'],
            total_increments=self.calculation_results['total_increases'],
            net_pay=self.calculation_results['net_pay']
        )

        # Create payroll deductions and increases
        self.create_payroll_items(
            payroll, 
            self.calculation_results['base_deduction_results'] + self.calculation_results['final_deduction_results'],
            PayrollDeduction,
            'deduction_type',
            self.contract.currency_type
        )
        
        self.create_payroll_items(
            payroll,
            self.calculation_results['base_increase_results'] + self.calculation_results['final_increase_results'],
            PayrollIncrease,
            'increase_type',
            self.contract.currency_type
        )

        return payroll
        
    def create_payroll_items(self, payroll, items, model, type_field, currency_type):
        for item in items:
            model.objects.create(
                payroll=payroll,
                **{type_field: item['type']},
                amount_type=item['amount_type'],
                amount_value=item['amount_value'],
                application_type=item['application_type'],
                description=item.get('description', ''),
                amount=item.get('amount', 1.0) or 1.0,
                calculated_amount=item['calculated_amount'],
                currency_type=currency_type
            )
        
    def to_representation(self, instance):
        # Return the full payroll details in the response
        from rest_framework import serializers as drf_serializers
        
        class ContractSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = EmployeeContract
                fields = ['contract_code', 'start_date', 'end_date', 'salary_base']
        
        class EmployeeSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = Employee
                fields = ['id_employee', 'email']
        
        representation = super().to_representation(instance)
        representation['id_employee_contract'] = ContractSerializer(instance.id_employee_contract).data
        representation['id_employee'] = EmployeeSerializer(instance.id_employee).data
        return representation
