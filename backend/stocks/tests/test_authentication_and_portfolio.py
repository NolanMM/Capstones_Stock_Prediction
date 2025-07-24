from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from stocks.models import PortfolioItem

class AuthenticationTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_user_registration(self):
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            're_password': 'newpass123'
        }
        response = self.client.post('/api/users/', new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new@example.com').exists())
    
    def test_user_login(self):
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post('/api/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.json())

    def test_login_invalid_credentials(self):
        login_data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_protected_endpoint_requires_auth(self):
        response = self.client.get('/api/account/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_authenticated_user_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/account/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['email'], self.user_data['email'])

class PortfolioTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='portfoliouser',
            email='portfolio@example.com',
            password='portfoliopass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_add_stock_to_portfolio(self):
        stock_data = {'stock_symbol': 'AAPL'}
        response = self.client.post('/api/portfolio/', stock_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PortfolioItem.objects.filter(user=self.user, stock_symbol='AAPL').exists())

    def test_add_duplicate_stock(self):
        PortfolioItem.objects.create(user=self.user, stock_symbol='MSFT')
        stock_data = {'stock_symbol': 'MSFT'}
        response = self.client.post('/api/portfolio/', stock_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already in your portfolio', response.json()['error'])

    def test_get_portfolio(self):
        PortfolioItem.objects.create(user=self.user, stock_symbol='AAPL')
        PortfolioItem.objects.create(user=self.user, stock_symbol='GOOGL')
        response = self.client.get('/api/portfolio/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_remove_stock_from_portfolio(self):
        PortfolioItem.objects.create(user=self.user, stock_symbol='TSLA')
        response = self.client.delete('/api/portfolio/TSLA/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PortfolioItem.objects.filter(user=self.user, stock_symbol='TSLA').exists())

class AccountTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='accountuser',
            email='account@example.com',
            password='accountpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_account_info(self):
        response = self.client.get('/api/account/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['username'], 'accountuser')
        self.assertEqual(data['email'], 'account@example.com')

    def test_update_email(self):
        update_data = {'email': 'newemail@example.com'}
        response = self.client.put('/api/account/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_update_password(self):
        new_password = 'newpassword123'
        update_data = {'password': new_password}
        response = self.client.put('/api/account/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_delete_account(self):
        user_id = self.user.id
        response = self.client.delete('/api/account/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user_id).exists())
