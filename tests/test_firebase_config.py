"""
Tests para verificar la configuración de Firebase
"""
from django.test import TestCase
from config.firebase_config import firebase_initialized, bucket


class FirebaseConfigTests(TestCase):
    """Tests para verificar la configuración de Firebase"""
    
    def test_firebase_not_initialized_in_development(self):
        """Test para verificar que Firebase no está inicializado en desarrollo"""
        # En el entorno de desarrollo sin credenciales reales,
        # Firebase no debería estar inicializado
        self.assertFalse(firebase_initialized)
        self.assertIsNone(bucket)
    
    def test_firebase_configuration_imports(self):
        """Test para verificar que la configuración de Firebase se puede importar"""
        # Si llegamos aquí, la configuración se importó correctamente
        self.assertTrue(True)


class FileUploadServiceTests(TestCase):
    """Tests para el servicio de carga de archivos"""
    
    def test_upload_service_handles_no_firebase(self):
        """Test para verificar que el servicio maneja la ausencia de Firebase"""
        from core.services.file_upload_service import upload_file_to_firebase
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Crear un archivo de prueba
        test_file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        
        # Verificar que se lanza excepción cuando Firebase no está configurado
        with self.assertRaises(Exception) as context:
            upload_file_to_firebase(
                file=test_file,
                directory='test/',
                allowed_extensions=['.txt'],
                max_size_mb=1
            )
        
        self.assertIn("Firebase no está configurado", str(context.exception))
