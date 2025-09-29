"""
Tests para utilidades y funciones auxiliares
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from core.services.file_upload_service import upload_file_to_firebase
from config.firebase_config import firebase_initialized
import tempfile
import os

User = get_user_model()


class FileUploadServiceTests(TestCase):
    """Tests para el servicio de carga de archivos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_firebase_not_initialized_error(self):
        """Test para verificar que se lanza error cuando Firebase no está inicializado"""
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
    
    def test_file_validation(self):
        """Test para validación de archivos"""
        # Test con archivo válido
        valid_file = SimpleUploadedFile(
            "test.txt",
            b"test content",
            content_type="text/plain"
        )
        
        # Test con archivo de extensión no permitida
        invalid_extension_file = SimpleUploadedFile(
            "test.exe",
            b"test content",
            content_type="application/octet-stream"
        )
        
        # Test con archivo muy grande
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large.txt",
            large_content,
            content_type="text/plain"
        )
        
        # Verificar que se lanzan excepciones apropiadas
        with self.assertRaises(Exception) as context:
            upload_file_to_firebase(
                file=invalid_extension_file,
                directory='test/',
                allowed_extensions=['.txt'],
                max_size_mb=1
            )
        self.assertIn("Formato de archivo no permitido", str(context.exception))
        
        with self.assertRaises(Exception) as context:
            upload_file_to_firebase(
                file=large_file,
                directory='test/',
                allowed_extensions=['.txt'],
                max_size_mb=1
            )
        self.assertIn("excede el tamaño máximo", str(context.exception))


class FirebaseConfigTests(TestCase):
    """Tests para la configuración de Firebase"""
    
    def test_firebase_initialization_status(self):
        """Test para verificar el estado de inicialización de Firebase"""
        # Verificar que Firebase no está inicializado por defecto
        self.assertFalse(firebase_initialized)
    
    def test_firebase_configuration_handling(self):
        """Test para verificar el manejo de configuración de Firebase"""
        # Este test verificaría que la configuración de Firebase se maneja correctamente
        # cuando no está configurado
        pass


class ModelValidationTests(TestCase):
    """Tests para validación de modelos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_model_validation(self):
        """Test para validación del modelo de usuario"""
        # Test con datos válidos
        user = User(
            username='validuser',
            email='valid@example.com',
            password='validpass123'
        )
        user.full_clean()  # Esto debería no lanzar excepción
        
        # Test con email inválido
        user_invalid_email = User(
            username='invaliduser',
            email='invalid-email',
            password='validpass123'
        )
        
        with self.assertRaises(Exception):
            user_invalid_email.full_clean()
    
    def test_required_fields_validation(self):
        """Test para validación de campos requeridos"""
        # Test para usuario sin username
        user_no_username = User(
            email='test@example.com',
            password='testpass123'
        )
        
        with self.assertRaises(Exception):
            user_no_username.full_clean()
        
        # Test para usuario sin email
        user_no_email = User(
            username='testuser',
            password='testpass123'
        )
        
        with self.assertRaises(Exception):
            user_no_email.full_clean()


class UtilityFunctionsTests(TestCase):
    """Tests para funciones de utilidad"""
    
    def test_string_representations(self):
        """Test para representaciones string de modelos"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Verificar representación string
        self.assertEqual(str(user), 'testuser')
    
    def test_model_relationships(self):
        """Test para relaciones entre modelos"""
        from parameterization.models import Brands, Models
        
        brand = Brands.objects.create(
            name='Test Brand',
            description='Test Description'
        )
        
        model = Models.objects.create(
            name='Test Model',
            description='Test Model Description',
            id_brands=brand
        )
        
        # Verificar relación
        self.assertEqual(model.id_brands, brand)
        self.assertIn(model, brand.models_set.all())
    
    def test_model_defaults(self):
        """Test para valores por defecto de modelos"""
        from parameterization.models import Brands
        
        brand = Brands.objects.create(
            name='Test Brand'
        )
        
        # Verificar valores por defecto
        self.assertTrue(brand.is_active)
        self.assertEqual(brand.description, '')
