from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


class RegisterTests(APITestCase):
    url = '/api/auth/register/'

    def test_register_success(self):
        data = {'username': 'pookii', 'email': 'pookii@example.com', 'password': 'StrongPass123!', 'password2': 'StrongPass123!'}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='pookii').exists())

    def test_register_password_mismatch(self):
        data = {'username': 'pookii', 'email': 'pookii@example.com', 'password': 'StrongPass123!', 'password2': 'WrongPass123!'}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username='pookii', password='pass', email='a@b.com')
        data = {'username': 'pookii', 'email': 'other@example.com', 'password': 'StrongPass123!', 'password2': 'StrongPass123!'}
        res = self.client.post(self.url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pookii', password='StrongPass123!', email='p@example.com')

    def test_login_success(self):
        res = self.client.post('/api/auth/login/', {'username': 'pookii', 'password': 'StrongPass123!'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_login_wrong_password(self):
        res = self.client.post('/api/auth/login/', {'username': 'pookii', 'password': 'wrongpassword'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class MeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='pookii', password='StrongPass123!', email='p@example.com')
        login = self.client.post('/api/auth/login/', {'username': 'pookii', 'password': 'StrongPass123!'})
        self.token = login.data['access']

    def test_me_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'pookii')

    def test_me_unauthenticated(self):
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
