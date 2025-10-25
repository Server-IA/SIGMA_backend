from rest_framework import serializers
from django.utils import timezone
from datetime import datetime


class ServiceRequestReportSerializer(serializers.Serializer):
    """
    Serializer para validar los filtros del reporte de solicitudes de servicio.
    Todos los campos son opcionales.
    """
    customer_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID del cliente para filtrar"
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
    scheduled_start_date_from = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Fecha de inicio programada desde (YYYY-MM-DD)"
    )
    scheduled_start_date_to = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Fecha de inicio programada hasta (YYYY-MM-DD)"
    )
    report_format = serializers.ChoiceField(
        choices=[('excel', 'Excel'), ('csv', 'CSV')],
        default='excel',
        help_text="Formato del reporte: excel o csv"
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

    def validate_scheduled_start_date_from(self, value):
        """Validar que la fecha de inicio programada desde no sea futura."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de inicio programada desde no puede ser futura."
            )
        return value

    def validate_scheduled_start_date_to(self, value):
        """Validar que la fecha de inicio programada hasta no sea futura."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de inicio programada hasta no puede ser futura."
            )
        return value

    def validate_report_format(self, value):
        """Validar que el formato sea válido."""
        if value not in ['excel', 'csv']:
            raise serializers.ValidationError(
                "El formato debe ser 'excel' o 'csv'."
            )
        return value

    def validate(self, attrs):
        """Validar rangos de fechas."""
        # Validar rango de fechas de registro
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                'date_from': 'La fecha de inicio debe ser menor o igual a la fecha de fin.',
                'date_to': 'La fecha de fin debe ser mayor o igual a la fecha de inicio.'
            })
        
        # Validar rango de fechas programadas
        scheduled_from = attrs.get('scheduled_start_date_from')
        scheduled_to = attrs.get('scheduled_start_date_to')
        
        if scheduled_from and scheduled_to and scheduled_from > scheduled_to:
            raise serializers.ValidationError({
                'scheduled_start_date_from': 'La fecha de inicio programada desde debe ser menor o igual a la fecha hasta.',
                'scheduled_start_date_to': 'La fecha de inicio programada hasta debe ser mayor o igual a la fecha desde.'
            })
        
        return attrs
