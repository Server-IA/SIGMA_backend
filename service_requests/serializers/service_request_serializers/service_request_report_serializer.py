from rest_framework import serializers
from django.utils import timezone
from datetime import datetime


class ServiceRequestReportSerializer(serializers.Serializer):
    """
    Serializer para validar los filtros del reporte de solicitudes de servicio.
    Todos los campos son opcionales.
    """
    format = serializers.ChoiceField(
        choices=['excel', 'csv'],
        required=True,
        help_text="Formato del reporte: 'excel' o 'csv'"
    )
    customer_document = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Documento del cliente para filtrar"
    )
    request_status = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID del estado de la solicitud"
    )
    date_from = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Fecha de inicio del rango (YYYY-MM-DD)"
    )
    date_to = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Fecha de fin del rango (YYYY-MM-DD)"
    )
    payment_method = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Código del método de pago"
    )

    def validate_date_from(self, value):
        """Validar que la fecha de inicio no sea futura."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de inicio no puede ser futura."
            )
        return value

    def validate_date_to(self, value):
        """Validar que la fecha de fin no sea futura."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de fin no puede ser futura."
            )
        return value

    def validate(self, attrs):
        """Validar que date_from <= date_to si ambas están presentes."""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                'date_from': 'La fecha de inicio debe ser menor o igual a la fecha de fin.',
                'date_to': 'La fecha de fin debe ser mayor o igual a la fecha de inicio.'
            })
        
        return attrs
