import os
import uuid
from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from config.firebase_config import bucket

def upload_file_to_firebase(
    file,
    directory: str,
    allowed_extensions: list = None,
    max_size_mb: int = 10
) -> str:
    """
    Sube un archivo a Firebase Storage y devuelve la URL pública.
    
    Args:
        file: Archivo a subir (InMemoryUploadedFile, TemporaryUploadedFile o similar).
        directory: Directorio donde se guardará el archivo (ej: 'machinery/images/').
        allowed_extensions: Lista de extensiones permitidas (ej: ['.jpg', '.png', '.jpeg', '.pdf']).
        max_size_mb: Tamaño máximo permitido en MB.

    Returns:
        str: URL pública del archivo subido.
    """
    try:
        # Validar extensión del archivo
        file_extension = os.path.splitext(file.name)[1].lower()
        if allowed_extensions and file_extension not in allowed_extensions:
            raise ValueError(
                f"Formato de archivo no permitido. Formatos permitidos: {', '.join(allowed_extensions)}"
            )

        # Validar tamaño del archivo (en bytes)
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.size > max_size_bytes:
            raise ValueError(f"El archivo excede el tamaño máximo permitido de {max_size_mb}MB")
        
        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{uuid.uuid4()}_{timestamp}{file_extension}"
        
        # Asegurar que el directorio termine con /
        if not directory.endswith('/'):
            directory += '/'
        
        # Nombre completo del archivo en Firebase Storage
        blob_path = f"{directory}{unique_filename}"
        
        # Subir el archivo
        blob = bucket.blob(blob_path)

        if isinstance(file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            file.open()
            file.seek(0)
            blob.upload_from_file(file.file, content_type=file.content_type)
        else:
            # fallback genérico
            file_bytes = file.read()
            blob.upload_from_string(file_bytes, content_type=getattr(file, "content_type", None))

        # Hacer el archivo público
        blob.make_public()
        return blob.public_url
        
    except Exception as e:
        raise Exception(f"Error al subir el archivo: {str(e)}")


def upload_invoice_file(file_data: bytes, invoice_number: str, reference_code: str, file_extension: str, content_type: str) -> str:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"factura_{invoice_number}_{reference_code}_{timestamp}.{file_extension}"
        
        blob_path = f"invoices/{filename}"
        blob = bucket.blob(blob_path)
        
        blob.upload_from_string(file_data, content_type=content_type)
        blob.make_public()
        
        return blob.public_url
        
    except Exception as e:
        raise Exception(f"Error al subir el archivo {file_extension.upper()} a Firebase: {str(e)}")


def upload_invoice_pdf(file_data: bytes, invoice_number: str, reference_code: str) -> str:
    return upload_invoice_file(file_data, invoice_number, reference_code, 'pdf', 'application/pdf')


def upload_invoice_files_pair(pdf_data: bytes, xml_data: bytes, invoice_number: str, reference_code: str) -> tuple:
    """
    Sube simultáneamente PDF y XML de una factura con el mismo nombre base.
    
    Args:
        pdf_data: Contenido del PDF en bytes
        xml_data: Contenido del XML en bytes
        invoice_number: Número de la factura
        reference_code: Código de referencia de la factura

    Returns:
        tuple: (pdf_url, xml_url)
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"factura_{invoice_number}_{reference_code}_{timestamp}"
        
        # Subir PDF
        pdf_filename = f"{base_name}.pdf"
        pdf_blob = bucket.blob(f"invoices/{pdf_filename}")
        pdf_blob.upload_from_string(pdf_data, content_type='application/pdf')
        pdf_blob.make_public()
        
        # Subir XML
        xml_filename = f"{base_name}.xml"
        xml_blob = bucket.blob(f"invoices/{xml_filename}")
        xml_blob.upload_from_string(xml_data, content_type='application/xml')
        xml_blob.make_public()
        
        return pdf_blob.public_url, xml_blob.public_url
        
    except Exception as e:
        raise Exception(f"Error al subir archivos de factura a Firebase: {str(e)}")

