from urllib.request import urlopen
import polars as pl
import certifi
import time
import json
import os

DATABASE_WORK_PATH = "./Bronze_Layer_Data/"
FMP_URL_STOCK_KEY_METRICS = "https://financialmodelingprep.com/api/v3/key-metrics/"

def Ingest_Quarter_Historical_Financial_Statement_Fact_Data(symbols, period, api_key, limit=10000):
    """
    Fetch raw historical stock price data from Yahoo Finance.
    Returns a dictionary where keys are stock symbols and values are raw Pandas DataFrames.
    """
    quarter_historical_financial_statement_fact_dict = {}
    for symbol in symbols:
        try:
            url_quarter_historical_financial_statement_fact = FMP_URL_STOCK_KEY_METRICS + f"{symbol}?period={period}&limit={limit}&apikey={api_key}"
            response = urlopen(url_quarter_historical_financial_statement_fact, cafile=certifi.where())
            data = response.read().decode("utf-8")
            data_df_pl = pl.DataFrame(json.loads(data))
            # Rate-limiting to avoid getting blocked
            time.sleep(3)
            if data_df_pl.is_empty():
                print(f"⚠️ No data found for {symbol}")
                quarter_historical_financial_statement_fact_dict[symbol] = None
                continue
            quarter_historical_financial_statement_fact_dict[symbol] = data_df_pl
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            quarter_historical_financial_statement_fact_dict[symbol] = None
    return quarter_historical_financial_statement_fact_dict

def Transform_Quarter_Historical_Financial_Statement_Fact_Data(quarter_historical_financial_statement_fact_data, market_index):
    """
    Convert raw stock data from Pandas to Polars DataFrame.
    Returns a dictionary with structured data.
    """
    transformed_data = {}
    for symbol, raw_data in quarter_historical_financial_statement_fact_data.items():
        if raw_data is None:
            transformed_data[symbol] = None
            continue
        try:
            pl_df = raw_data.unique(keep="any", maintain_order=True)
            pl_df = pl_df.with_columns(pl.lit(market_index).alias("market_index"))
            transformed_data[symbol] = pl_df
        except Exception as e:
            print(f"❌ Error transforming data for {symbol}: {e}")
            transformed_data[symbol] = None
    return transformed_data

def Store_Quarter_Historical_Financial_Statement_Fact_Data(quarter_historical_financial_statement_fact_data_process):
    """
    Save transformed stock data to CSV files.
    """
    for symbol, processed_df in quarter_historical_financial_statement_fact_data_process.items():
        if processed_df is None:
            continue
        try:
            directory = f"{DATABASE_WORK_PATH}Dimensional_tables/Financial_Statement_Historical_Fact_Table"
            os.makedirs(directory, exist_ok=True)
            file_path = f"{directory}/{symbol}.csv"
            processed_df.write_csv(file_path)
            print(f"✅ Successfully stored {symbol} at {file_path}")
        except Exception as e:
            print(f"❌ Error storing data for {symbol}: {e}")