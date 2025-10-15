from rest_framework import serializers
import os
import requests
import logging

from service_requests.models import ServiceRequest


class ServiceRequestListSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="id_request", read_only=True)
    customer_id = serializers.IntegerField(source="customer.id_customer", read_only=True)
    legal_entity_name = serializers.CharField(source="customer.legal_entity_name", read_only=True)
    customer_name = serializers.SerializerMethodField()
    request_status_name = serializers.SerializerMethodField()
    request_status_id = serializers.IntegerField(source="request_status.id_statues", read_only=True)
    payment_status_name = serializers.SerializerMethodField()
    payment_status_id = serializers.SerializerMethodField()
    scheduled_date = serializers.DateField(source="scheduled_start_date", read_only=True)
    completion_date = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            "code",
            "customer_id",
            "legal_entity_name",
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
            customer = getattr(obj, "customer", None)
            if not customer:
                return None

            if not hasattr(self, "_ext_users_cache"):
                self._ext_users_cache = {}

            user_id = getattr(customer, "id_user_id", None)
            ext_data = {}
            if user_id:
                if user_id in self._ext_users_cache:
                    ext_data = self._ext_users_cache[user_id]
                else:
                    base_url = os.getenv("AUTH_SERVICE_URL", "").rstrip("/")
                    if base_url:
                        url = f"{base_url}/users/users/basic-user-list/by-ids"
                        headers = {}
                        request = self.context.get("request") if isinstance(self.context, dict) else None
                        if request is not None:
                            auth_header = getattr(request, "META", {}).get("HTTP_AUTHORIZATION") or (request.headers.get("Authorization") if hasattr(request, "headers") else None)
                            if auth_header:
                                headers["Authorization"] = auth_header
                        try:
                            resp = requests.post(url, json={"ids": [user_id]}, headers=headers, timeout=10)
                            if resp.status_code == 200 and resp.content:
                                payload = resp.json() or {}
                                data = payload.get("data") or []
                                if isinstance(data, list):
                                    for u in data:
                                        try:
                                            if u and str(u.get("id")) == str(user_id):
                                                ext_data = u
                                                self._ext_users_cache[user_id] = u
                                                break
                                        except Exception:
                                            continue
                        except Exception:
                            pass

            name = (ext_data.get("name") if isinstance(ext_data, dict) else None) or getattr(customer, "name", None)
            fln = (ext_data.get("first_last_name") if isinstance(ext_data, dict) else None) or getattr(customer, "first_last_name", None)
            sln = (ext_data.get("second_last_name") if isinstance(ext_data, dict) else None) or getattr(customer, "second_last_name", None)
            parts = [p for p in [name, fln, sln] if p]
            return " ".join(parts) if parts else None
        except Exception:
            return None

    def get_request_status_name(self, obj):
        try:
            return obj.request_status.name if obj.request_status else None
        except Exception:
            return None

    def get_payment_status_name(self, obj):
        try:
            return obj.payment_status.name if obj.payment_status else None
        except Exception:
            return None

    def get_payment_status_id(self, obj):
        try:
            return getattr(obj.payment_status, 'id_statues', None) if obj.payment_status else None
        except Exception:
            return None

    def get_completion_date(self, obj):
        try:
            # Si el estado del request es 23, no mostrar fecha de finalización
            try:
                if obj.request_status and getattr(obj.request_status, 'id_statues', None) == 23:
                    return None
            except Exception:
                pass

            if obj.completion_cancellation_datetime:
                return obj.completion_cancellation_datetime.date()
            return None
        except Exception:
            return None
