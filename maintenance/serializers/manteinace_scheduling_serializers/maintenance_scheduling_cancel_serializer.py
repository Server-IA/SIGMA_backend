from rest_framework import serializers


class MaintenanceSchedulingCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=350, allow_blank=False)

    def validate_reason(self, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("La causa de cancelación es obligatoria.")
        return value


