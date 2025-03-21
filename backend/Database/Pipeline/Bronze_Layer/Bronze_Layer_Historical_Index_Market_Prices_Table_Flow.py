from Bronze_Layer.Bronze_Layer_Tasks.Get_Stock_Symbols import Get_Data_From_URL_FMP
from Bronze_Layer.Azure_Services import write_dataframe_to_blob
from prefect import task, flow
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv("./Bronze_Layer/.env", override=True)

DATABASE_WORK_PATH = "./Bronze_Layer_Data/"
FMP_URL_MARKET_INDEX_QUOTE_DETAILS = "https://financialmodelingprep.com/api/v3/quotes/index?apikey="
API_KEY_FMP = os.getenv("API_KEY_FMP")

@task
def Get_Historical_Index_Market_Quote_Data_FMP(url_available_fmp, api_key):
    return Get_Data_From_URL_FMP(url_available_fmp, api_key)

@task
def Append_File_To_Azure_Blob_Storage(df_data_processed_):
    if df_data_processed_ is None:
        return "No data processed"
    try:
        directory = "/DataDimensional_tables/Historical_Index_Market_Quote_Data.csv"
        write_dataframe_to_blob(df_data_processed_, directory)
        print(f"✅ Successfully stored Historical_Index_Market_Quote_Data at Blob Storage")
    except Exception as e:
        print(f"❌ Error storing data for {e}")

@task
def Store_Historical_Index_Market_Quote_Data_Table_Data(list_index_market_quote_df_):
    list_index_market_group_path = f"{DATABASE_WORK_PATH}DataDimensional_tables"
    os.makedirs(list_index_market_group_path, exist_ok=True)
    list_index_market_quote_df_.to_csv(f"{list_index_market_group_path}/Historical_Index_Market_Quote_Data.csv")

@flow(log_prints=True)
def Bronze_Layer_Historical_Index_Market_Prices_Table_Flow():
    list_index_market_quote_df = Get_Historical_Index_Market_Quote_Data_FMP(FMP_URL_MARKET_INDEX_QUOTE_DETAILS, API_KEY_FMP)
    Store_Historical_Index_Market_Quote_Data_Table_Data(list_index_market_quote_df)
    Append_File_To_Azure_Blob_Storage(list_index_market_quote_df)
    

# if __name__ == "__main__":
#     Bronze_Layer_Historical_Index_Market_Prices_Table_Flow.serve(
#         name="Bronze_Layer_Historical_Index_Market_Prices_Table_Flow"
#     )