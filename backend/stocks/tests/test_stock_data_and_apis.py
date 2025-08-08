from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.db import connection


class StockDataTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('stocks.views.connection')
    def test_available_stocks_endpoint(self, mock_connection):
        """Test getting list of available stock symbols"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('AAPL',), ('MSFT',), ('GOOGL',)]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/api/available-stocks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('symbols', data)
        self.assertEqual(len(data['symbols']), 3)
        self.assertIn('AAPL', data['symbols'])

    @patch('stocks.views.connection')
    def test_available_stocks_database_error(self, mock_connection):
        """Test handling of database errors in available stocks"""
        mock_connection.cursor.side_effect = Exception("Database error")
        
        response = self.client.get('/api/available-stocks/')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        data = response.json()
        self.assertIn('error', data)

    @patch('stocks.views.connection')
    def test_stock_history_endpoint(self, mock_connection):
        """Test getting historical data for specific stock"""
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Stock_Symbol',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 'AAPL', 150.00, 155.00, 148.00, 152.00, 1000000),
            ('2025-01-02', 'AAPL', 152.00, 157.00, 150.00, 155.00, 1200000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/api/stock-history/AAPL/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('history', data)
        self.assertIn('symbol', data)
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertEqual(len(data['history']), 2)

    @patch('stocks.views.connection')
    def test_stock_history_invalid_symbol(self, mock_connection):
        """Test stock history with invalid symbol"""
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Stock_Symbol',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/api/stock-history/INVALID/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data['history']), 0)
        self.assertEqual(data['symbol'], 'INVALID')

    @patch('stocks.views.connection')
    def test_stock_history_database_error(self, mock_connection):
        """Test handling of database errors in stock history"""
        mock_connection.cursor.side_effect = Exception("Database connection failed")
        
        response = self.client.get('/api/stock-history/AAPL/')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        data = response.json()
        self.assertIn('error', data)


class FrontendAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('stocks.views.connection')
    def test_stock_names_json_endpoint(self, mock_connection):
        """Test stock names JSON endpoint for frontend"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('AAPL',), ('MSFT',), ('GOOGL',)]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/json/stocknames.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['name'], 'AAPL')

    @patch('stocks.views.connection')
    def test_chart_data_json_endpoint(self, mock_connection):
        """Test chart data JSON endpoint for frontend"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('AAPL', '2025-01-01', '150.00'),
            ('AAPL', '2025-01-02', '152.00'),
            ('MSFT', '2025-01-01', '300.00')
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/json/chartdata.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('chart1', data)
        self.assertIn('chart2', data)
        self.assertIn('barChart', data)
        self.assertIn('scatterChart', data)
        
        # Check chart1 structure
        self.assertIn('title', data['chart1'])
        self.assertIn('datasets', data['chart1'])
        self.assertIsInstance(data['chart1']['datasets'], list)

    @patch('stocks.views.connection')
    def test_stock_details_json_endpoint(self, mock_connection):
        """Test stock details JSON endpoint for frontend"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ('AAPL', '150.00'),
            ('MSFT', '300.00'),
            ('GOOGL', '2500.00')
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/json/stockdetails.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_news_articles_json_endpoint(self):
        """Test news articles JSON endpoint for frontend"""
        response = self.client.get('/json/newsarticles.json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIsInstance(data, list)
        # Should have hardcoded test data
        self.assertTrue(len(data) > 0)
        
        # Check structure of first article
        if data:
            first_stock = data[0]
            self.assertIn('stock', first_stock)
            self.assertIn('articles', first_stock)
            self.assertIsInstance(first_stock['articles'], list)

    @patch('stocks.views.connection')
    def test_frontend_api_database_errors(self, mock_connection):
        """Test frontend APIs handle database errors gracefully"""
        mock_connection.cursor.side_effect = Exception("Database unavailable")
        
        endpoints = [
            '/json/stocknames.json',
            '/json/chartdata.json', 
            '/json/stockdetails.json'
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            data = response.json()
            self.assertIn('error', data)


class LegacyEndpointTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('stocks.views.pyodbc')
    def test_connection_endpoint_success(self, mock_pyodbc):
        """Test legacy database connection test endpoint"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('col1',), ('col2',)]
        mock_cursor.fetchall.return_value = [('value1', 'value2')]
        mock_conn.cursor.return_value = mock_cursor
        mock_pyodbc.connect.return_value = mock_conn
        
        response = self.client.get('/api/test-connection/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('stocks', data)
        self.assertIn('method', data)
        self.assertEqual(data['method'], 'direct_sql')

    @patch('stocks.views.pyodbc')
    def test_connection_endpoint_failure(self, mock_pyodbc):
        """Test legacy database connection test endpoint failure"""
        mock_pyodbc.connect.side_effect = Exception("Connection failed")
        
        response = self.client.get('/api/test-connection/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('error', data)


class StockDataIntegrationTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_stock_data_endpoints_consistency(self):
        """Test that stock data endpoints return consistent data structures"""
        with patch('stocks.views.connection') as mock_connection:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [('AAPL',), ('MSFT',)]
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Test available stocks
            response1 = self.client.get('/api/available-stocks/')
            self.assertEqual(response1.status_code, status.HTTP_200_OK)
            
            # Test stock names JSON (should have similar data)
            response2 = self.client.get('/json/stocknames.json')
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            
            # Both should return data about stocks
            data1 = response1.json()
            data2 = response2.json()
            
            self.assertIn('symbols', data1)
            self.assertIsInstance(data2, list)

    def test_error_response_format_consistency(self):
        """Test that all endpoints return consistent error formats"""
        with patch('stocks.views.connection') as mock_connection:
            mock_connection.cursor.side_effect = Exception("Test error")
            
            endpoints = [
                '/api/available-stocks/',
                '/api/stock-history/AAPL/',
                '/json/stocknames.json',
                '/json/chartdata.json',
                '/json/stockdetails.json'
            ]
            
            for endpoint in endpoints:
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
                data = response.json()
                self.assertIn('error', data)
                self.assertIsInstance(data['error'], str)
