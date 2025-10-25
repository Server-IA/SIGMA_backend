from typing import Dict, Any, Tuple
from django.db.models import QuerySet
from django.http import HttpResponse
from datetime import datetime

from ..utils.report_factory import ReportGeneratorFactory
from ..utils.external_user_helper import get_users_info_batch


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
    def generate_report_response(cls, queryset: QuerySet, format_type: str, 
                                user_data_map: Dict[int, Dict[str, Any]], 
                                user_info: Dict[str, Any] = None,
                                customer_id: int = None,
                                has_list_own_permission: bool = False,
                                has_list_all_permission: bool = False) -> HttpResponse:
        """
        Genera la respuesta HTTP con el reporte.
        
        Args:
            queryset: QuerySet filtrado
            format_type: Tipo de formato ('excel' o 'csv')
            user_data_map: Mapa de datos de usuarios
            user_info: Información del usuario actual
            customer_id: ID del cliente (opcional)
            has_list_own_permission: Si tiene permiso para ver sus propias solicitudes
            has_list_all_permission: Si tiene permiso para ver todas las solicitudes
            
        Returns:
            HttpResponse con el archivo del reporte
        """
        # Crear generador según el formato
        generator = ReportGeneratorFactory.create_generator(format_type)
        
        # Generar contenido del reporte
        report_content = generator.generate(queryset, user_data_map, user_info)
        
        # Preparar metadatos del archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_extension = cls.FILE_EXTENSIONS[format_type]
        content_type = cls.CONTENT_TYPES[format_type]
        
        # Construir nombre del archivo
        filename = cls._build_filename(timestamp, file_extension, user_info, 
                                     customer_id, has_list_own_permission, 
                                     has_list_all_permission, queryset, user_data_map)
        
        # Crear respuesta HTTP
        response = HttpResponse(report_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    @classmethod
    def _build_filename(cls, timestamp: str, file_extension: str, user_info: Dict[str, Any],
                       customer_id: int, has_list_own_permission: bool, 
                       has_list_all_permission: bool, queryset: QuerySet, 
                       user_data_map: Dict[int, Dict[str, Any]]) -> str:
        """Construye el nombre del archivo según las reglas de negocio."""
        base_filename = f'RF_{timestamp}'
        
        # Prioridad 1: Usuario con permiso 168 (sin 149)
        if has_list_own_permission and not has_list_all_permission:
            user_name = cls._get_user_name(user_info)
            if user_name:
                return f'{base_filename}_{user_name}.{file_extension}'
        
        # Prioridad 2: Filtro por cliente (con permiso 149)
        elif customer_id and has_list_all_permission:
            customer_name = cls._get_customer_name(queryset, user_data_map)
            if customer_name:
                return f'{base_filename}_{customer_name}.{file_extension}'
        
        # Prioridad 3: Reporte general
        return f'{base_filename}.{file_extension}'
    
    @classmethod
    def _get_user_name(cls, user_info: Dict[str, Any]) -> str:
        """Extrae y formatea el nombre del usuario."""
        if not user_info:
            return ""
        
        name_parts = []
        for field in ['name', 'first_last_name', 'second_last_name']:
            value = user_info.get(field, '').strip()
            if value:
                name_parts.append(value)
        
        return cls._clean_filename('_'.join(name_parts))
    
    @classmethod
    def _get_customer_name(cls, queryset: QuerySet, user_data_map: Dict[int, Dict[str, Any]]) -> str:
        """Extrae y formatea el nombre del cliente."""
        if not queryset.exists():
            return ""
        
        customer = queryset.first().customer
        if not customer:
            return ""
        
        # Preferir datos externos si existen
        if customer.id_user_id and customer.id_user_id in user_data_map:
            external_user = user_data_map[customer.id_user_id]
            name_parts = []
            for field in ['name', 'first_last_name', 'second_last_name']:
                value = external_user.get(field, '').strip()
                if value:
                    name_parts.append(value)
            return cls._clean_filename('_'.join(name_parts))
        
        # Usar datos de la tabla customers
        name_parts = []
        for field in ['name', 'first_last_name', 'second_last_name']:
            value = getattr(customer, field, '').strip()
            if value:
                name_parts.append(value)
        
        return cls._clean_filename('_'.join(name_parts))
    
    @classmethod
    def _clean_filename(cls, name: str) -> str:
        """Limpia el nombre para usar en archivo."""
        import re
        # Remover caracteres especiales
        cleaned = re.sub(r'[^\w\s-]', '', name).strip()
        # Normalizar espacios y guiones
        cleaned = re.sub(r'[-\s]+', '_', cleaned)
        return cleaned
