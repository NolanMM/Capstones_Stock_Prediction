import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta

# This file handles the machine learning model for stock prediction.
# It defines the LSTM model, loads the pre-trained weights, and provides functions to compute technical indicators,
# prepare data, and make predictions.

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Absolute path to the model file
MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(BASE_DIR), 'currentModels', 'lstm_best.pth'))

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Define the LSTM model
class LSTMModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout=0.5):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                            dropout=dropout, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        h0 = torch.zeros(self.lstm.num_layers, x.size(0),
                         self.lstm.hidden_size, device=x.device)
        c0 = torch.zeros_like(h0)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :]).squeeze(-1)  # output last time step

# Load model on module import (only once when Django starts)
model = None
feature_cols = None
window_size = None

# Load model on module import
try:
    if os.path.exists(MODEL_PATH):
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        
        # Extract model parameters from checkpoint
        feature_cols = checkpoint["feature_order"]
        hidden_dim = checkpoint["hidden_dim"]
        num_layers = checkpoint["num_layers"]
        window_size = checkpoint["window"]
        
        # Initialize and load model
        model = LSTMModel(
            input_dim=len(feature_cols),
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            dropout=0.5
        ).to(device)
        
        model.load_state_dict(checkpoint["model_state"])
        model.eval()
        
except Exception as e:
    print(f"Error loading ML model: {str(e)}")


def compute_indicators(df):
    """Compute technical indicators matching the Walk-Forward model training"""
    df = df.copy()
    
    # RSI calculation (14-period)
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    roll_up = gain.ewm(span=14).mean()
    roll_down = loss.ewm(span=14).mean()
    rs = roll_up / roll_down
    df["RSI"] = 100 - 100 / (1 + rs)

    # MACD calculation
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    df["MACD"] = macd
    df["MACD_Signal"] = signal
    df["MACD_Hist"] = macd - signal

    # Bollinger Bands (20-period)
    sma = df["Close"].rolling(20).mean()
    std = df["Close"].rolling(20).std()
    df["BB_Mid"] = sma
    df["BB_Upper"] = sma + 2*std
    df["BB_Lower"] = sma - 2*std

    # Returns and volatility
    df["Return_3D"] = df["Close"].pct_change(periods=3).shift(-3)  # 3-day return
    df["Volatility_3D"] = df["Close"].pct_change().rolling(window=3).std()  # 3-day volatility
    
    # For lag1_ret, use the actual previous day's return (not the target)
    df["lag1_ret"] = df["Close"].pct_change().shift(1)  # Previous day's actual return
    
    # Create Return_1D as target (this will be NaN for the last row, which is expected)
    df["Return_1D"] = df["Close"].pct_change().shift(-1)  # Next day's return (target)
    
    # For prediction purposes, we need to preserve the last row even if Return_1D is NaN
    # Save info about the last row before dropping NaNs
    last_date = df.index[-1]
    last_row_data = df.iloc[-1].copy()
    
    # Drop NaN values (this will remove the last row because Return_1D is NaN)
    df.dropna(inplace=True)
    
    # Add back the last row for prediction, filling Return_1D with 0 (dummy value)
    if last_date not in df.index:
        last_row_data["Return_1D"] = 0  # Dummy value for target
        # Ensure all other values are not NaN
        for col in last_row_data.index:
            if pd.isna(last_row_data[col]) and col != "Return_1D":
                if len(df) > 0:
                    last_row_data[col] = df[col].iloc[-1]  # Use previous value
                else:
                    last_row_data[col] = 0
        
        # Add the row back
        df.loc[last_date] = last_row_data
        df = df.sort_index()
    
    return df


def prepare_quarterly(df, feats, tgt, window):
    """Scale data quarterly for better normalization"""
    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        date_col = 'date' if 'date' in df.columns else 'Date' if 'Date' in df.columns else None
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col)
        else:
            raise ValueError("DataFrame index is not DatetimeIndex and no 'date' or 'Date' column found.")

    if df.empty:
        raise ValueError("DataFrame is empty, cannot scale data")
    
    # Ensure all required columns exist
    all_cols = feats + [tgt]
    missing_cols = [col for col in all_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Check if we have enough data to scale properly
    if len(df) < window:
        # Fall back to using all available data with a single scaler
        m = MinMaxScaler()
        data_to_scale = df[feats + [tgt]].fillna(0)
        arr = m.fit_transform(data_to_scale.values)
        df_s = pd.DataFrame(arr, index=df.index, columns=feats+[tgt])
        return {str(df.index[0].to_period("Q")): m}, df_s
    
    df2 = df.copy()
    df2["Quarter"] = df2.index.to_period("Q")
    
    scalers, chunks = {}, []
    for q, g in df2.groupby("Quarter"):
        if len(g) < window:
            continue
            
        m = MinMaxScaler()
        arr = m.fit_transform(g[feats + [tgt]].values)
        chunks.append(pd.DataFrame(arr, index=g.index, columns=feats+[tgt]))
        scalers[str(q)] = m
    
    if not chunks:
        # If no quarter has enough data, use all data with a single scaler
        m = MinMaxScaler()
        arr = m.fit_transform(df[feats + [tgt]].values)
        df_s = pd.DataFrame(arr, index=df.index, columns=feats+[tgt])
        return {str(df.index[0].to_period("Q")): m}, df_s
        
    df_s = pd.concat(chunks).sort_index().dropna()
    return scalers, df_s


def build_last_window(df_scaled, feats, window):
    """Build the latest window for prediction"""
    data = df_scaled[feats].values
    return data[-window:]


def forecast_future_scaled(net, window_scaled, horizon):
    """Generate future predictions in scaled space"""
    arr, preds = window_scaled.copy(), []
    
    for _ in range(horizon):
        inp = torch.tensor(arr).float().unsqueeze(0).to(device)
        with torch.no_grad():
            p = net(inp).item()
        preds.append(p)
        
        # Roll the window - create new row based on last row
        # The prediction p represents the next day's return
        new_row = arr[-1].copy()
        # For lag1_ret (index 0), use the current prediction
        new_row[0] = p  # lag1_ret becomes the current prediction
        arr = np.vstack([arr[1:], new_row])
        
    return np.array(preds)


def predict_stock_returns(stock_data, horizon=7):
    """
    Main function to predict stock returns
    
    Args:
        stock_data: DataFrame with columns date, open, high, low, close, volume
        horizon: Number of days to predict
        
    Returns:
        Dictionary with prediction results and metadata
    """
    global model, feature_cols, window_size
    
    if stock_data.empty:
        return {"error": "No stock data provided"}
            
    if model is None or feature_cols is None or window_size is None:
        return {"error": "Model not loaded properly"}
    
    try:
        df = stock_data.copy()
        
        # Set date column as index if needed
        date_col = 'date' if 'date' in df.columns else 'Date' if 'Date' in df.columns else None
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col)
        
        # Rename columns to match expected format
        df = df.rename(columns={
            col: col[0].upper() + col[1:] for col in ['open', 'high', 'low', 'close', 'volume']
            if col in df.columns
        })
        
        # Validate required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return {"error": f"Missing required columns: {missing}"}
        
        # Compute technical indicators
        df = compute_indicators(df)
        
        # Check if we have all the required features that the model expects
        missing_features = [f for f in feature_cols if f not in df.columns]
        if missing_features:
            available_features_list = [f for f in feature_cols if f in df.columns]
            return {"error": f"Feature mismatch. Model expects {len(feature_cols)} features: {feature_cols}. Available: {len(available_features_list)} features: {available_features_list}. Missing: {missing_features}"}
        
        # Use the exact feature order from the model
        available_features = feature_cols
        
        # Prepare data by quarters for scaling
        scalers_q, df_scaled = prepare_quarterly(df, available_features, "Return_1D", window_size)
        
        if not scalers_q:
            return {"error": "Could not create quarterly scalers. Insufficient data."}
        
        # Get last window for prediction
        last_window = build_last_window(df_scaled, available_features, window_size)
        
        # Make prediction
        forecast_scaled = forecast_future_scaled(model, last_window, horizon)
        
        # Unscale the predictions
        q_last = str(df_scaled.index[-1].to_period("Q"))
        
        # Try to get the scaler for the current quarter, fallback to most recent available
        if q_last in scalers_q:
            m = scalers_q[q_last]
        else:
            # Use the most recent scaler if current quarter's scaler doesn't exist
            available_quarters = list(scalers_q.keys())
            if not available_quarters:
                return {"error": "No scalers available for unscaling predictions"}
            
            # Sort quarters and use the most recent one
            sorted_quarters = sorted(available_quarters)
            m = scalers_q[sorted_quarters[-1]]
        
        minv, maxv = m.data_min_[-1], m.data_max_[-1]  # min/max for target feature
        raw_rets = forecast_scaled * (maxv - minv) + minv
        pct_rets = raw_rets * 100
        
        # Calculate price forecasts
        last_price = df["Close"].iloc[-1]
        price_forecast = [float(last_price * (1 + raw_rets[0]))]
        
        for r in raw_rets[1:]:
            price_forecast.append(float(price_forecast[-1] * (1 + r)))
        
        # Format dates for the forecast
        last_date = df.index[-1]
        if not isinstance(last_date, (pd.Timestamp, datetime)):
            last_date = pd.to_datetime(last_date)
        forecast_dates = [(last_date + timedelta(days=i+1)).strftime("%Y-%m-%d") 
                          for i in range(horizon)]
        
        # Create response data
        return {
            "last_date": last_date.strftime("%Y-%m-%d"),
            "last_price": float(last_price),
            "forecast": [
                {
                    "date": date,
                    "return_pct": float(ret),
                    "price": float(price)
                } for date, ret, price in zip(forecast_dates, pct_rets, price_forecast)
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}
