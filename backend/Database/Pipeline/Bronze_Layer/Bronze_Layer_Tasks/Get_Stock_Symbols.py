from urllib.request import urlopen
import pandas as pd
import certifi
import json

def Get_Data_From_URL_FMP(url_available_stock_market, api_key):
    url_available_stock_market_api = url_available_stock_market + api_key
    response = urlopen(url_available_stock_market_api, cafile=certifi.where())
    data = response.read().decode("utf-8")
    data_df = pd.DataFrame(json.loads(data))
    return data_df