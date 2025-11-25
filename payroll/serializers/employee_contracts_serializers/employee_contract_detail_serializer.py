from rest_framework import serializers

from parameterization.models import EmployeeCharge
from payroll.models import (
    EmployeeContract,
    EmployeeContractDeduction,
    EmployeeContractIncrease,
    EmployeeContractPayment,
    DaysOfWeek,
)


class EmployeeContractPaymentSerializer(serializers.ModelSerializer):
    day_of_week_name = serializers.CharField(
        source="id_day_of_week.name", read_only=True, allow_null=True
    )

    class Meta:
        model = EmployeeContractPayment
        fields = ["id_day_of_week", "day_of_week_name", "date_payment"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get("id_day_of_week") is None:
            representation["day_of_week_name"] = None
        elif isinstance(representation["id_day_of_week"], dict):
            representation["day_of_week_name"] = representation["id_day_of_week"].get("name")
            representation["id_day_of_week"] = representation["id_day_of_week"].get("id_day_of_week")
        return representation


class EmployeeContractDeductionSerializer(serializers.ModelSerializer):
    deduction_type_name = serializers.CharField(source="deduction_type.name", read_only=True)

    class Meta:
        model = EmployeeContractDeduction
        fields = [
            "deduction_type",
            "deduction_type_name",
            "amount_type",
            "amount_value",
            "application_deduction_type",
            "start_date_deduction",
            "end_date_deductions",
            "description",
            "amount",
        ]


class DayOfWeekSerializer(serializers.ModelSerializer):
    class Meta:
        model = DaysOfWeek
        fields = ['id_day_of_week', 'name']


class EmployeeContractIncreaseSerializer(serializers.ModelSerializer):
    increase_type_name = serializers.CharField(source="increase_type.name", read_only=True)

    class Meta:
        model = EmployeeContractIncrease
        fields = [
            "increase_type",
            "increase_type_name",
            "amount_type",
            "amount_value",
            "application_increase_type",
            "start_date_increase",
            "end_date_increase",
            "description",
            "amount",
        ]


class EmployeeContractDetailSerializer(serializers.ModelSerializer):
    contract_type_name = serializers.CharField(source="contract_type.name", read_only=True)
    workday_type_name = serializers.CharField(source="workday_type.name", read_only=True)
    work_mode_type_name = serializers.CharField(source="work_mode_type.name", read_only=True)
    currency_type_name = serializers.CharField(source="currency_type.name", read_only=True)
    contract_status_name = serializers.CharField(source="contract_status.name", read_only=True)
    employee_charge_name = serializers.SerializerMethodField()
    contract_payments = EmployeeContractPaymentSerializer(many=True, read_only=True)
    employee_contract_deductions = EmployeeContractDeductionSerializer(
        many=True, read_only=True
    )
    employee_contract_increases = EmployeeContractIncreaseSerializer(
        many=True, read_only=True
    )
    days_of_week = DayOfWeekSerializer(source='days_of_week.all', many=True, read_only=True)

    class Meta:
        model = EmployeeContract
        fields = [
            "contract_code",
            "id_employee_charge",
            "employee_charge_name",
            "description",
            "contract_type",
            "contract_type_name",
            "start_date",
            "end_date",
            "payment_frequency_type",
            "minimum_hours",
            "workday_type",
            "workday_type_name",
            "work_mode_type",
            "work_mode_type_name",
            "salary_type",
            "working_hours",
            "salary_base",
            "currency_type",
            "currency_type_name",
            "trial_period_days",
            "vacation_days",
            "vacation_frequency_days",
            "cumulative_vacation",
            "start_cumulative_vacation",
            "maximum_disability_days",
            "overtime",
            "overtime_period",
            "notice_period_days",
            "contract_status",
            "contract_status_name",
            "contract_payments",
            "days_of_week",
            "employee_contract_deductions",
            "employee_contract_increases",
        ]
        read_only_fields = ["contract_code"]

    def get_employee_charge_name(self, obj):
        try:
            return obj.id_employee_charge.name if obj.id_employee_charge else None
        except EmployeeCharge.DoesNotExist:
            return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        date_fields = ["start_date", "end_date", "start_cumulative_vacation"]
        for field in date_fields:
            if representation.get(field):
                representation[field] = representation[field].split("T")[0]

        for deduction in representation.get("employee_contract_deductions", []):
            for date_field in ["start_date_deduction", "end_date_deductions"]:
                if deduction.get(date_field):
                    deduction[date_field] = deduction[date_field].split("T")[0]

        for increase in representation.get("employee_contract_increases", []):
            for date_field in ["start_date_increase", "end_date_increase"]:
                if increase.get(date_field):
                    increase[date_field] = increase[date_field].split("T")[0]

        return representation
