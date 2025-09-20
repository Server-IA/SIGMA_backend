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
