from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.db import connection
from rest_framework.response import Response
from .models import StockPrice
from rest_framework import viewsets
import pyodbc

# Add these imports at the top of your file
import pandas as pd
import numpy as np
import joblib
import os
import tempfile

# Define the LSTMModel class to match what was used when creating the model
class LSTMModel:
    """
    LSTM model class for stock prediction.
    This class needs to match the structure of the original class used to create the model.
    """
    def __init__(self):
        self.model = None
    
    def predict(self, data):
        # This is a placeholder - the actual implementation will be loaded from the pickle file
        pass

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
        cursor.execute('SELECT TOP 5 * FROM StockPriceSilverData_Table')
        
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
            cursor.execute("SELECT DISTINCT Symbol FROM StockPriceSilverData_Table")
            symbols = [row[0] for row in cursor.fetchall()[:50]]  # Limit to 50
        return Response({"symbols": symbols})
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
def market_indices(request):
    indices = StockPrice.objects.values_list('Market_Index', flat=True).distinct()
    return Response({"indices": list(indices)})

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
                "SELECT TOP {} Date, Close_Prices, Open_Prices, High_Prices, Low_Prices, Volume "
                "FROM StockPriceSilverData_Table "
                "WHERE Symbol = '{}' "
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
            market = request.query_params.get('market')
            
            # Build query
            query = "SELECT TOP 100 * FROM StockPriceSilverData_Table"
            where_clauses = []
            
            if symbol:
                where_clauses.append(f"Symbol = '{symbol}'")
            if market:
                where_clauses.append(f"Market_Index = '{market}'")
                
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
                SELECT TOP 100 Symbol, Date, Close_Prices 
                FROM StockPriceSilverData_Table
                ORDER BY Date DESC
            """)
            columns = [col[0] for col in cursor.description]
            chart_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            symbols = {}
            for row in chart_data:
                symbol = row['Symbol']
                if symbol not in symbols:
                    symbols[symbol] = []
                symbols[symbol].append({
                    'date': row['Date'],
                    'price': float(row['Close_Prices'])
                })
                
        return JsonResponse(symbols)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(['GET'])
def stock_names(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT Symbol 
                FROM StockPriceSilverData_Table
                ORDER BY Symbol
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
            cursor.execute("SELECT DISTINCT Symbol FROM StockPriceSilverData_Table")
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
            # Fetch all required columns for the model
            cursor.execute("""
                SELECT TOP 30 Symbol, Date, Close_Prices, High_Prices, Low_Prices, Open_Prices, Volume 
                FROM StockPriceSilverData_Table
                WHERE Symbol IN ('AAPL')
                ORDER BY Date DESC
            """)
            rows = cursor.fetchall()
            
        # Get the directory of the current file and locate the model
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lstm_model.pkl")

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
        
        # Load model and make predictions
        try:
            # Make sure sys.modules['__main__'] can find the LSTMModel class
            import sys
            sys.modules['__main__'].__dict__['LSTMModel'] = LSTMModel
            
            # Load the model
            lstm_model = joblib.load(model_path)
            
            # Create DataFrame from query results with all required columns
            columns = ['Symbol', 'Date', 'Close_Prices', 'High_Prices', 'Low_Prices', 'Open_Prices', 'Volume']
            df = pd.DataFrame(rows, columns=columns)
            
            # Convert numeric columns to float
            for col in ['Close_Prices', 'High_Prices', 'Low_Prices', 'Open_Prices', 'Volume']:
                df[col] = df[col].astype(float)
            
            # Sort by date ascending (oldest first) for proper sequence
            df = df.sort_values('Date')
            
            # Create a temporary CSV file with the required format
            temp_csv_path = os.path.join(tempfile.gettempdir(), 'stock_data_for_model.csv')
            df.to_csv(temp_csv_path, index=False)
            
            # Print debug info
            print(f"Temporary CSV created at: {temp_csv_path}")
            print(f"CSV file exists: {os.path.exists(temp_csv_path)}")
            
            # Load model and make prediction using the CSV file
            y_pred = lstm_model.predict(temp_csv_path)
            
            # Print prediction info for debugging
            print(f"Prediction type: {type(y_pred)}")
            print(f"Prediction value: {y_pred}")
            
            # Clean up the temporary file
            if os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
            
            # Handle various prediction return types
            if y_pred is None:
                # Model returned None - create fallback predictions
                print("Model returned None, generating fallback predictions")
                
                # Get the last few closing prices and dates
                prices_array = np.array([float(r[2]) for r in rows if r[0] == list(symbols)[0]])
                dates_array = np.array([r[1] for r in rows if r[0] == list(symbols)[0]])
                
                # Sort dates in ascending order (oldest first)
                sorted_indices = np.argsort(dates_array)
                dates_array = dates_array[sorted_indices]
                prices_array = prices_array[sorted_indices]
                
                # Create a simple linear regression for fallback prediction
                # First, generate x values as indices
                x = np.arange(len(prices_array)).reshape(-1, 1)
                y = prices_array
                
                # Fit simple linear regression
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(x, y)
                
                # Generate FUTURE dates for predictions (30 days into the future)
                latest_date = max(dates_array)
                from datetime import datetime, timedelta
                
                # Parse the latest date string and generate future dates
                if isinstance(latest_date, str):
                    latest_date = datetime.strptime(latest_date, "%Y-%m-%d")
                
                future_dates = []
                future_predictions = []
                for i in range(1, 31):  # Predict 30 days into the future
                    future_date = latest_date + timedelta(days=i)
                    future_dates.append(future_date.strftime("%Y-%m-%d"))
                    
                    # Predict for this future date
                    future_x = np.array([[len(prices_array) + i - 1]])  # Continue from end of historical data
                    prediction = model.predict(future_x)[0]
                    future_predictions.append(prediction)
                
                # Create separate datasets for historical and prediction data
                # Historical data is already handled in the earlier code
                
                # Update chart labels to include future dates
                all_dates = list(data["chart1"]["labels"]) + future_dates
                data["chart1"]["labels"] = all_dates
                
                # Create arrays of the right length with nulls for missing values
                historical_length = len(data["chart1"]["labels"]) - len(future_dates)
                future_length = len(future_dates)
                
                # Create null-padded arrays for visualization
                # Historical data gets nulls for future dates
                for dataset in data["chart1"]["datasets"]:
                    # Extend existing datasets with nulls for future dates
                    dataset["data"].extend([None] * future_length)
                
                # Predictions get nulls for historical dates and values for future dates
                prediction_data = [None] * historical_length + future_predictions
                
                # Add predictions to chart1 data as a separate line
                prediction_color = "#dc3545"  # Red color for predictions
                data["chart1"]["datasets"].append({
                    "label": "Future Predictions",
                    "backgroundColor": "transparent",
                    "borderColor": prediction_color,
                    "data": prediction_data,
                    "borderDash": [5, 5],  # Add dashed line for predictions
                    "pointStyle": "triangle"  # Use different point style for predictions
                })
                
                # Print success message
                print("Added future date predictions based on linear regression")
                
            elif isinstance(y_pred, (int, float, np.number)):
                # If the model returns a single prediction value
                print("Model returned a scalar prediction")
                prediction_value = float(y_pred)
                
                # Create an array of predictions - using the same value or with slight variations
                # Get the last closing price to use as a baseline
                last_price = prices[0] if prices else 0
                
                # Create an array with the predicted value and some interpolated points
                # between the last known price and the prediction
                num_points = len(dates)
                pred_array = np.linspace(last_price, prediction_value, num_points)
                
                # Add predictions to chart1 data
                prediction_color = "#dc3545"  # Red color for predictions
                data["chart1"]["datasets"].append({
                    "label": "Predictions",
                    "backgroundColor": "transparent",
                    "borderColor": prediction_color,
                    "data": pred_array.tolist(),
                    "borderDash": [5, 5]  # Add dashed line for predictions
                })
            
            elif isinstance(y_pred, np.ndarray) and y_pred.ndim == 0:
                # Handle 0-dimensional numpy array (scalar)
                print("Model returned a 0-dimensional array")
                prediction_value = float(y_pred)
                
                # Create an array with slight variations for visualization
                num_points = len(dates)
                last_price = prices[0] if prices else 0
                pred_array = np.linspace(last_price, prediction_value, num_points)
                
                # Add predictions to chart1 data
                prediction_color = "#dc3545"  # Red color for predictions
                data["chart1"]["datasets"].append({
                    "label": "Predictions",
                    "backgroundColor": "transparent",
                    "borderColor": prediction_color,
                    "data": pred_array.tolist(),
                    "borderDash": [5, 5]  # Add dashed line for predictions
                })
                
            elif hasattr(y_pred, '__len__'):
                # For array-like predictions that have a length
                print(f"Model returned an array or list with length: {len(y_pred)}")
                
                # Check if it has a shape attribute (like numpy arrays)
                if hasattr(y_pred, 'shape'):
                    print(f"With shape: {y_pred.shape}")
                
                # Safely handle sequence reversal
                if len(y_pred) > 1:
                    y_pred_reversed = y_pred[::-1]
                else:
                    y_pred_reversed = y_pred
                
                # Convert to list safely
                if hasattr(y_pred_reversed, 'tolist'):
                    pred_data = y_pred_reversed.tolist()
                else:
                    pred_data = list(y_pred_reversed)
                
                # Trim if necessary
                if len(pred_data) > 30:
                    pred_data = pred_data[-30:]
                
                # Add predictions to chart1 data
                prediction_color = "#dc3545"  # Red color for predictions
                data["chart1"]["datasets"].append({
                    "label": "Predictions",
                    "backgroundColor": "transparent",
                    "borderColor": prediction_color,
                    "data": pred_data,
                    "borderDash": [5, 5]  # Add dashed line for predictions
                })
            
            else:
                # For any other return type we can't handle
                print(f"Model returned an unsupported type: {type(y_pred)}")
            
            # Print success message
            print("Successfully processed model output")
            
        except Exception as e:
            print(f"Error loading or using the LSTM model: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Generate fallback predictions even when there's an exception
            print("Generating fallback predictions due to model error")
            try:
                # Get the last few closing prices
                prices_array = np.array([float(r[2]) for r in rows if r[0] == list(symbols)[0]])
                
                # Create a simple linear regression for fallback prediction
                x = np.arange(len(prices_array)).reshape(-1, 1)
                y = prices_array
                
                # Fit simple linear regression
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(x, y)
                
                # Generate future indices for prediction
                future_x = np.arange(len(prices_array), len(prices_array) + 10).reshape(-1, 1)
                
                # Make predictions
                future_predictions = model.predict(future_x)
                
                # Create a smooth transition between actual and predictions
                combined_predictions = np.append(prices_array, future_predictions)
                
                # Add predictions to chart1 data
                prediction_color = "#dc3545"  # Red color for predictions
                data["chart1"]["datasets"].append({
                    "label": "Fallback Predictions",
                    "backgroundColor": "transparent",
                    "borderColor": prediction_color,
                    "data": combined_predictions.tolist(),
                    "borderDash": [5, 5]  # Add dashed line for predictions
                })
                
                print("Successfully added fallback predictions")
            except Exception as fallback_error:
                print(f"Error generating fallback predictions: {str(fallback_error)}")
            
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# THIS IS FOR TESTING PURPOSES ONLY
# stock details in the format according to marketPrediction.js
@api_view(['GET'])
def stock_details_json(request):
    try:
        with connection.cursor() as cursor:
            query = """
                WITH LatestStock AS (
                    SELECT
                        Symbol,
                        Close_Prices,
                        Open_Prices,
                        High_Prices,
                        Low_Prices,
                        ROW_NUMBER() OVER (PARTITION BY Symbol ORDER BY Date DESC) AS rn
                    FROM StockPriceSilverData_Table
                ),
                LatestFS AS (
                    SELECT
                        Symbol,
                        peRatio,
                        tangibleBookValuePerShare,
                        ROW_NUMBER() OVER (PARTITION BY Symbol ORDER BY Date DESC) AS rn
                    FROM Financial_Statement_Historical_Dimensional_Table
                )
                SELECT 
                    LS.Symbol,
                    LS.Close_Prices,
                    LS.Open_Prices,
                    LS.High_Prices,
                    LS.Low_Prices,
                    FS.peRatio,
                    FS.tangibleBookValuePerShare
                FROM LatestStock LS
                LEFT JOIN LatestFS FS ON LS.Symbol = FS.Symbol AND FS.rn = 1
                WHERE LS.rn = 1
            """
            cursor.execute(query)
            stocks = []
            for row in cursor.fetchall():
                symbol = row[0]
                try:
                    close_price = float(row[1])
                except (ValueError, TypeError):
                    close_price = 0.0
                try:
                    open_price = float(row[2])
                except (ValueError, TypeError):
                    open_price = 0.0
                try:
                    high_price = float(row[3])
                except (ValueError, TypeError):
                    high_price = 0.0
                try:
                    low_price = float(row[4])
                except (ValueError, TypeError):
                    low_price = 0.0
                try:
                    pe_ratio = float(row[5]) if row[5] is not None else 0.0
                except (ValueError, TypeError):
                    pe_ratio = 0.0
                try:
                    tangible_book = float(row[6]) if row[6] is not None else 0.0
                except (ValueError, TypeError):
                    tangible_book = 0.0

                stocks.append({
                    "name": symbol,
                    "currentPrice": f"{close_price:.2f}",
                    "priceAtClose": f"{close_price:.2f}",
                    "afterHoursPrice": f"{open_price:.2f}",
                    "priceToEarnings": f"{pe_ratio:.2f}",
                    "priceToBook": f"{tangible_book:.2f}"
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