import yfinance as yf
import pandas as pd
import polars as pl
import time
import os

DATABASE_WORK_PATH = "./Bronze_Layer_Data/DataFact_tables"

def Ingest_Historical_Stock_Prices_Fact_Tables_Data(symbols, start="2010-01-01", end=pd.Timestamp.now().strftime("%Y-%m-%d")):
    """
    Fetch raw historical stock price data from Yahoo Finance.
    Returns a dictionary where keys are stock symbols and values are raw Pandas DataFrames.
    """
    stock_data = {}
    for symbol in symbols:
        try:
            data_yf = yf.download(symbol, start=start, end=end)
            # Rate-limiting to avoid getting blocked
            time.sleep(2)
            if data_yf.empty:
                print(f"⚠️ No data found for {symbol}")
                stock_data[symbol] = None
                continue
            stock_data[symbol] = data_yf
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            stock_data[symbol] = None
    return stock_data

def Transform_Historical_Stock_Prices_Fact_Tables_Data(stock_data, market_index):
    """
    Convert raw stock data from Pandas to Polars DataFrame.
    Returns a dictionary with structured data.
    """
    transformed_data = {}
    for symbol, raw_data in stock_data.items():
        if raw_data is None:
            transformed_data[symbol] = None
            continue
        try:
            pl_df = pl.DataFrame(raw_data.reset_index())
            pl_df = pl_df.rename({
                f"('Date', '')": "Date",
                f"('Close', '{symbol}')": "Close_Prices",
                f"('High', '{symbol}')": "High_Prices",
                f"('Low', '{symbol}')": "Low_Prices",
                f"('Open', '{symbol}')": "Open_Prices",
                f"('Volume', '{symbol}')": "Volume"
            })
            pl_df = pl_df.with_columns(pl.lit(symbol).alias("Symbol"))
            pl_df = pl_df.with_columns(pl.lit(market_index).alias("Market_Index"))
            transformed_data[symbol] = pl_df
        except Exception as e:
            print(f"❌ Error transforming data for {symbol}: {e}")
            transformed_data[symbol] = None
    return transformed_data

def Store_Historical_Stock_Prices_Fact_Tables_Data(stock_data, market_index):
    """
    Save transformed stock data to CSV files.
    """
    for symbol, processed_df in stock_data.items():
        if processed_df is None:
            continue
        try:
            directory = f"{DATABASE_WORK_PATH}/{market_index}"
            os.makedirs(directory, exist_ok=True)
            file_path = f"{directory}/{symbol}.csv"
            if hasattr(processed_df, "to_csv"):
                processed_df.to_csv(file_path, index=False)
            elif hasattr(processed_df, "write_csv"):
                processed_df.write_csv(file_path)
            else:
                raise TypeError("Unsupported DataFrame type")
            print(f"✅ Successfully stored {symbol} at {file_path}")
        except Exception as e:
            print(f"❌ Error storing data for {symbol}: {e}")