from Bronze_Layer.Bronze_Layer_Tasks.Dimensional_Tables.Dimensional_Stock_Company_Information_Profile_Table_Tasks import Ingest_Company_Information_Profile_Dimensional_Data
from Bronze_Layer.Bronze_Layer_Tasks.Dimensional_Tables.Dimensional_Stock_Company_Information_Profile_Table_Tasks import Transform_Company_Information_Profile_Dimensional_Data
from Bronze_Layer.Bronze_Layer_Tasks.Dimensional_Tables.Dimensional_Stock_Company_Information_Profile_Table_Tasks import Store_Company_Information_Profile_Dimensional_Data
from Bronze_Layer.Bronze_Layer_Tasks.Get_Stock_Symbols import Get_Data_From_URL_FMP
from Bronze_Layer.Azure_Services import write_dataframe_to_blob
import pandas as pd
import polars as pl
from prefect import task, flow
from dotenv import load_dotenv
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
def Append_File_To_Azure_Blob_Storage(list_data):
    list_data_df = []
    for df in list_data:
        if not isinstance(df, pd.DataFrame):
            df = df.to_pandas()

        list_data_df.append(df)
    company_information_profile_dimensional_df_data_processed = pd.concat(list_data_df)
    if company_information_profile_dimensional_df_data_processed is None:
        return "No data to store"
    try:
        directory = f"DataDimensional_tables"
        file_path = f"{directory}/company_information_profile_SP500_NAQ_DJI_dimensional.csv"
        # processed_df.write_csv(file_path)
        write_dataframe_to_blob(company_information_profile_dimensional_df_data_processed, file_path)
        print(f"✅ Successfully stored CSV Files at {file_path}")
    except Exception as e:
        print(f"❌ Error storing data for CSV Files: {e}")

# Ingest, Transform, and Store Historical Stock Prices Fact Tables Data (SP500 Index)
@task
def Fetch_Company_Information_Profile_Dimensional_Tasks(symbols, market_index, api_key):
    """
    End-to-end process:
    1. Fetch raw stock data.
    2. Transform raw data into structured Polars DataFrames.
    3. Store structured data in CSV format.
    """
    # Stage 1: Data Ingestion
    df_companies_information = Ingest_Company_Information_Profile_Dimensional_Data(symbols, api_key)
    
    # Stage 2: Data Transformation
    df_companies_information_processed = Transform_Company_Information_Profile_Dimensional_Data(df_companies_information, market_index)
    
    # Stage 3: Data Storage
    result = Store_Company_Information_Profile_Dimensional_Data(df_companies_information_processed, market_index)

    return df_companies_information_processed

@flow(log_prints=True)
def Bronze_Layer_Stock_Company_Information_Profile_Dimensional_Table_Flow():
    SP500_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_SP500, API_KEY_FMP)
    dimensional_companies_information_profile_sp500_table_df = Fetch_Company_Information_Profile_Dimensional_Tasks(SP500_index_df["symbol"].to_list()[:100], "SP500", API_KEY_FMP)
    
    NASDAQ_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_NASDAQ, API_KEY_FMP)
    dimensional_companies_information_profile_nasdaq_fact_table_df = Fetch_Company_Information_Profile_Dimensional_Tasks(NASDAQ_index_df["symbol"].to_list()[:100], "Nasdaq", API_KEY_FMP)

    DOWJONES_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_AVAILABLE_STOCK_SYMBOLS_DOWJONES, API_KEY_FMP)
    dimensional_companies_information_profile_dowjones_table_df = Fetch_Company_Information_Profile_Dimensional_Tasks(DOWJONES_index_df["symbol"].to_list()[:100], "Dowjones", API_KEY_FMP)

    list_dict_data = [dimensional_companies_information_profile_sp500_table_df, dimensional_companies_information_profile_nasdaq_fact_table_df, dimensional_companies_information_profile_dowjones_table_df]
    Append_File_To_Azure_Blob_Storage(list_dict_data)
# if __name__ == "__main__":
#     Bronze_Layer_Stock_Company_Information_Profile_Dimensional_Table_Flow.serve(
#         name="Bronze_Layer_Stock_Company_Information_Profile_Dimensional_Table_Flow"
#     )
