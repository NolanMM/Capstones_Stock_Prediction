from datetime import datetime, timedelta
import requests

class RetrieveDataServices:
    def __init__(self, client=None, fmp_api_key=None, finnhub_api_key=None):
        self.client = client
        self.fmp_api_key = fmp_api_key
        self.finnhub_api_key = finnhub_api_key

    def get_fmp_data(self, ticker: str) -> dict | None:
        number_of_days_trading_1_year = 252
        if not self.fmp_api_key:
            print("FMP API key not found.")
            return None
        try:
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={self.fmp_api_key}"
            profile_response = requests.get(profile_url)
            profile_response.raise_for_status()
            profile_data = profile_response.json()[0]

            hist_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={self.fmp_api_key}"
            hist_response = requests.get(hist_url)
            hist_response.raise_for_status()
            historical_data = hist_response.json()["historical"]
            
            high_52_week = None
            low_52_week = None
            if historical_data:
                historical_data = historical_data[:number_of_days_trading_1_year]
                high_52_week = max(d["high"] for d in historical_data)
                low_52_week = min(d["low"] for d in historical_data)

            fmp_data = {
                "profile": profile_data,
                "historical_summary": {
                    "high_52_week": high_52_week,
                    "low_52_week": low_52_week,
                },
            }
            print(f"Fetched Fundamental and Historical data from FMP for {ticker}")
            return fmp_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from FMP: {e}")
            return None

    def get_finnhub_news(self, ticker: str) -> str:
        """Gets company news for a given ticker from the past year using Finnhub API."""
        if not self.finnhub_api_key:
            print("Finnhub API key not found.")
            return None
        to_date, from_date = datetime.now().strftime("%Y-%m-%d"), (
            datetime.now() - timedelta(days=365)
        ).strftime("%Y-%m-%d")
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={self.finnhub_api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            news_items = [
                f"- Headline: {item['headline']}\n  Summary: {item['summary']}"
                for item in response.json()[:20]
            ]
            print(
                f"Fetched {len(news_items)} News Articles from Finnhub for the past year."
            )
            return (
                "\n".join(news_items)
                if news_items
                else "No news found for the past year."
            )
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news from Finnhub: {e}")
            return None
