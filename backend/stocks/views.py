from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.db import connection
from rest_framework.response import Response
from .models import StockPrice
from rest_framework import viewsets
import pyodbc

# Endpoints are not ready yet. 
# I shall refactor the code during sprint 2. 
# These endpoints contain a lot of shitty testing code. 

# Create your views here.
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
            symbols = [row[0] for row in cursor.fetchall()[:50]]  # Limit to 50
        return Response({"symbols": symbols})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def stock_history(request, symbol):
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30
        
    try:
        # Fix SQL parameter syntax for SQL Server
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT TOP {} Date, Close, Open, High, Low, Volume "
                "FROM [Bronze].[Historical_Prices] "
                "WHERE Stock_Symbol = '{}' "
                "ORDER BY Date DESC".format(days, symbol)
            )
            
            columns = [col[0] for col in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return Response({
            "symbol": symbol,
            "history": history
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

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

# THIS IS FOR TESTING PURPOSES ONLY
# stock names in the format according to marketPrediction.js
@api_view(['GET'])
def stock_names_json(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT Stock_Symbol FROM [Bronze].[Historical_Prices]")
            symbols = [{"name": row[0]} for row in cursor.fetchall()]
        
        return JsonResponse(symbols, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# THIS IS FOR TESTING PURPOSES ONLY
# chart data in the format according to marketPrediction.js
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

# THIS IS FOR TESTING PURPOSES ONLY
# stock details in the format according to marketPrediction.js
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

# THIS IS FOR TESTING PURPOSES ONLY
# news articles in the format according to marketPrediction.js
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

def account(request):
    return render(request, 'account.html')

def index(request):
    return render(request, 'index.html')

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