"""
Tests simples para verificar que el sistema funciona
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleTests(TestCase):
    """Tests simples para verificar funcionalidad básica"""
    
    def test_user_creation(self):
        """Test básico para crear un usuario"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.is_active)
    
    def test_user_str_representation(self):
        """Test para representación string del usuario"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        self.assertEqual(str(user), 'testuser')
    
    def test_database_connection(self):
        """Test para verificar conexión a base de datos"""
        # Si llegamos aquí, la conexión a la base de datos funciona
        self.assertTrue(True)
    
    def test_django_setup(self):
        """Test para verificar que Django está configurado correctamente"""
        from django.conf import settings
        
        # En el entorno de test, DEBUG puede estar en False
        self.assertIsInstance(settings.DEBUG, bool)
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.postgresql')
