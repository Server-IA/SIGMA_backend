from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from payroll.models import (
    EstablishedContract, 
    ContractPaymentsEstablishedContract, 
    EstablishedDeduction, 
    EstablishedIncrease,
    DaysOfWeek
)
from payroll.serializers.established_contracts_serializers.established_contract_serializer import (
    EstablishedContractCreateSerializer,
    ContractPaymentEstablishedContractSerializer,
    EstablishedDeductionSerializer,
    EstablishedIncreaseSerializer
)


class EstablishedContractUpdateSerializer(EstablishedContractCreateSerializer):
    contract_payments = ContractPaymentEstablishedContractSerializer(many=True, required=False)
    established_deductions = EstablishedDeductionSerializer(many=True, required=False)
    established_increases = EstablishedIncreaseSerializer(many=True, required=False)

    class Meta(EstablishedContractCreateSerializer.Meta):
        model = EstablishedContract
        fields = EstablishedContractCreateSerializer.Meta.fields
        read_only_fields = [
            'contract_code',
            'creation_date',
            'id_responsible_user',
            'established_contract_status',
            'id_employee_charge'
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        contract_payments_data = validated_data.pop('contract_payments', None)
        deductions_data = validated_data.pop('established_deductions', None)
        increases_data = validated_data.pop('established_increases', None)
        days_of_week = validated_data.pop('days_of_week', None)  # Get days_of_week from validated_data

        for field in self.Meta.read_only_fields:
            validated_data.pop(field, None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle days_of_week if provided
        if days_of_week is not None:
            # Clear existing days
            instance.days_of_week.clear()
            # Add new days if any
            if days_of_week:
                days = DaysOfWeek.objects.filter(id_day_of_week__in=days_of_week)
                instance.days_of_week.set(days)

        if contract_payments_data is not None:
            ContractPaymentsEstablishedContract.objects.filter(
                established_contracts_contract_code=instance
            ).delete()
            self.process_contract_payments(
                instance,
                contract_payments_data,
                instance.payment_frequency_type
            )

        if deductions_data is not None:
            EstablishedDeduction.objects.filter(
                established_contracts_contract_code=instance
            ).delete()
            for deduction in deductions_data:
                EstablishedDeduction.objects.create(
                    established_contracts_contract_code=instance,
                    **deduction
                )

        if increases_data is not None:
            EstablishedIncrease.objects.filter(
                established_contracts_contract_code=instance
            ).delete()
            for increase in increases_data:
                EstablishedIncrease.objects.create(
                    established_contracts_contract_code=instance,
                    **increase
                )

        instance.modification_date = timezone.now()
        instance.save()

        return instance
