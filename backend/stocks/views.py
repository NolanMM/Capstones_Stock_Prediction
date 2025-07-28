import os
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.http import JsonResponse
from django.db import connection
import pandas as pd
from rest_framework.response import Response
from django.core.cache import cache
from .services import email_services
from .models import StockPrice, PortfolioItem
from rest_framework import viewsets , status
import pyodbc
from datetime import datetime, timedelta
from . import ml_handler
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import CustomUserCreateSerializer, UserSerializer, PortfolioItemSerializer
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from .authentication import CsrfExemptSessionAuthentication
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
import json

# Legacy database connection test - TODO: Refactor in sprint 2
def test_connection(request):
    try:
        # Connect directly using pyodbc 
        conn = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};'
                             'Server=tcp:capstone-database-server.database.windows.net,1433;'
                             'Database=writedatabasesilverlayer;'
                             'Uid=capstonedioxieteam;'
                             'Pwd=Connhenbeo1@;'
                             'Encrypt=yes;'
                             'TrustServerCertificate=no;'
                             'Connection Timeout=30;')
        cursor = conn.cursor()
        cursor.execute('SELECT TOP 5 * FROM [Bronze].[Historical_Prices]')
        
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        conn.close()
        return JsonResponse({"stocks": results, "method": "direct_sql"})
    except Exception as e:
        return JsonResponse({"error": str(e)})
    
@api_view(['GET'])
def available_stocks(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT Stock_Symbol FROM [Bronze].[Historical_Prices]")
            symbols = [row[0] for row in cursor.fetchall()]  # Limit to 50
        return Response({"symbols": symbols})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def stock_history(request, symbol):
    days_str = request.GET.get('days', '30')
    try:
        days = int(days_str)
    except ValueError:
        days = 30
        
    try:
        with connection.cursor() as cursor:
            # This query now groups by Date to remove duplicates and correctly filters by a date range.
            # It aggregates the values for each day to ensure a single, smooth data point.
            
            base_query = """
                SELECT
                    [Date],
                    Stock_Symbol,
                    AVG(CAST([Open] AS float)) as [Open],
                    AVG(CAST([High] AS float)) as [High],
                    AVG(CAST([Low] AS float)) as [Low],
                    AVG(CAST([Close] AS float)) as [Close],
                    SUM(CAST([Volume] AS bigint)) as [Volume]
                FROM 
                    [Bronze].[Historical_Prices]
                WHERE 
                    Stock_Symbol = %s
            """
            
            params = [symbol]
            
            if days <= 30000: # A large number to signify "All time" is not used
                base_query += " AND [Date] >= DATEADD(day, -%s, GETDATE())"
                params.append(days)

            query = base_query + " GROUP BY [Date], Stock_Symbol ORDER BY [Date] ASC"
            
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return Response({
            "symbol": symbol,
            "history": history
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def predict_stock(request):
    """
    Endpoint to predict future stock prices for a given symbol.
    
    Parameters:
    - symbol: The stock symbol to predict (e.g., AAPL, MSFT)
    - days: Number of days to predict (default 5)
    
    Returns:
    - Prediction data including forecasted price and returns
    """
    try:
        import traceback  # For detailed error reporting
        
        # Get query parameters
        symbol = request.query_params.get('symbol', 'AAPL')
        horizon = request.query_params.get('days', 5)

        print(f"Attempting to predict {symbol} for {horizon} days")
        
        try:
            horizon = int(horizon)
            if horizon <= 0 or horizon > 30:
                horizon = 5  # Default to 5 days if invalid
        except ValueError:
            horizon = 5

        # with connection.cursor() as cursor:
        #     try:
        #         query = f"""
        #             SELECT [Date], [Open], [High], [Low], [Close], [Volume]
        #             FROM [Bronze].[Historical_Prices]
        #             WHERE [Stock_Symbol] = '{symbol}'
        #             ORDER BY [Date] DESC
        #         """
        #         cursor.execute(query)
        #     except Exception as e:
        #         print(f"Error executing query: {str(e)}")
        #         raise            
        #     columns = [column[0] for column in cursor.description]
        #     results = []
        #     for row in cursor.fetchall():
        #         results.append(dict(zip(columns, row)))
        
        # if not results:
        #     return Response({"error": f"No data found for symbol: {symbol}"}, status=404)
        
        # # Convert to DataFrame for processing
        # df = pd.DataFrame(results)
        
        # # Convert string columns to proper types
        # numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        # for col in numeric_cols:
        #     if col in df.columns:
        #         df[col] = pd.to_numeric(df[col])
        #     else:
        #         print(f"Warning: Column {col} not found in DataFrame")
        
        # # Sort by date in ascending order (oldest to newest)
        # df['Date'] = pd.to_datetime(df['Date'])
        # df = df.sort_values('Date')

        # print(f"DataFrame shape after processing: {df.shape}")
        
        # Call prediction function
        try:
            FMP_API_KEY = os.getenv('FMP_API_KEY', None)
            if not FMP_API_KEY:
                raise ValueError("FMP_API_KEY environment variable is not set.")
            prediction_result = ml_handler.predict_stock_returns(symbol, FMP_API_KEY)
            
            if "error" in prediction_result:
                print(f"Error from ml_handler: {prediction_result['error']}")
                return Response({"error": prediction_result["error"]}, status=500)
            
            # Add symbol to response
            prediction_result["symbol"] = symbol
            
            return Response(prediction_result)
        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error in ml_handler: {e}")
            print(f"Stack trace: {stack_trace}")
            return Response({"error": str(e), "stack_trace": stack_trace}, status=500)
    
    except Exception as e:
        stack_trace = traceback.format_exc()
        print(f"Error in predict_stock: {e}")
        print(f"Stack trace: {stack_trace}")
        return Response({"error": str(e), "stack_trace": stack_trace}, status=500)

class StockPriceViewSet(viewsets.ViewSet):
    def list(self, request):
        try:
            # Get query parameters
            symbol = request.query_params.get('symbol')
            
            # Build query
            query = "SELECT TOP 100 * FROM [Bronze].[Historical_Prices]"
            where_clauses = []
            
            if symbol:
                where_clauses.append(f"Stock_Symbol = '{symbol}'")
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            # Execute query
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            return Response(results)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# Needs refactoring. Will do next sprint 
@api_view(['GET'])
def chart_data(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TOP 100 Stock_Symbol, Date, Close 
                FROM [Bronze].[Historical_Prices]
                ORDER BY Date DESC
            """)
            columns = [col[0] for col in cursor.description]
            chart_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            symbols = {}
            for row in chart_data:
                symbol = row['Stok_Symbol']
                if symbol not in symbols:
                    symbols[symbol] = []
                symbols[symbol].append({
                    'date': row['Date'],
                    'price': float(row['Close'])
                })
                
        return JsonResponse(symbols)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
def stock_names(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT Stock_Symbol 
                FROM [Bronze].[Historical_Prices]
                ORDER BY Stock_Symbol
            """)
            stock_symbols = [row[0] for row in cursor.fetchall()]
            
        return JsonResponse({"symbols": stock_symbols})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Get stock symbols in format for marketPrediction.js
@api_view(['GET'])
def stock_names_json(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT Stock_Symbol FROM [Bronze].[Historical_Prices]")
            symbols = [{"name": row[0]} for row in cursor.fetchall()]
        
        return JsonResponse(symbols, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Get chart data in format for marketPrediction.js
@api_view(['GET'])
def chart_data_json(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TOP 30 Stock_Symbol, Date, Close 
                FROM [Bronze].[Historical_Prices]
                WHERE Stock_Symbol IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META')
                ORDER BY Date DESC
            """)
            rows = cursor.fetchall()
            
        symbols = set(row[0] for row in rows)
        dates = sorted(set(row[1] for row in rows))
        
        data = {
            "chart1": {
                "title": "Stock Price History",
                "labels": [str(date) for date in dates[-30:]],
                "datasets": []
            },
            "chart2": {
                "title": "Price Change Rate",
                "labels": [str(date) for date in dates[-30:]],
                "datasets": []
            },
            "barChart": {
                "title": "Price Comparison",
                "labels": list(symbols),
                "datasets": [{
                    "label": "Current Price",
                    "backgroundColor": "#007bff",
                    "data": []
                }]
            },
            "scatterChart": {
                "title": "Price vs Volume",
                "datasets": []
            }
        }
        
        for i, symbol in enumerate(symbols):
            color = ["#007bff", "#28a745", "#333333", "#c3e6cb", "#dc3545"][i % 5]
            
            symbol_data = [r for r in rows if r[0] == symbol]
            prices = [float(r[2]) for r in symbol_data]
            
            # Chart 1: Price history
            data["chart1"]["datasets"].append({
                "label": symbol,
                "backgroundColor": "transparent",
                "borderColor": color,
                "data": prices[-30:]
            })
            
            # Chart 2: Price change rate
            changes = [0] + [(prices[i] - prices[i-1])/prices[i-1]*100 for i in range(1, len(prices))]
            data["chart2"]["datasets"].append({
                "label": symbol,
                "backgroundColor": "transparent",
                "borderColor": color,
                "data": changes[-30:]
            })
            
            # Bar chart
            data["barChart"]["datasets"][0]["data"].append(prices[0] if prices else 0)
            
            # Scatter chart
            data["scatterChart"]["datasets"].append({
                "label": symbol,
                "borderColor": color,
                "backgroundColor": color,
                "data": [{"x": i, "y": price} for i, price in enumerate(prices[-30:])]
            })
            
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Get stock details in format for marketPrediction.js
@api_view(['GET'])
def stock_details_json(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT Stock_Symbol, Close
                FROM [Bronze].[Historical_Prices]
                WHERE Stock_Symbol IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META')
            """)
            stocks = []
            for row in cursor.fetchall():
                stocks.append({
                    "name": row[0],
                    "priceAtClose": str(row[1]),
                    "afterHoursPrice": str(float(row[1]) * 1.001),  
                    "priceToEarnings": "28.53",  
                    "priceToBook": "30.12"  
                })
        
        return JsonResponse(stocks, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Get news articles in format for marketPrediction.js
@api_view(['GET'])
def news_articles_json(request):
    data = [
        {
            "stock": "AAPL",
            "articles": [
                {
                    "title": "Apple Stocks Surge Amid Earnings Report",
                    "date": "2025-03-15",
                    "description": "Apple's stock price increased significantly following a strong quarterly earnings report.",
                    "link": "#"
                },
                {
                    "title": "New iPhone Launch Expected to Boost Apple Stock",
                    "date": "2025-03-10",
                    "description": "Analysts predict the upcoming iPhone launch will drive Apple's stock price higher.",
                    "link": "#"
                }
            ]
        },
        {
            "stock": "MSFT",
            "articles": [
                {
                    "title": "Microsoft Expands Cloud Services",
                    "date": "2025-03-18",
                    "description": "Microsoft announced expansion of their Azure cloud services platform.",
                    "link": "#"
                }
            ]
        }
    ]
    return JsonResponse(data, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class AccountDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        request.user.delete()
        return Response(status=204)

@method_decorator(csrf_exempt, name='dispatch')
class PortfolioListCreate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = PortfolioItem.objects.filter(user=request.user)
        serializer = PortfolioItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PortfolioItemSerializer(data=request.data)
        if serializer.is_valid():
            # Check if the item already exists
            if PortfolioItem.objects.filter(user=request.user, stock_symbol=serializer.validated_data['stock_symbol']).exists():
                return Response({'error': 'This stock is already in your portfolio.'}, status=400)
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class PortfolioDestroy(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, stock_symbol):
        try:
            item = PortfolioItem.objects.get(user=request.user, stock_symbol=stock_symbol)
            item.delete()
            return Response(status=204)
        except PortfolioItem.DoesNotExist:
            return Response({'error': 'Stock not found in portfolio.'}, status=404)

def account(request):
    return render(request, 'account.html')

def index(request):
    return render(request, 'index.html')

@csrf_exempt
@api_view(['POST'])
def custom_login(request):
    """Custom login endpoint that uses Django sessions instead of tokens"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Try to authenticate with username first, then email
        user = None
        if username:
            user = authenticate(request, username=username, password=password)
        
        if not user and email:
            # Try to find user by email and authenticate with their username
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def custom_logout(request):
    """Custom logout endpoint"""
    try:
        logout(request)
        return JsonResponse({'message': 'Logged out successfully'})
    except Exception as e:
        return JsonResponse({'message': 'Logged out'})  # Always return success for logout

def marketprediction(request):
    return render(request, 'marketprediction.html')

def portfolio(request):
    return render(request, 'portfolio.html')

def register(request):
    return render(request, 'register.html')

# Default handler 
def page_handler(request, page_name):
    try:
        return render(request, f'{page_name}.html')
    except Exception as e:
        print(f"Error loading {page_name}.html: {str(e)}")
        return redirect('index')

@api_view(['POST'])
@permission_classes([AllowAny])
def create_user(request):
    """
    Creates a new user account.
    Upon successful creation, the user is marked as inactive and a verification
    email with an OTP is sent.
    """
    serializer = CustomUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        # The serializer's create method now handles setting is_active=False
        user = serializer.save()
        
        # Generate and cache OTP
        otp = email_services.generate_random_key()
        # 1-hour expiry for OTP
        cache.set(f"otp_{user.email}", otp, timeout=3600)  

        # Send verification email
        email_sent = email_services.send_verification_email(request, user, otp)

        if email_sent:
            return Response(
                {"detail": "User created successfully. Please check your email to verify your account."},
                status=status.HTTP_201_CREATED
            )
        else:
            user.delete()
            return Response(
                {"error": "Failed to send verification email. Please try registering again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verifies the user's email with the provided OTP.
    """
    email = request.data.get('email')
    otp_provided = request.data.get('otp')

    if not email or not otp_provided:
        return Response({'error': 'Email and OTP are required.'}, status=status.HTTP_400_BAD_REQUEST)

    stored_otp = cache.get(f"otp_{email}")

    if not stored_otp:
        return Response({'error': 'OTP has expired or is invalid.'}, status=status.HTTP_400_BAD_REQUEST)

    if stored_otp == otp_provided:
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({'message': 'Account is already active.'}, status=status.HTTP_200_OK)
            
            user.is_active = True
            user.save()
            cache.delete(f"otp_{email}") # OTP has been used, so delete it
            return Response({'message': 'Email verified successfully! You can now log in.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def verify_email_page(request):
    return render(request, 'verifyemail.html')