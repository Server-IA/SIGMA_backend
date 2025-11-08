# core/services/factus_service.py

import requests
from django.conf import settings
import logging

import base64
import re

logger = logging.getLogger(__name__)

class FactusServiceError(Exception):
    """Excepción para errores de la API de Facturación."""
    pass

class FactusService:
    """Clase para la interacción real con la API de Factus (Sandbox)."""
    
    def __init__(self):
        # Lee las variables de entorno de Django settings
        self.BASE_URL = settings.FACTUS_API_URL.rstrip('/')
        self.CLIENT_ID = settings.FACTUS_CLIENT_ID
        self.CLIENT_SECRET = settings.FACTUS_CLIENT_SECRET
        self.EMAIL = settings.FACTUS_EMAIL
        self.PASSWORD = settings.FACTUS_PASSWORD
        self._token = None
    
    @property
    def token(self):
        """Obtiene el token (solo si no se ha obtenido antes)."""
        if not self._token:
            self._token = self._get_auth_token()
        return self._token
    
    def _get_auth_token(self):
        url = f"{self.BASE_URL}/oauth/token" 
        try:
            response = requests.post(url, data={
                'grant_type': 'password',
                'username': self.EMAIL,  
                'password': self.PASSWORD,
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
            }, timeout=10)
            response.raise_for_status()
            
            return response.json().get('access_token')
            
        except requests.RequestException as e:
            logger.error(f"Factus Auth Error: {e}")
            raise FactusServiceError("Fallo al autenticar con la API de Factus. Revise credenciales y endpoint.")

    # Utilidad: extraer el consecutivo numérico de 'number' (p.ej., SETP990017969 -> 990017969)
    def _extract_number_seq(self, bill_number: str) -> int:
        try:
            if not bill_number:
                return -1
            m = re.search(r"(\d+)$", str(bill_number))
            if m:
                return int(m.group(1))
            return -1
        except Exception:
            return -1

    def generate_invoice(self, payload: dict):
        """
        Envía el payload de factura al endpoint de validación: /v1/bills/validate.
        """
        if not self.token:
            raise FactusServiceError("No se pudo obtener el token de Factus.")

        url = f"{self.BASE_URL}/v1/bills/validate" 
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                return response.json()
            
            error_detail = response.json() if response.content else "Error desconocido."
            logger.error(f"Factus API Error {response.status_code}: {error_detail}")
            raise FactusServiceError(f"Validación rechazada: HTTP {response.status_code}. Detalle: {error_detail}")

        except requests.RequestException as e:
            logger.error(f"Factus Request Exception: {e}")
            raise FactusServiceError("Error de conexión o timeout al intentar validar la factura.")

    def check_and_cleanup_rejected_invoice(self, reference_code: str) -> dict:
        """
        Verifica si existe una factura rechazada (status=0) en Factus con el reference_code dado.
        Si existe, la elimina automáticamente para evitar conflictos.
        
        Returns:
            dict con keys:
                - 'had_rejected': bool - Si había una factura rechazada
                - 'deleted': bool - Si se eliminó exitosamente
                - 'message': str - Mensaje descriptivo
                - 'errors': dict - Errores de la factura rechazada (si existía)
        """
        if not self.token:
            raise FactusServiceError("No se pudo obtener el token de Factus.")
        
        # 1. Consultar facturas por reference_code
        url = f"{self.BASE_URL}/v1/bills"
        params = {
            'filter[reference_code]': reference_code,
            'page[size]': 50,
            'per_page': 50,
        }
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }
        
        try:
            logger.info(f"[CLEANUP] Verificando facturas existentes para reference_code: {reference_code}")
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            
            payload = response.json() if response.content else {}
            data = payload.get('data', {})
            bills = data.get('data', [])
            
            if not bills:
                logger.info(f"[CLEANUP] No hay facturas previas con reference_code: {reference_code}")
                return {
                    'had_rejected': False,
                    'deleted': False,
                    'message': 'No hay facturas previas con este código de referencia.',
                    'errors': None
                }
            
            # 2. Buscar la última factura por campo 'number' (consecutivo)
            bills_sorted = sorted(
                bills,
                key=lambda x: (self._extract_number_seq((x or {}).get('number')), (x or {}).get('id', 0)),
                reverse=True
            )
            last_bill = bills_sorted[0]
            
            bill_status = last_bill.get('status')
            bill_id = last_bill.get('id')
            bill_number = last_bill.get('number')
            bill_errors = last_bill.get('errors', {})
            
            logger.info(f"[CLEANUP] Última factura encontrada: id={bill_id}, number={bill_number}, status={bill_status}")
            
            # 3. Si status=0 (rechazada), eliminarla
            if bill_status == 0:
                logger.warning(f"[CLEANUP] Factura rechazada detectada (status=0). Errores: {bill_errors}")
                logger.info(f"[CLEANUP] Eliminando factura rechazada con reference_code: {reference_code}")
                
                delete_url = f"{self.BASE_URL}/v1/bills/destroy/reference/{reference_code}"
                delete_response = requests.delete(delete_url, headers=headers, timeout=20)
                
                if delete_response.status_code in [200, 204]:
                    logger.info(f"[CLEANUP] ✓ Factura rechazada eliminada exitosamente: {reference_code}")
                    return {
                        'had_rejected': True,
                        'deleted': True,
                        'message': f'Factura rechazada (status=0) eliminada. Errores previos: {list(bill_errors.keys())}',
                        'errors': bill_errors
                    }
                else:
                    logger.error(f"[CLEANUP] ✗ Error al eliminar por referencia: {delete_response.status_code} - {delete_response.text}")
                    # Fallback: intentar eliminar por id si la API lo permite
                    try:
                        if bill_id:
                            del_by_id_url = f"{self.BASE_URL}/v1/bills/destroy/{bill_id}"
                            del_by_id_resp = requests.delete(del_by_id_url, headers=headers, timeout=20)
                            if del_by_id_resp.status_code in [200, 204]:
                                logger.info(f"[CLEANUP] ✓ Eliminada por id id={bill_id} tras fallo por referencia")
                                return {
                                    'had_rejected': True,
                                    'deleted': True,
                                    'message': 'Factura rechazada (status=0) eliminada por id.',
                                    'errors': bill_errors
                                }
                            else:
                                logger.error(f"[CLEANUP] ✗ Error al eliminar por id: {del_by_id_resp.status_code} - {del_by_id_resp.text}")
                    except Exception as ex:
                        logger.error(f"[CLEANUP] Excepción en fallback delete por id: {ex}", exc_info=True)
                    
                    return {
                        'had_rejected': True,
                        'deleted': False,
                        'message': f'No se pudo eliminar la factura rechazada (ref/id). HTTP ref={delete_response.status_code}',
                        'errors': bill_errors
                    }
            else:
                # Status != 0 (probablemente 1 = validada)
                logger.info(f"[CLEANUP] Última factura tiene status={bill_status}, no requiere limpieza")
                return {
                    'had_rejected': False,
                    'deleted': False,
                    'message': f'La última factura tiene status={bill_status}, puede proceder.',
                    'errors': None
                }
                
        except requests.RequestException as e:
            logger.error(f"[CLEANUP] Error consultando/eliminando facturas: {e}", exc_info=True)
            raise FactusServiceError(f"Error al verificar facturas previas: {str(e)}")

    def cleanup_last_pending_for_account(self) -> dict:
        """
        SANDBOX global cleanup:
        - Obtiene las facturas más recientes de Factus (sin filtro de status).
        - Busca la factura con el ID más alto.
        - Si tiene status=1 (validada), no hace nada y permite continuar.
        - Si tiene status=0 (rechazada/pendiente), la elimina por reference_code.

        Returns:
            {
              'found': bool,           # si se encontró alguna factura status=0
              'deleted': bool,         # si se eliminó exitosamente
              'reference_code': str|None,
              'bill_id': int|None,
              'message': str,
              'errors': dict|None,
            }
        """
        if not self.token:
            raise FactusServiceError("No se pudo obtener el token de Factus.")

        url = f"{self.BASE_URL}/v1/bills"
        params = {
            'page[size]': 100,
            'per_page': 100,
        }
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }

        try:
            logger.info("[CLEANUP-SBX] Buscando factura más reciente (ID más alto)")
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()

            payload = response.json() if response.content else {}
            data = payload.get('data', {})
            bills = data.get('data', [])

            if not bills:
                logger.info("[CLEANUP-SBX] No hay facturas en el sistema")
                return {
                    'found': False,
                    'deleted': False,
                    'reference_code': None,
                    'bill_id': None,
                    'message': 'No hay facturas en el sistema.',
                    'errors': None,
                }
            
            # Tomar la factura con el ID más alto (la más reciente)
            last_bill = max(bills, key=lambda x: x.get('id', 0))
            bill_id = last_bill.get('id')
            bill_status = last_bill.get('status')
            ref = last_bill.get('reference_code')
            bill_number = last_bill.get('number')
            errors = last_bill.get('errors', {})

            logger.info(f"[CLEANUP-SBX] Última factura: id={bill_id}, number={bill_number}, status={bill_status}, ref={ref}")

            # Si status=1 (validada), no hacer nada
            if bill_status == 1:
                logger.info(f"[CLEANUP-SBX] ✓ Última factura tiene status=1 (validada), puede proceder directamente")
                return {
                    'found': False,
                    'deleted': False,
                    'reference_code': ref,
                    'bill_id': bill_id,
                    'message': f'Última factura tiene status=1, no requiere limpieza.',
                    'errors': None,
                }
            
            # Si status=0 (rechazada/pendiente), eliminar por reference_code
            if bill_status == 0:
                if not ref:
                    logger.warning(f"[CLEANUP-SBX] Factura {bill_id} con status=0 pero sin reference_code")
                    return {
                        'found': True,
                        'deleted': False,
                        'reference_code': None,
                        'bill_id': bill_id,
                        'message': 'Factura status=0 sin reference_code, no se puede eliminar.',
                        'errors': errors,
                    }

                logger.warning(f"[CLEANUP-SBX] Última factura tiene status=0, eliminando por reference_code: {ref}")
                delete_url = f"{self.BASE_URL}/v1/bills/destroy/reference/{ref}"
                del_resp = requests.delete(delete_url, headers=headers, timeout=20)
                
                if del_resp.status_code in [200, 204]:
                    logger.info(f"[CLEANUP-SBX] ✓ Eliminada factura status=0: id={bill_id}, ref={ref}, number={bill_number}")
                    return {
                        'found': True,
                        'deleted': True,
                        'reference_code': ref,
                        'bill_id': bill_id,
                        'message': f'Factura status=0 eliminada (id={bill_id}).',
                        'errors': errors,
                    }
                else:
                    logger.error(f"[CLEANUP-SBX] ✗ Error al eliminar ref={ref}: {del_resp.status_code} {del_resp.text}")
                    return {
                        'found': True,
                        'deleted': False,
                        'reference_code': ref,
                        'bill_id': bill_id,
                        'message': f'No se pudo eliminar factura status=0 (ref={ref}): HTTP {del_resp.status_code}',
                        'errors': errors,
                    }
            
            # Otros status (no esperados, pero por robustez)
            logger.info(f"[CLEANUP-SBX] Última factura tiene status={bill_status}, continuando")
            return {
                'found': False,
                'deleted': False,
                'reference_code': ref,
                'bill_id': bill_id,
                'message': f'Última factura tiene status={bill_status}.',
                'errors': None,
            }

        except requests.RequestException as e:
            logger.error(f"[CLEANUP-SBX] Error en consulta/eliminación: {e}", exc_info=True)
            raise FactusServiceError(f"Error al limpiar pendientes por cuenta: {str(e)}")

    def _download_invoice_file(self, identifier: str, file_type: str, base64_keys: list, default_filename_prefix: str):
        """
        Método genérico para descargar archivos (PDF o XML) desde Factus.
        
        Args:
            identifier: Número de factura o CUFE
            file_type: 'pdf' o 'xml'
            base64_keys: Lista de posibles claves para el base64 en la respuesta
            default_filename_prefix: Prefijo para nombre de archivo por defecto
        
        Returns:
            tuple: (file_bytes, filename)
        """
        url = f"{self.BASE_URL}/v1/bills/download-{file_type}/{identifier}"
        headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'}
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            payload = response.json() if response.content else None
            if not payload:
                raise FactusServiceError(f"Respuesta vacía al solicitar descarga de {file_type.upper()}.")

            data = payload.get('data') if isinstance(payload, dict) else None
            if not data:
                raise FactusServiceError(f"Formato de respuesta inesperado al descargar {file_type.upper()}: {payload}")

            b64 = None
            for key in base64_keys:
                b64 = data.get(key)
                if b64:
                    break
            
            filename = data.get('file_name') or f"{default_filename_prefix}_{identifier}"

            if not b64:
                raise FactusServiceError(f'El {file_type.upper()} en base64 no fue encontrado en la respuesta de Factus.')

            try:
                file_bytes = base64.b64decode(b64)
            except Exception as e:
                logger.error(f"Error decodificando base64 del {file_type.upper()}: {e}")
                raise FactusServiceError(f'Error al decodificar el {file_type.upper()} recibido desde Factus.')

            if not filename.lower().endswith(f'.{file_type}'):
                filename = f"{filename}.{file_type}"

            return file_bytes, filename
            
        except requests.RequestException as e:
            logger.error(f"Factus {file_type.upper()} Error: {e}")
            raise FactusServiceError(f"Error al descargar el {file_type.upper()} de la factura.")

    def get_invoice_pdf(self, cufe: str):
        """Obtiene el PDF de la factura usando el CUFE."""
        return self._download_invoice_file(
            identifier=cufe,
            file_type='pdf',
            base64_keys=['pdf_base_64_encoded', 'pdf_base64', 'pdf'],
            default_filename_prefix='Factura'
        )

    def get_invoice_pdf_by_number(self, number: str):
        """
        Descarga el PDF usando el número de factura.
        Retorna (bytes_pdf, filename).
        """
        return self._download_invoice_file(
            identifier=number,
            file_type='pdf',
            base64_keys=['pdf_base_64_encoded', 'pdf_base64', 'pdf'],
            default_filename_prefix='Factura'
        )

    def get_invoice_xml_by_number(self, number: str):
        """
        Descarga el XML usando el número de factura desde /v1/bills/download-xml/{number}.
        Retorna (bytes_xml, filename).
        """
        return self._download_invoice_file(
            identifier=number,
            file_type='xml',
            base64_keys=['xml_base_64_encoded', 'xml_base64', 'xml'],
            default_filename_prefix='Factura'
        )

    def get_invoice_xml(self, cufe: str):
        """
        Descarga el XML usando el CUFE (si el endpoint lo soporta).
        Retorna (bytes_xml, filename).
        """
        return self._download_invoice_file(
            identifier=cufe,
            file_type='xml',
            base64_keys=['xml_base_64_encoded', 'xml_base64', 'xml'],
            default_filename_prefix='Factura'
        )

    # ------------------------------
    # Catálogos: Unidades de Medida
    # ------------------------------
    def _get_measurement_units(self):
        """Obtiene el catálogo de unidades de medida desde Factus."""
        if not self.token:
            raise FactusServiceError("No se pudo obtener el token de Factus.")

        url = f"{self.BASE_URL}/v1/measurement-units"
        headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'}
        try:
            logger.info(f"[FACTUS] Solicitando catálogo de unidades de medida: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            logger.info(f"[FACTUS] Respuesta measurement-units: status={response.status_code}")
            response.raise_for_status()
            payload = response.json() if response.content else None
            if not payload or 'data' not in payload:
                logger.error(f"[FACTUS] Respuesta inesperada: {payload}")
                raise FactusServiceError("Respuesta inesperada al consultar unidades de medida.")
            logger.info(f"[FACTUS] Unidades obtenidas: {len(payload['data'])} items")
            return payload['data']
        except requests.RequestException as e:
            logger.error(f"[FACTUS] Measurement Units Error: {e}", exc_info=True)
            raise FactusServiceError("Error al consultar unidades de medida en Factus.")

    def get_measurement_unit_ids(self, refresh: bool = True):
        """Retorna un set de IDs válidos de unidades de medida.
        Por ahora, refresca en cada llamada para asegurar consistencia con Factus.
        """
        if refresh or not hasattr(self, '_mu_cache'):
            data = self._get_measurement_units()
            self._mu_cache = {int(item['id']) for item in data if 'id' in item}
        return self._mu_cache

    def validate_measurement_unit(self, unit_id: int) -> bool:
        """Valida que el ID de unidad de medida exista en Factus."""
        try:
            unit_int = int(unit_id)
            logger.info(f"[FACTUS] Validando unidad de medida: {unit_int}")
            valid_ids = self.get_measurement_unit_ids(refresh=True)
            is_valid = unit_int in valid_ids
            logger.info(f"[FACTUS] Resultado validación: unit={unit_int} valid={is_valid} total_ids={len(valid_ids)}")
            
            # Debug: Si no es válido, mostrar algunos IDs disponibles
            if not is_valid:
                sample_ids = sorted(list(valid_ids))[:10]
                logger.warning(f"[FACTUS] Unit {unit_int} no válido. Ejemplos de IDs válidos: {sample_ids}")
            
            return is_valid
        except Exception as e:
            logger.error(f"[FACTUS] Error validando unidad {unit_id}: {e}", exc_info=True)
            return False

    # ------------------------------
    # Catálogos: Tributos
    # ------------------------------
    def _get_tributes(self, name: str = ""):
        """Obtiene el catálogo de tributos desde Factus.
        
        Args:
            name: Filtro opcional por nombre del tributo
            
        Returns:
            Lista de tributos con su información
        """
        if not self.token:
            raise FactusServiceError("No se pudo obtener el token de Factus.")

        url = f"{self.BASE_URL}/v1/tributes/products"
        params = {}
        if name:
            params['name'] = name
            
        headers = {'Authorization': f'Bearer {self.token}', 'Accept': 'application/json'}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json() if response.content else None
            if not payload or 'data' not in payload:
                raise FactusServiceError("Respuesta inesperada al consultar tributos.")
            return payload['data']
        except requests.RequestException as e:
            logger.error(f"Factus Tributes Error: {e}")
            raise FactusServiceError("Error al consultar tributos en Factus.")

    def get_tribute_info(self, tribute_id: int):
        """Obtiene la información de un tributo específico por su ID.
        
        Args:
            tribute_id: ID del tributo a consultar
            
        Returns:
            dict con información del tributo (id, name, description, etc.) o None si no existe
        """
        try:
            # Obtener todos los tributos y buscar el específico
            tributes = self._get_tributes()
            for tribute in tributes:
                if tribute.get('id') == tribute_id:
                    return tribute
            return None
        except Exception as e:
            logger.error(f"Error obteniendo info de tributo {tribute_id}: {e}")
            return None

    def get_tribute_tax_type(self, tribute_id: int) -> str:
        """Obtiene el tipo de impuesto (tax type) basado en el tribute_id.
        
        Args:
            tribute_id: ID del tributo
            
        Returns:
            str: Nombre del tipo de impuesto (ej: 'IVA', 'INC', etc.) o 'IVA' por defecto
        """
        try:
            tribute_info = self.get_tribute_info(tribute_id)
            if tribute_info:
                # Usar el campo 'name' como tax_type
                # Ejemplos: 'IVA', 'INC', 'Bolsas', etc.
                return tribute_info.get('name', 'IVA')
            return 'IVA'  # Default si no se encuentra
        except Exception as e:
            logger.error(f"Error obteniendo tax_type para tribute {tribute_id}: {e}")
            return 'IVA'  # Default en caso de error