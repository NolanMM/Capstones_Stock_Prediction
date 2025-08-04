from pydantic import BaseModel, Field
from typing import List

class FinancialAnalysis(BaseModel):
    company_name: str = Field(
        ..., description="The name of the company being analyzed."
    )
    ticker_symbol: str = Field(..., description="The stock ticker symbol.")
    stock_price: float = Field(
        ..., description="The latest stock price from the provided data."
    )
    market_cap: int = Field(
        ..., description="The company's market capitalization from the provided data."
    )
    industry: str = Field(..., description="The industry the company operates in.")
    summary_52_week: str = Field(
        ...,
        description="A summary of the stock's performance over the last 52 weeks, referencing the high and low.",
    )
    recommendation: str = Field(
        ...,
        description="A clear 'Buy', 'Sell', or 'Hold' recommendation based on the holistic analysis.",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="A confidence score for the recommendation, from 0.0 to 1.0.",
    )
    sentiment_analysis: str = Field(
        ...,
        description="Overall sentiment ('Bullish', 'Bearish', 'Neutral') based on an analysis of news headlines and summaries from the past year.",
    )
    key_themes: List[str] = Field(
        ...,
        description="A list of key strategic themes, challenges, or opportunities identified from the news and company data.",
    )
    key_insights: List[str] = Field(
        ...,
        description="A list of 4-5 actionable insights derived from the complete analysis.",
    )
