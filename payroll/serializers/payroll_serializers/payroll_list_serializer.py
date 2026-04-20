from rest_framework import serializers
import os
import requests
import logging
from typing import Dict, Any, Optional

from payroll.models import Payroll

logger = logging.getLogger(__name__)


class PayrollListSerializer(serializers.ModelSerializer):
    """Serializer para listar nóminas generadas"""

    document_number = serializers.SerializerMethodField()
    employee_full_name = serializers.SerializerMethodField()
    responsible_user_full_name = serializers.SerializerMethodField()
    currency_type_name = serializers.CharField(source="currency_type.name", read_only=True)

    class Meta:
        model = Payroll
        fields = [
            "id_payroll",
            "document_number",
            "employee_full_name",
            "responsible_user_full_name",
            "creation_date",
            "start_date",
            "end_date",
            "currency_type_name",
            "date_payment"
        ]

    # -----------------------------
    #      GET INFO EXTERNA
    # -----------------------------
    def _get_external_user(self, user_id) -> Dict[str, Any]:
        if not user_id:
            return {}

        if not hasattr(self, "_cache"):
            self._cache = {}

        if user_id in self._cache:
            return self._cache[user_id]

        base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
        if not base_url:
            return {}

        url = f"{base_url}/users/users/basic-user-list/by-ids"
        headers = {"Content-Type": "application/json"}

        request = self.context.get("request")
        if request:
            token = request.headers.get("Authorization")
            if token:
                headers["Authorization"] = token

        try:
            resp = requests.post(url, json={"ids": [user_id]}, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    self._cache[user_id] = data[0]
                    return data[0]
        except Exception as e:
            logger.error(f"Error consultando servicio externo: {str(e)}")

        return {}

    # -----------------------------
    # CAMPOS CALCULADOS
    # -----------------------------
    def _get_employee_user(self, obj):
        emp = getattr(obj, "id_employee", None)
        return getattr(emp, "id_user_id", None) if emp else None

    def get_document_number(self, obj):
        user_id = self._get_employee_user(obj)
        return self._get_external_user(user_id).get("document_number")

    def get_employee_full_name(self, obj):
        user_id = self._get_employee_user(obj)
        u = self._get_external_user(user_id)
        return f"{u.get('name', '')} {u.get('first_last_name', '')} {u.get('second_last_name', '')}".strip()

    def get_responsible_user_full_name(self, obj):
        resp = getattr(obj, "id_responsible_user", None)
        user_id = getattr(resp, "id_user", None)
        u = self._get_external_user(user_id)
        return f"{u.get('name', '')} {u.get('first_last_name', '')} {u.get('second_last_name', '')}".strip()
