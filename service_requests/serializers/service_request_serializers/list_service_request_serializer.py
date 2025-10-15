from rest_framework import serializers

from service_requests.models import ServiceRequest


class ServiceRequestListSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="id_request", read_only=True)
    customer_id = serializers.IntegerField(source="customer.id_customer", read_only=True)
    customer_name = serializers.SerializerMethodField()
    request_status_name = serializers.SerializerMethodField()
    request_status_id = serializers.IntegerField(source="request_status.id_statues", read_only=True)
    payment_status_name = serializers.SerializerMethodField()
    payment_status_id = serializers.IntegerField(source="payment_status.id_statues", read_only=True)
    scheduled_date = serializers.DateField(source="scheduled_start_date", read_only=True)
    completion_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "code",
            "customer_id",
            "customer_name",
            "request_status_id",
            "request_status_name",
            "payment_status_id",
            "payment_status_name",
            "scheduled_date",
            "completion_date",
        ]

    def get_customer_name(self, obj):
        try:
            return str(obj.customer) if obj.customer else None
        except Exception:
            return None

    def get_request_status_name(self, obj):
        try:
            return str(obj.request_status) if obj.request_status else None
        except Exception:
            return None

    def get_payment_status_name(self, obj):
        try:
            return str(obj.payment_status) if obj.payment_status else None
        except Exception:
            return None

    def get_completion_date(self, obj):
        try:
            if obj.completion_cancellation_datetime:
                return obj.completion_cancellation_datetime.date()
            return None
        except Exception:
            return None
