from urllib.request import urlopen
import polars as pl
import requests
import certifi
import time
import json
import os

DATABASE_WORK_PATH="./Bronze_Layer_Data/DataDimensional_tables/"
FMP_URL_STOCK_COMPANY_PROFILE_DETAILS = "https://financialmodelingprep.com/api/v3/profile/"

def Ingest_Company_Information_Profile_Dimensional_Data(symbols, api_key):
    """
    Fetch raw company information profile stock dimensional
    Returns a dictionary where keys are stock symbols and values are raw Pandas DataFrames.
    """
    company_information_profile_dimensional_dict = {}
    for symbol in symbols:
        try:
            url_company_information_profile_dimensional = FMP_URL_STOCK_COMPANY_PROFILE_DETAILS + f"{symbol}?apikey={api_key}"
            response = urlopen(url_company_information_profile_dimensional, cafile=certifi.where())
            data = response.read().decode("utf-8")
            data_df_pl = pl.DataFrame(json.loads(data))
            # Rate-limiting to avoid getting blocked
            time.sleep(2)
            if data_df_pl.is_empty():
                print(f"⚠️ No data found for {symbol}")
                company_information_profile_dimensional_dict[symbol] = None
                continue

            for col in data_df_pl.columns:
                if data_df_pl[col].dtype == pl.Float64:
                    data_df_pl = data_df_pl.with_columns(data_df_pl[col].cast(pl.Float64))
                elif data_df_pl[col].dtype == pl.Int64:
                    data_df_pl = data_df_pl.with_columns(data_df_pl[col].cast(pl.Float64))
            
            company_information_profile_dimensional_dict[symbol] = data_df_pl
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            company_information_profile_dimensional_dict[symbol] = None

    dataframes_final = [df for df in company_information_profile_dimensional_dict.values() if df is not None]
    if dataframes_final:
        return pl.concat(dataframes_final, how="vertical")
    else:
        return pl.DataFrame()

def Transform_Company_Information_Profile_Dimensional_Data(company_information_profile_dimensional_df_data_raw, market_index, image_column="image"):
    """
    Download images from URLs in a Polars DataFrame and save them with custom filenames.
    """
    save_path= DATABASE_WORK_PATH + "stock_company_images"
    os.makedirs(save_path, exist_ok=True)
    pl_df = company_information_profile_dimensional_df_data_raw.unique(keep="any", maintain_order=True)
    pl_df = pl_df.with_columns(pl.lit(market_index).alias("market_index"))
    for idx, row in enumerate(pl_df.iter_rows(named=True)):
        image_url = row.get(image_column)
        if not image_url:
            print(f"⚠️ Skipping empty URL at row {idx}")
            continue
        try:
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            filename = os.path.basename(image_url)
            file_path = os.path.join(save_path, filename)
            with open(file_path, "wb") as img_file:
                for chunk in response.iter_content(1024):
                    img_file.write(chunk)
            print(f"✅ Saved: {file_path}")
            return pl_df
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to download {image_url}: {e}")
            return pl_df
        

def Store_Company_Information_Profile_Dimensional_Data(company_information_profile_dimensional_df_data_processed, market_index):
    """
    Save transformed stock data to CSV files.
    """
    if company_information_profile_dimensional_df_data_processed is None:
        return "Empty Dataframe"
    try:
        directory = f"{DATABASE_WORK_PATH}"
        os.makedirs(directory, exist_ok=True)  # Ensure directory exists
        file_path = f"{directory}company_information_profile_{market_index}_dimensional.csv"
        company_information_profile_dimensional_df_data_processed.write_csv(file_path)
        print(f"✅ Successfully stored company_information_profile_dimensional.csv at {file_path}")
    except Exception as e:
        print(f"❌ Error storing data for company_information_profile_dimensional.csv: {e}")
