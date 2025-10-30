import io
import zipfile
import requests
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class ZipService:
    """
    Servicio para crear archivos ZIP en memoria sin almacenarlos en Firebase.
    Genera ZIP temporal con PDF y XML de facturas para envío por correo.
    """
    
    @staticmethod
    def create_invoice_zip_in_memory(
        pdf_url: str,
        xml_url: str,
        invoice_number: str,
        reference_code: str
    ) -> Tuple[bytes, str]:
        """
        Crea un ZIP en memoria con PDF y XML descargados desde Firebase.
        
        Args:
            pdf_url: URL pública del PDF en Firebase Storage
            xml_url: URL pública del XML en Firebase Storage
            invoice_number: Número de la factura
            reference_code: Código de referencia de la factura
            
        Returns:
            Tuple[bytes, str]: (contenido_zip_en_bytes, nombre_archivo_zip)
            
        Raises:
            Exception: Si hay error al descargar archivos o crear el ZIP
        """
        try:
            # Generar nombre del archivo ZIP y nombre base para archivos internos
            base_name = f"Factura_{invoice_number}_{reference_code}"
            zip_filename = f"{base_name}.zip"
            
            logger.info(f"[ZIP SERVICE] Iniciando creación de ZIP para factura {invoice_number}")
            
            # --- Descargar PDF desde Firebase ---
            logger.info(f"[ZIP SERVICE] Descargando PDF desde: {pdf_url}")
            pdf_response = requests.get(pdf_url, timeout=30)
            pdf_response.raise_for_status()
            pdf_data = pdf_response.content
            pdf_size_mb = len(pdf_data) / (1024 * 1024)
            logger.info(f"[ZIP SERVICE] PDF descargado: {pdf_size_mb:.2f} MB")
            
            # --- Descargar XML desde Firebase ---
            logger.info(f"[ZIP SERVICE] Descargando XML desde: {xml_url}")
            xml_response = requests.get(xml_url, timeout=30)
            xml_response.raise_for_status()
            xml_data = xml_response.content
            xml_size_mb = len(xml_data) / (1024 * 1024)
            logger.info(f"[ZIP SERVICE] XML descargado: {xml_size_mb:.2f} MB")
            
            # --- Crear ZIP en memoria ---
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(f"{base_name}.pdf", pdf_data)
                logger.info(f"[ZIP SERVICE] PDF agregado al ZIP: {base_name}.pdf")
                
                zip_file.writestr(f"{base_name}.xml", xml_data)
                logger.info(f"[ZIP SERVICE] XML agregado al ZIP: {base_name}.xml")
            
            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()
            
            zip_size_mb = len(zip_bytes) / (1024 * 1024)
            logger.info(f"[ZIP SERVICE] ✓ ZIP creado exitosamente: {zip_filename} ({zip_size_mb:.2f} MB)")
            logger.info(f"[ZIP SERVICE] Compresión: {pdf_size_mb + xml_size_mb:.2f} MB → {zip_size_mb:.2f} MB")
            
            return zip_bytes, zip_filename
            
        except requests.RequestException as e:
            error_msg = f"Error al descargar archivos desde Firebase: {str(e)}"
            logger.error(f"[ZIP SERVICE] {error_msg}")
            raise Exception(error_msg)
        except zipfile.BadZipFile as e:
            error_msg = f"Error al crear archivo ZIP: {str(e)}"
            logger.error(f"[ZIP SERVICE] {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error inesperado al crear ZIP: {str(e)}"
            logger.error(f"[ZIP SERVICE] {error_msg}", exc_info=True)
            raise Exception(error_msg)
    
    @staticmethod
    def get_zip_size_mb(zip_bytes: bytes) -> float:
        """
        Calcula el tamaño del ZIP en megabytes.
        
        Args:
            zip_bytes: Contenido del ZIP en bytes
            
        Returns:
            float: Tamaño en MB con 2 decimales
        """
        size_mb = len(zip_bytes) / (1024 * 1024)
        return round(size_mb, 2)
