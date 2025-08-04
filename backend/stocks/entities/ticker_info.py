from pydantic import BaseModel, Field

class TickerInfo(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol 'NVDA' or 'AAPL'")