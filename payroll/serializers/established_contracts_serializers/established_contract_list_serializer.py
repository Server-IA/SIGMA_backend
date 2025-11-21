from rest_framework import serializers
from payroll.models.established_contract import EstablishedContract

class EstablishedContractListSerializer(serializers.ModelSerializer):
    contract_type = serializers.SerializerMethodField()
    contract_type_name = serializers.SerializerMethodField()
    established_contract_status = serializers.SerializerMethodField()
    established_contract_status_name = serializers.SerializerMethodField()

    class Meta:
        model = EstablishedContract
        fields = [
            'contract_code',
            'contract_type',
            'contract_type_name',
            'start_date',
            'end_date',
            'established_contract_status',
            'established_contract_status_name',
            'salary_base'
        ]

    def get_contract_type(self, obj):
        return obj.contract_type_id

    def get_contract_type_name(self, obj):
        return getattr(obj.contract_type, 'name', None) if obj.contract_type_id else None

    def get_established_contract_status(self, obj):
        return obj.established_contract_status_id

    def get_established_contract_status_name(self, obj):
        return getattr(obj.established_contract_status, 'name', None) if obj.established_contract_status_id else None

