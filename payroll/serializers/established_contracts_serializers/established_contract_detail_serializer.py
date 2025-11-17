from rest_framework import serializers
from payroll.models import (
    EstablishedContract, 
    ContractPaymentsEstablishedContract, 
    EstablishedDeduction, 
    EstablishedIncrease
)
from parameterization.models import Types, Units, Statues, EmployeeCharge


class ContractPaymentSerializer(serializers.ModelSerializer):
    day_of_week_name = serializers.CharField(source='id_day_of_week.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ContractPaymentsEstablishedContract
        fields = ['id_day_of_week', 'day_of_week_name', 'date_payment']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # If id_day_of_week is None, ensure day_of_week_name is also None
        if representation.get('id_day_of_week') is None:
            representation['day_of_week_name'] = None
        else:
            # If id_day_of_week is a dictionary (from nested serializer), extract the name
            if isinstance(representation['id_day_of_week'], dict):
                representation['day_of_week_name'] = representation['id_day_of_week'].get('name')
                representation['id_day_of_week'] = representation['id_day_of_week'].get('id_day_of_week')
        return representation


class EstablishedDeductionSerializer(serializers.ModelSerializer):
    deduction_type_name = serializers.CharField(source='deduction_type.name', read_only=True)
    
    class Meta:
        model = EstablishedDeduction
        fields = [
            'deduction_type', 'deduction_type_name', 'amount_type', 
            'amount_value', 'application_deduction_type', 'start_date_deduction',
            'end_date_deductions', 'description', 'amount'
        ]


class EstablishedIncreaseSerializer(serializers.ModelSerializer):
    increase_type_name = serializers.CharField(source='increase_type.name', read_only=True)
    
    class Meta:
        model = EstablishedIncrease
        fields = [
            'increase_type', 'increase_type_name', 'amount_type', 
            'amount_value', 'application_increase_type', 'start_date_increase',
            'end_date_increase', 'description', 'amount'
        ]


class EstablishedContractDetailSerializer(serializers.ModelSerializer):
    # Basic contract fields
    contract_type_name = serializers.CharField(source='contract_type.name', read_only=True)
    workday_type_name = serializers.CharField(source='workday_type.name', read_only=True)
    work_mode_type_name = serializers.CharField(source='work_mode_type.name', read_only=True)
    currency_type_name = serializers.CharField(source='currency_type.name', read_only=True)
    established_contract_status_name = serializers.CharField(source='established_contract_status.name', read_only=True)
    employee_charge_name = serializers.SerializerMethodField()
    
    def get_employee_charge_name(self, obj):
        try:
            return obj.id_employee_charge.name if obj.id_employee_charge else None
        except EmployeeCharge.DoesNotExist:
            return None
    
    # Related fields
    contract_payments = ContractPaymentSerializer(many=True, read_only=True)
    established_deductions = EstablishedDeductionSerializer(many=True, read_only=True)
    established_increases = EstablishedIncreaseSerializer(many=True, read_only=True)
    
    class Meta:
        model = EstablishedContract
        fields = [
            'contract_code', 'id_employee_charge', 'employee_charge_name', 'description', 
            'contract_type', 'contract_type_name', 'start_date', 'end_date',
            'payment_frequency_type', 'minimum_hours', 'workday_type',
            'workday_type_name', 'work_mode_type', 'work_mode_type_name',
            'salary_type', 'salary_base', 'currency_type', 'currency_type_name',
            'trial_period_days', 'vacation_days', 'vacation_frequency_days',
            'cumulative_vacation', 'start_cumulative_vacation',
            'maximum_disability_days', 'overtime', 'overtime_period',
            'notice_period_days', 'established_contract_status',
            'established_contract_status_name', 'contract_payments',
            'established_deductions', 'established_increases'
        ]
        read_only_fields = ['contract_code', 'creation_date', 'modification_date']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Ensure all date fields are in the correct format
        date_fields = ['start_date', 'end_date', 'start_cumulative_vacation']
        for field in date_fields:
            if representation.get(field):
                representation[field] = representation[field].split('T')[0]
        
        # Format nested date fields
        for deduction in representation.get('established_deductions', []):
            for date_field in ['start_date_deduction', 'end_date_deductions']:
                if deduction.get(date_field):
                    deduction[date_field] = deduction[date_field].split('T')[0]
        
        for increase in representation.get('established_increases', []):
            for date_field in ['start_date_increase', 'end_date_increase']:
                if increase.get(date_field):
                    increase[date_field] = increase[date_field].split('T')[0]
        
        return representation
