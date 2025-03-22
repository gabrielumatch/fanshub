from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages
from accounts.models import UserProfile

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_register_page_loads(self):
        """Test that the registration page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_success(self):
        """Test successful user registration"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'bio': 'Test bio'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful registration
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('newpass123'))
        
        # Verify profile was created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.bio, 'Test bio')

    def test_register_duplicate_username(self):
        """Test registration with duplicate username"""
        data = {
            'username': 'testuser',  # Already exists
            'email': 'another@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'A user with that username already exists.')

    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'pass123',
            'password2': 'differentpass'  # Different from password1
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', "The two password fields didn't match.")

    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password1': 'pass123',
            'password2': 'pass123'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'Enter a valid email address.')

    def test_login_page_loads(self):
        """Test that the login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_success(self):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful login
        
        # Verify user is logged in
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertContains(response, 'Please enter a correct username and password.')

    def test_logout(self):
        """Test user logout"""
        # First login the user
        self.client.login(username='testuser', password='testpass123')
        self.assertTrue('_auth_user_id' in self.client.session)
        
        # Then logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Should redirect after logout
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_profile_creation(self):
        """Test that user profile is created on registration"""
        data = {
            'username': 'profileuser',
            'email': 'profile@example.com',
            'password1': 'pass123',
            'password2': 'pass123',
            'bio': 'Test profile bio'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username='profileuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.bio, 'Test profile bio')

    def test_profile_picture_upload(self):
        """Test profile picture upload during registration"""
        # Create a test image
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',  # Add some image bytes in a real test
            content_type='image/jpeg'
        )
        
        data = {
            'username': 'pictureuser',
            'email': 'picture@example.com',
            'password1': 'pass123',
            'password2': 'pass123',
            'profile_picture': image
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username='pictureuser')
        self.assertTrue(user.profile.profile_picture)

    def test_required_fields(self):
        """Test registration with missing required fields"""
        data = {
            'username': '',  # Missing username
            'email': 'test@example.com',
            'password1': 'pass123',
            'password2': 'pass123'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

    def test_password_validation(self):
        """Test password validation rules"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': '123',  # Too short
            'password2': '123'
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password1', 'This password is too short. It must contain at least 8 characters.') 