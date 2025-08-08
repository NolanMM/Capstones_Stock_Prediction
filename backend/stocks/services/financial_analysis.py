from ..entities.financial_analysis import FinancialAnalysis
from .retrieve_data import RetrieveDataServices
from ..entities.ticker_info import TickerInfo

class FinancialAnalysisService:
    def __init__(self, client, fmp_api_key: str, fh_api_key: str):
        self.client = client
        self.fmp_api_key = fmp_api_key
        self.fh_api_key = fh_api_key
        self.retrieve_data_service = RetrieveDataServices(
            fmp_api_key=self.fmp_api_key,
            finnhub_api_key=self.fh_api_key
        )

    def create_financial_analysis(self, query: str) -> FinancialAnalysis | None:
        print("Extracting ticker from query...")
        ticker_info = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=TickerInfo,
            messages=[
                {"role": "system", "content": "You are an expert at extracting stock ticker symbols from user queries."},
                {"role": "user", "content": query},
            ],
        )
        ticker = ticker_info.ticker
        print(f"Ticker extracted: {ticker}")

        fmp_data = self.retrieve_data_service.get_fmp_data(ticker)
        if not fmp_data:
            print(f"Could not retrieve FMP data for {ticker}")
            return None

        news = self.retrieve_data_service.get_finnhub_news(ticker)
        if not news or "Could not retrieve" in news:
            print(f"Could not retrieve Finnhub news for {ticker}")
            news = "No news available."

        print("Generating financial analysis...")
        analysis = self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=FinancialAnalysis,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior financial analyst. Your role is to provide a clear, concise, and insightful analysis of a company based on the provided data. Generate a structured response following the user's schema.",
                },
                {
                    "role": "user",
                    "content": f"Analyze the following company based on the data below and generate a comprehensive report.\n\n"
                               f"User Query: {query}\n"
                               f"Company Profile: {fmp_data['profile']}\n"
                               f"52-Week Data: {fmp_data['historical_summary']}\n"
                               f"Recent News (past year):\n{news}",
                },
            ],
        )
        return analysis