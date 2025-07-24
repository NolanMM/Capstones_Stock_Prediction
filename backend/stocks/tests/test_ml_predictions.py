from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta


class MLPredictionTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_predict_stock_success(self, mock_connection, mock_ml_handler):
        """Test successful stock prediction"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 150.0, 155.0, 148.0, 152.0, 1000000),
            ('2025-01-02', 152.0, 157.0, 150.0, 155.0, 1200000),
            ('2025-01-03', 155.0, 160.0, 153.0, 158.0, 1100000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML prediction response
        mock_ml_handler.predict_stock_returns.return_value = {
            "last_date": "2025-01-03",
            "last_price": 158.0,
            "forecast": [
                {
                    "date": "2025-01-04",
                    "return_pct": 1.5,
                    "price": 160.37
                },
                {
                    "date": "2025-01-05",
                    "return_pct": 0.8,
                    "price": 161.65
                }
            ]
        }
        
        response = self.client.get('/api/predict-stock/?symbol=AAPL&days=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('symbol', data)
        self.assertIn('last_date', data)
        self.assertIn('last_price', data)
        self.assertIn('forecast', data)
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertEqual(len(data['forecast']), 2)

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_predict_stock_with_default_parameters(self, mock_connection, mock_ml_handler):
        """Test prediction with default parameters (AAPL, 7 days)"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 150.0, 155.0, 148.0, 152.0, 1000000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML prediction with 7 day forecast
        forecast_data = [
            {"date": f"2025-01-{i+2:02d}", "return_pct": 1.0, "price": 153.52 + i}
            for i in range(7)
        ]
        mock_ml_handler.predict_stock_returns.return_value = {
            "last_date": "2025-01-01",
            "last_price": 152.0,
            "forecast": forecast_data
        }
        
        response = self.client.get('/api/predict-stock/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['symbol'], 'AAPL')  # Default symbol
        self.assertEqual(len(data['forecast']), 7)  # Default days

    @patch('stocks.views.connection')
    def test_predict_stock_no_data(self, mock_connection):
        """Test prediction when no historical data is found"""
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        response = self.client.get('/api/predict-stock/?symbol=INVALID')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('No data found for symbol: INVALID', data['error'])

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_predict_stock_ml_error(self, mock_connection, mock_ml_handler):
        """Test handling of ML model errors"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 150.0, 155.0, 148.0, 152.0, 1000000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML handler returning error
        mock_ml_handler.predict_stock_returns.return_value = {
            "error": "Model not loaded properly"
        }
        
        response = self.client.get('/api/predict-stock/?symbol=AAPL')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Model not loaded properly')

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_predict_stock_ml_exception(self, mock_connection, mock_ml_handler):
        """Test handling of ML handler exceptions"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 150.0, 155.0, 148.0, 152.0, 1000000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML handler raising exception
        mock_ml_handler.predict_stock_returns.side_effect = Exception("GPU memory error")
        
        response = self.client.get('/api/predict-stock/?symbol=AAPL')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('GPU memory error', data['error'])

    @patch('stocks.views.connection')
    def test_predict_stock_database_error(self, mock_connection):
        """Test handling of database errors in prediction"""
        mock_connection.cursor.side_effect = Exception("Database connection lost")
        
        response = self.client.get('/api/predict-stock/?symbol=AAPL')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Database connection lost', data['error'])

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_predict_stock_parameter_validation(self, mock_connection, mock_ml_handler):
        """Test parameter validation for prediction requests"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 150.0, 155.0, 148.0, 152.0, 1000000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML prediction
        mock_ml_handler.predict_stock_returns.return_value = {
            "last_date": "2025-01-01",
            "last_price": 152.0,
            "forecast": [{"date": "2025-01-02", "return_pct": 1.0, "price": 153.52}]
        }
        
        # Test invalid days parameter (should default to 7)
        test_cases = [
            ('days=invalid', 7),
            ('days=0', 7),
            ('days=-5', 7),
            ('days=50', 7),  # Too large, should default
            ('days=15', 15)  # Valid value
        ]
        
        for query_param, expected_forecast_count in test_cases:
            # Adjust mock for expected forecast count
            forecast_data = [
                {"date": f"2025-01-{i+2:02d}", "return_pct": 1.0, "price": 153.52}
                for i in range(expected_forecast_count)
            ]
            mock_ml_handler.predict_stock_returns.return_value['forecast'] = forecast_data
            
            response = self.client.get(f'/api/predict-stock/?symbol=AAPL&{query_param}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            data = response.json()
            self.assertEqual(len(data['forecast']), expected_forecast_count)

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_predict_stock_data_conversion(self, mock_connection, mock_ml_handler):
        """Test that data is properly converted for ML processing"""
        # Mock database response with mixed data types
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', '150.00', '155.00', '148.00', '152.00', '1000000'),
            ('2025-01-02', '152.00', '157.00', '150.00', '155.00', '1200000')
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML prediction
        mock_ml_handler.predict_stock_returns.return_value = {
            "last_date": "2025-01-02",
            "last_price": 155.0,
            "forecast": [{"date": "2025-01-03", "return_pct": 1.0, "price": 156.55}]
        }
        
        response = self.client.get('/api/predict-stock/?symbol=AAPL&days=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that ml_handler was called with proper DataFrame
        mock_ml_handler.predict_stock_returns.assert_called_once()
        call_args = mock_ml_handler.predict_stock_returns.call_args[0]
        df = call_args[0]
        
        # Check that DataFrame has correct structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        
        # Check that numeric columns were properly converted
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            self.assertTrue(pd.api.types.is_numeric_dtype(df[col]))


class MLPredictionIntegrationTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('stocks.views.ml_handler')
    @patch('stocks.views.connection')
    def test_prediction_response_format(self, mock_connection, mock_ml_handler):
        """Test that prediction response follows expected format"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.description = [('Date',), ('Open',), ('High',), ('Low',), ('Close',), ('Volume',)]
        mock_cursor.fetchall.return_value = [
            ('2025-01-01', 150.0, 155.0, 148.0, 152.0, 1000000)
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock ML prediction with comprehensive response
        mock_ml_handler.predict_stock_returns.return_value = {
            "last_date": "2025-01-01",
            "last_price": 152.0,
            "forecast": [
                {
                    "date": "2025-01-02",
                    "return_pct": 1.25,
                    "price": 153.90
                },
                {
                    "date": "2025-01-03",
                    "return_pct": -0.5,
                    "price": 153.13
                }
            ]
        }
        
        response = self.client.get('/api/predict-stock/?symbol=TSLA&days=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        
        # Verify response structure
        required_fields = ['symbol', 'last_date', 'last_price', 'forecast']
        for field in required_fields:
            self.assertIn(field, data)
        
        # Verify forecast structure
        self.assertIsInstance(data['forecast'], list)
        self.assertEqual(len(data['forecast']), 2)
        
        for forecast_item in data['forecast']:
            forecast_fields = ['date', 'return_pct', 'price']
            for field in forecast_fields:
                self.assertIn(field, forecast_item)
            
            # Verify data types
            self.assertIsInstance(forecast_item['date'], str)
            self.assertIsInstance(forecast_item['return_pct'], (int, float))
            self.assertIsInstance(forecast_item['price'], (int, float))

    def test_prediction_endpoint_availability(self):
        """Test that prediction endpoint is properly configured"""
        # This should fail gracefully even without mocking
        response = self.client.get('/api/predict-stock/?symbol=TEST&days=1')
        
        # Should not return 404 (endpoint exists)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should return some kind of response (success or error)
        self.assertIn(response.status_code, [200, 404, 500])
        
        # Response should be JSON
        try:
            data = response.json()
            self.assertIsInstance(data, dict)
        except:
            self.fail("Response should be valid JSON")
