import pandas as pd
import requests
import time
from datetime import datetime, timedelta

class SAndPNewsFetcher:
    def __init__(self, dbutils, sandp_url_secret_scope: str = "Capstone", sandp_url_secret_key: str = "sandp500url",
                 finhub_key_scope: str = "Capstone", finhub_key_secret: str = "FinhubAPIKey",
                 sleep_seconds: int = 1):
        self.dbutils = dbutils
        # URLs and API keys
        self.sandp_url = dbutils.secrets.get(scope=sandp_url_secret_scope, key=sandp_url_secret_key)
        self.api_key = dbutils.secrets.get(scope=finhub_key_scope, key=finhub_key_secret)
        # Date range: yesterday to today
        today = pd.Timestamp.now().normalize()
        self.end_date = today.strftime("%Y-%m-%d")
        self.start_date = (today - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        self.sleep_seconds = sleep_seconds

    def read_sp500_symbols(self) -> list[str]:
        tables = pd.read_html(self.sandp_url)
        sp500_table = tables[0]
        return sp500_table["Symbol"].tolist()

    def fetch_news_for_symbol(self, symbol: str) -> pd.DataFrame:
        url = (
            f"https://finnhub.io/api/v1/company-news"
            f"?symbol={symbol}"
            f"&from={self.start_date}"
            f"&to={self.end_date}"
            f"&token={self.api_key}"
        )
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch {symbol}: HTTP {resp.status_code}")
            return pd.DataFrame()

        data = resp.json()
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        # convert unix timestamp to datetime and filter only end_date
        df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
        df = df[df["datetime"].dt.strftime("%Y-%m-%d") == self.end_date]
        if not df.empty:
            df["symbol"] = symbol
        return df

    def fetch_all_news(self) -> pd.DataFrame:
        symbols = self.read_sp500_symbols()
        all_news = []
        for symbol in symbols:
            try:
                df = self.fetch_news_for_symbol(symbol)
                if not df.empty:
                    all_news.append(df)
                time.sleep(self.sleep_seconds)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
            finally:
                print(f"✅ Processed {symbol}")

        if not all_news:
            return pd.DataFrame()
        result = pd.concat(all_news, ignore_index=True)
        return result

    def run(self) -> pd.DataFrame:
        news_df = self.fetch_all_news()
        print(f"Fetched news for {len(news_df)} articles on {self.end_date}")
        return news_df


fetcher = SAndPNewsFetcher(dbutils)
today_news = fetcher.run()
today_news.to_csv('/dbfs/FileStore/News/sp500_news.csv', index=False)
