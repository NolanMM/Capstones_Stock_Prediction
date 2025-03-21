from Bronze_Layer.Bronze_Layer_Tasks.Transactional_Tables.Historical_Financial_Statement_Fact_Table_Task import Ingest_Quarter_Historical_Financial_Statement_Fact_Data
from Bronze_Layer.Bronze_Layer_Tasks.Transactional_Tables.Historical_Financial_Statement_Fact_Table_Task import Transform_Quarter_Historical_Financial_Statement_Fact_Data
from Bronze_Layer.Bronze_Layer_Tasks.Transactional_Tables.Historical_Financial_Statement_Fact_Table_Task import Store_Quarter_Historical_Financial_Statement_Fact_Data
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
    for fact_tabbles in list_dict_data:
        for symbol, processed_df in fact_tabbles.items():
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
        directory = "/DataDimensional_tables"
        file_path = f"{directory}/Financial_Statement_Historical_Fact_Table_SP500_NAQ_DJI.csv"
        # processed_df.write_csv(file_path)
        write_dataframe_to_blob(processed_df, file_path)
        print(f"✅ Successfully stored {symbol} at {file_path}")
    except Exception as e:
        print(f"❌ Error storing data for {symbol}: {e}")
    

@task
def Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow_Tasks(symbols, market_index):
    """
    End-to-end process:
    1. Fetch raw stock data.
    2. Transform raw data into structured Polars DataFrames.
    3. Store structured data in CSV format.
    """
    # Stage 1: Data Ingestion
    Historical_Financial_Statement_Fact_Table_symbol_df = Ingest_Quarter_Historical_Financial_Statement_Fact_Data(symbols, "quarter", API_KEY_FMP, 10000)
    
    # Stage 2: Data Transformation
    Historical_Financial_Statement_Fact_Table_symbol_df_data_processed_ = Transform_Quarter_Historical_Financial_Statement_Fact_Data(Historical_Financial_Statement_Fact_Table_symbol_df, market_index)
    
    # Stage 3: Data Storage
    result = Store_Quarter_Historical_Financial_Statement_Fact_Data(Historical_Financial_Statement_Fact_Table_symbol_df_data_processed_)

    return Historical_Financial_Statement_Fact_Table_symbol_df_data_processed_

@flow(log_prints=True)
def Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow():
    SP500_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_SP500, API_KEY_FMP)
    historical_index_market_prices_sp500_fact_table_dict = Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow_Tasks(SP500_index_df["symbol"].to_list()[:100], "SP500")
    
    NASDAQ_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_NASDAQ, API_KEY_FMP)
    historical_index_market_prices_nasdaq_fact_table_dict = Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow_Tasks(NASDAQ_index_df["symbol"].to_list()[:100], "NASDAQ")

    DOWJONES_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_DOWJONES, API_KEY_FMP)
    historical_index_market_prices_dowjones_fact_table_dict = Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow_Tasks(DOWJONES_index_df["symbol"].to_list()[:100], "DOWJONES")

    list_dict_data = [historical_index_market_prices_sp500_fact_table_dict, historical_index_market_prices_nasdaq_fact_table_dict, historical_index_market_prices_dowjones_fact_table_dict]
    Append_File_To_Azure_Blob_Storage(list_dict_data)
# if __name__ == "__main__":
#     Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow.serve(
#         name="Bronze_Layer_Historical_Financial_Statement_Fact_Table_Flow"
#     )
