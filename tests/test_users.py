"""
Tests para el módulo de usuarios
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import User

User = get_user_model()


class UserModelTests(TestCase):
    """Tests para el modelo de usuario"""
    
    def test_user_creation(self):
        """Test para crear un usuario"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_superuser_creation(self):
        """Test para crear un superusuario"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.assertEqual(superuser.username, 'admin')
        self.assertEqual(superuser.email, 'admin@example.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_user_str_representation(self):
        """Test para la representación string del usuario"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        self.assertEqual(str(user), 'testuser')
    
    def test_user_id_user_field(self):
        """Test para el campo id_user personalizado"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            id_user='USR001'
        )
        
        self.assertEqual(user.id_user, 'USR001')


class UserAPITests(APITestCase):
    """Tests para la API de usuarios"""
    
    def setUp(self):
        """Configuración inicial para los tests de API"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_list_api(self):
        """Test para listar usuarios via API"""
        url = reverse('user-list')
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_creation_api(self):
        """Test para crear usuario via API"""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
        }
        
        response = self.client.post(url, data)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_detail_api(self):
        """Test para obtener detalles de usuario via API"""
        url = reverse('user-detail', kwargs={'pk': self.user.pk})
        response = self.client.get(url)
        
        # Debería requerir autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAuthenticationTests(TestCase):
    """Tests para la autenticación de usuarios"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_login(self):
        """Test para el login de usuario"""
        from django.contrib.auth import authenticate
        
        # Autenticación exitosa
        authenticated_user = authenticate(
            username='testuser',
            password='testpass123'
        )
        
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user, self.user)
    
    def test_user_login_wrong_password(self):
        """Test para login con contraseña incorrecta"""
        from django.contrib.auth import authenticate
        
        authenticated_user = authenticate(
            username='testuser',
            password='wrongpassword'
        )
        
        self.assertIsNone(authenticated_user)
    
    def test_user_login_wrong_username(self):
        """Test para login con usuario incorrecto"""
        from django.contrib.auth import authenticate
        
        authenticated_user = authenticate(
            username='wronguser',
            password='testpass123'
        )
        
        self.assertIsNone(authenticated_user)
