from Bronze_Layer.Bronze_Layer_Tasks.Transactional_Tables.Historical_Stock_Prices_Fact_Tables_Task import Ingest_Historical_Stock_Prices_Fact_Tables_Data
from Bronze_Layer.Bronze_Layer_Tasks.Transactional_Tables.Historical_Stock_Prices_Fact_Tables_Task import Transform_Historical_Stock_Prices_Fact_Tables_Data
from Bronze_Layer.Bronze_Layer_Tasks.Transactional_Tables.Historical_Stock_Prices_Fact_Tables_Task import Store_Historical_Stock_Prices_Fact_Tables_Data
from Bronze_Layer.Bronze_Layer_Tasks.Get_Stock_Symbols import Get_Data_From_URL_FMP
from Bronze_Layer.Azure_Services import write_dataframe_to_blob
from prefect import task, flow
from datetime import timedelta
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv("./Bronze_Layer/.env", override=True)

FMP_URL_AVAILABLE_STOCK_SYMBOLS_SP500 = "https://financialmodelingprep.com/stable/sp500-constituent?apikey="
FMP_URL_AVAILABLE_STOCK_SYMBOLS_NASDAQ = "https://financialmodelingprep.com/stable/nasdaq-constituent?apikey="
FMP_URL_AVAILABLE_STOCK_SYMBOLS_DOWJONES = "https://financialmodelingprep.com/stable/dowjones-constituent?apikey="
API_KEY_FMP = os.getenv("API_KEY_FMP")

@task
def Get_Available_Stock_Symbols_Market_Data_FMP_(url_available_stock_market, api_key):
    return Get_Data_From_URL_FMP(url_available_stock_market, api_key)

@task
def Append_File_To_Azure_Blob_Storage(list_dict_data):
    list_data_fact_tables = []
    for Historical_Financial_Statement_Fact_Table_symbol_df_data_processed_ in list_dict_data:
        for symbol, processed_df in Historical_Financial_Statement_Fact_Table_symbol_df_data_processed_.items():
            if processed_df is None:
                continue
            try:
                list_data_fact_tables.append(processed_df.to_pandas())
            except Exception as e:
                print(f"❌ Error storing data for {symbol}: {e}")
        
    processed_df = pd.concat(list_data_fact_tables)
    if processed_df is None:
        return "No data to store"
    try:
        directory = f"/DataFact_tables/"
        file_path = f"{directory}/Historical_Stock_Prices_Fact_Data_SP500_NAQ_DJI.csv"
        # processed_df.write_csv(file_path)
        write_dataframe_to_blob(processed_df, file_path)
        print(f"✅ Successfully stored {symbol} at {file_path}")
    except Exception as e:
        print(f"❌ Error storing data for {symbol}: {e}")

# Ingest, Transform, and Store Historical Stock Prices Fact Tables Data (SP500 Index)
@task
def Fetch_Historical_Stock_Prices_Fact_Tables_Market_Tasks(symbols, market_index, start="2010-01-01", end=pd.Timestamp.now().strftime("%Y-%m-%d")):
    """
    End-to-end process:
    1. Fetch raw stock data.
    2. Transform raw data into structured Polars DataFrames.
    3. Store structured data in CSV format.
    """
    # Stage 1: Data Ingestion
    df_stock_prices = Ingest_Historical_Stock_Prices_Fact_Tables_Data(symbols, start, end)
    
    # Stage 2: Data Transformation
    df_stock_prices_processed_ = Transform_Historical_Stock_Prices_Fact_Tables_Data(df_stock_prices, market_index)
    
    # Stage 3: Data Storage
    result = Store_Historical_Stock_Prices_Fact_Tables_Data(df_stock_prices_processed_, market_index)

    return df_stock_prices_processed_

@flow(log_prints=True)
def Bronze_Layer_Historical_Stock_Prices_Fact_Tables_Flow():
    SP500_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_SP500, API_KEY_FMP)
    historical_stock_prices_sp500_fact_table_dict = Fetch_Historical_Stock_Prices_Fact_Tables_Market_Tasks(SP500_index_df["symbol"].to_list()[:100], "SP500")
    #Append_File_To_Azure_Blob_Storage(historical_stock_prices_sp500_fact_table_dict, "SP500")

    NASDAQ_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_NASDAQ, API_KEY_FMP)
    historical_stock_prices_nasdaq_fact_table_dict = Fetch_Historical_Stock_Prices_Fact_Tables_Market_Tasks(NASDAQ_index_df["symbol"].to_list()[:100], "Nasdaq")
    #Append_File_To_Azure_Blob_Storage(historical_stock_prices_nasdaq_fact_table_dict, "Nasdaq")

    DOWJONES_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_DOWJONES, API_KEY_FMP)
    historical_stock_prices_dowjones_fact_table_dict = Fetch_Historical_Stock_Prices_Fact_Tables_Market_Tasks(DOWJONES_index_df["symbol"].to_list()[:100], "Dowjones")
    #Append_File_To_Azure_Blob_Storage(historical_stock_prices_dowjones_fact_table_dict, "Dowjones")

    list_dict_data = [historical_stock_prices_sp500_fact_table_dict, historical_stock_prices_nasdaq_fact_table_dict, historical_stock_prices_dowjones_fact_table_dict]
    Append_File_To_Azure_Blob_Storage(list_dict_data)

# if __name__ == "__main__":
#     Bronze_Layer_Historical_Stock_Prices_Fact_Tables_Flow.serve(
#         name="Bronze_Layer_Historical_Stock_Prices_Fact_Tables_Flow"
#     )
