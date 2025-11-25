import os
import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def get_users_info_batch(user_ids: List[int], request=None) -> Dict[int, Dict[str, Any]]:
    """
    Obtiene información de usuarios en batch desde el servicio externo.
    
    Args:
        user_ids: Lista de IDs de usuarios a consultar
        request: Objeto request para obtener headers de autenticación
        
    Returns:
        Diccionario mapeando user_id -> user_data
    """
    if not user_ids:
        return {}
    
    # Eliminar duplicados manteniendo orden
    unique_user_ids = list(dict.fromkeys(user_ids))
    
    base_url = os.getenv('AUTH_SERVICE_URL', '').rstrip('/')
    if not base_url:
        logger.warning('AUTH_SERVICE_URL no configurado')
        return {}
    
    url = f"{base_url}/users/users/basic-user-list/by-ids"
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Obtener header de autorización del request
    if request is not None:
        auth_header = getattr(request, 'META', {}).get('HTTP_AUTHORIZATION') or (
            request.headers.get('Authorization') if hasattr(request, 'headers') else None
        )
        if auth_header:
            headers['Authorization'] = auth_header
    
    try:
        response = requests.post(
            url,
            json={'ids': unique_user_ids},
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.warning('External user service returned %s', response.status_code)
            return {}
        
        payload = response.json() if response.content else {}
        data = (payload or {}).get('data') or []
        
        if not isinstance(data, list):
            logger.warning('Invalid response format from external user service')
            return {}
        
        # Mapear usuarios por ID
        user_data_map = {}
        for user_data in data:
            try:
                if user_data and 'id' in user_data:
                    user_id = user_data.get('id')
                    if user_id:
                        user_data_map[int(user_id)] = user_data
            except (ValueError, TypeError) as e:
                logger.error(f'Error procesando usuario: {str(e)}')
                continue
        
        return user_data_map
        
    except requests.exceptions.Timeout:
        logger.error('Timeout consultando servicio externo de usuarios')
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f'Error de conexión consultando servicio externo de usuarios: {str(e)}')
        return {}
    except Exception as e:
        logger.error(f'Error inesperado consultando servicio externo de usuarios: {str(e)}')
        return {}


def get_user_display_name(user_data: Optional[Dict[str, Any]]) -> str:
    """
    Construye el nombre completo de un usuario a partir de sus datos.
    
    Args:
        user_data: Diccionario con datos del usuario o None
        
    Returns:
        Nombre completo formateado o cadena vacía si no hay datos
    """
    if not user_data:
        return ''
    
    name_parts = []
    
    # Agregar nombre
    name = user_data.get('name')
    if name and isinstance(name, str):
        name = name.strip()
        if name:
            name_parts.append(name)
    
    # Agregar primer apellido
    first_last_name = user_data.get('first_last_name')
    if first_last_name and isinstance(first_last_name, str):
        first_last_name = first_last_name.strip()
        if first_last_name:
            name_parts.append(first_last_name)
    
    # Agregar segundo apellido
    second_last_name = user_data.get('second_last_name')
    if second_last_name and isinstance(second_last_name, str):
        second_last_name = second_last_name.strip()
        if second_last_name:
            name_parts.append(second_last_name)
    
    return ' '.join(name_parts)
