from rest_framework import serializers


class PayrollHistoryReportSerializer(serializers.Serializer):
    employeeIdentification = serializers.CharField(max_length=50)
    dateFrom = serializers.DateField(input_formats=["%Y-%m-%d"])
    dateTo = serializers.DateField(input_formats=["%Y-%m-%d"])
    reportType = serializers.CharField(max_length=50)

    def validate(self, attrs):
        date_from = attrs.get("dateFrom")
        date_to = attrs.get("dateTo")
        report_type = attrs.get("reportType")

        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError({
                "dateTo": ["La fecha hasta debe ser mayor o igual a la fecha desde."]
            })

        # Validar tipo de reporte esperado (HU-NOV-004: historial de nóminas)
        expected_type = "PAYROLL_HISTORY"
        if report_type != expected_type:
            raise serializers.ValidationError({
                "reportType": [f"Tipo de informe inválido. Debe ser '{expected_type}'."]
            })

        return attrs
