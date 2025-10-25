from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from django.db.models import QuerySet


class ReportGenerator(ABC):
    """Interfaz abstracta para generadores de reporte."""
    
    @abstractmethod
    def generate(self, queryset: QuerySet, user_data_map: Dict[int, Dict[str, Any]], 
                 user_info: Dict[str, Any] = None) -> Union[bytes, str]:
        """Genera el reporte en el formato específico."""
        pass


class ExcelReportGenerator(ReportGenerator):
    """Generador de reportes en formato Excel."""
    
    def generate(self, queryset: QuerySet, user_data_map: Dict[int, Dict[str, Any]], 
                 user_info: Dict[str, Any] = None) -> bytes:
        from .report_generator import generate_excel_report
        return generate_excel_report(queryset, user_data_map, user_info)


class CSVReportGenerator(ReportGenerator):
    """Generador de reportes en formato CSV."""
    
    def generate(self, queryset: QuerySet, user_data_map: Dict[int, Dict[str, Any]], 
                 user_info: Dict[str, Any] = None) -> str:
        from .report_generator import generate_csv_report
        return generate_csv_report(queryset, user_data_map, user_info)


class ReportGeneratorFactory:
    """Factory para crear generadores de reporte según el formato."""
    
    _generators = {
        'excel': ExcelReportGenerator,
        'csv': CSVReportGenerator
    }
    
    @classmethod
    def create_generator(cls, format_type: str) -> ReportGenerator:
        """Crea un generador de reporte según el formato especificado."""
        if format_type not in cls._generators:
            raise ValueError(f"Formato no soportado: {format_type}")
        
        return cls._generators[format_type]()
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """Retorna los formatos soportados."""
        return list(cls._generators.keys())
