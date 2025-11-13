from rest_framework import serializers
from django.utils import timezone


class HistoricalDataReportSerializer(serializers.Serializer):
    """
    Serializer para validar los filtros del reporte de datos históricos.
    Todos los campos son opcionales.
    """
    request_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="ID del dispositivo para filtrar"
    )
    # data_type = serializers.CharField(
    #     required=False,
    #     allow_blank=True,
    #     allow_null=True,
    #     help_text="Tipo de dato histórico"
    # )
    # date_from = serializers.DateField(
    #     required=False,
    #     allow_null=True,
    #     help_text="Fecha de inicio del rango (YYYY-MM-DD)"
    # )
    # date_to = serializers.DateField(
    #     required=False,
    #     allow_null=True,
    #     help_text="Fecha de fin del rango (YYYY-MM-DD)"
    # )
    report_format = serializers.ChoiceField(
        choices=[('excel', 'Excel'), ('csv', 'CSV')],
        default='excel',
        help_text="Formato del reporte: excel o csv"
    )

    def vaidate_report_format(self, value):
        """Validar que el formato del reporte sea válido."""
        valid_formats = ['excel', 'csv']
        if value not in valid_formats:
            raise serializers.ValidationError(
                f"Formato de reporte inválido. Los formatos válidos son: {', '.join(valid_formats)}."
            )
        return value
    
    def validate_request_id(self, value):
        """Validar que el ID del dispositivo no esté vacío si se proporciona."""
        if value is not None and value.strip() == "":
            raise serializers.ValidationError(
                "El ID del dispositivo no puede estar vacío."
            )
        return value
    
    