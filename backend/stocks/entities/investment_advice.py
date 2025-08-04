from pydantic import BaseModel, Field
from typing import List

class InvestmentAdviceResponse(BaseModel):
    question: str = Field(
        ..., description="The user's original investment advice question."
    )
    advice_summary: str = Field(
        ..., description="A direct answer to the user's question, framed as educational insight."
    )
    reasoning: List[str] = Field(
        ..., description="A list of points explaining the factors and reasoning behind the advice."
    )
    potential_risks: List[str] = Field(
        ..., description="A list of potential risks associated with the investment topic."
    )
    disclaimer: str = Field(
        description="A non-negotiable disclaimer stating that this is not financial advice.",
        default="Disclaimer: I am an AI assistant and not a licensed financial advisor. This information is for educational purposes only and should not be considered financial advice. Please consult with a qualified professional before making any investment decisions."
    )