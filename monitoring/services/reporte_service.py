from monitoring.utils.report_factory import ReportGeneratorFactory
from datetime import datetime
from django.db.models import QuerySet
from django.http import HttpResponse

class ReportService:
    """Servicio para manejo de generación de reportes."""

    CONTENT_TYPES = {
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv': 'text/csv; charset=utf-8'
    }
    
    FILE_EXTENSIONS = {
        'excel': 'xlsx',
        'csv': 'csv'
    }
    
    @classmethod
    def generate_report_response(cls, queryset: QuerySet, format_type: str) -> HttpResponse:
        """
        Genera la respuesta HTTP con el reporte.
        
       
        Returns:
            HttpResponse con el archivo del reporte
        """
        # Crear generador según el formato
        generator = ReportGeneratorFactory.create_generator(format_type)
        
        # Generar contenido del reporte
        report_content = generator.generate(queryset)
        
        # Preparar metadatos del archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = cls.FILE_EXTENSIONS[format_type]
        content_type = cls.CONTENT_TYPES[format_type]
        
        # Construir nombre del archivo
        filename = cls._build_filename(timestamp, file_extension, queryset)
        
        # Crear respuesta HTTP
        response = HttpResponse(report_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @classmethod
    def _build_filename(cls, timestamp: str, file_extension: str, queryset: QuerySet) -> str:
        """Construir el nombre del archivo del reporte."""
        base_name = "historical_data_report"
        filename = f"{base_name}_{timestamp}.{file_extension}"
        return filename