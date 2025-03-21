from Bronze_Layer.Bronze_Layer_Tasks.Get_Stock_Symbols import Get_Data_From_URL_FMP
from Bronze_Layer.Azure_Services import write_dataframe_to_blob
from prefect import task, flow
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv("./Bronze_Layer/.env", override=True)

DATABASE_WORK_PATH = "./Bronze_Layer_Data/"
FMP_URL_STOCK_SYMBOLS_CHANGE = "https://financialmodelingprep.com/api/v4/symbol_change?apikey="
API_KEY_FMP = os.getenv("API_KEY_FMP")

@task
def Get_Available_Stock_Symbols_Market_Data_FMP_(url_available_fmp, api_key):
    return Get_Data_From_URL_FMP(url_available_fmp, api_key)

@task
def Append_File_To_Azure_Blob_Storage(df_data_processed_):
    if df_data_processed_ is None:
        return "No data processed"
    try:
        directory = "DataDimensional_tables/historical_symbol_stock_change.csv"
        write_dataframe_to_blob(df_data_processed_, directory)
        print(f"✅ Successfully stored Historical_Index_Market_Quote_Data at Blob Storage")
    except Exception as e:
        print(f"❌ Error storing data for {e}")

@task
def Store_Stock_Symbol_Change_Symbol_History_Dimensional_Table_Data(symbol_stock_change_index_df_):
    symbol_stock_change_index_path = f"{DATABASE_WORK_PATH}DataDimensional_tables"
    os.makedirs(symbol_stock_change_index_path, exist_ok=True)
    symbol_stock_change_index_df_.to_csv(f"{symbol_stock_change_index_path}/historical_symbol_stock_change.csv")

# Ingest, Transform, and Store Historical Stock Prices Fact Tables Data (SP500 Index)
@flow(log_prints=True)
def Bronze_Layer_Stock_Symbol_Change_Symbol_History_Dimensional_Table_Flow():
    symbol_stock_change_index_df = Get_Available_Stock_Symbols_Market_Data_FMP_(FMP_URL_STOCK_SYMBOLS_CHANGE, API_KEY_FMP)
    Store_Stock_Symbol_Change_Symbol_History_Dimensional_Table_Data(symbol_stock_change_index_df)
    Append_File_To_Azure_Blob_Storage(symbol_stock_change_index_df)

# if __name__ == "__main__":
#     Bronze_Layer_Stock_Symbol_Change_Symbol_History_Dimensional_Table_Flow.serve(
#         name="Bronze_Layer_Stock_Symbol_Change_Symbol_History_Dimensional_Table_Flow"
#     )
