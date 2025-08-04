from ..entities.investment_advice import InvestmentAdviceResponse

class InvestmentAdviceService:
    def __init__(self, client):
        self.client = client

    def provide_investment_advice(self, query: str) -> InvestmentAdviceResponse | None:
        """
        Provides a balanced, educational perspective on an investment advice question.
        """
        print("Generating investment advice...")
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=InvestmentAdviceResponse,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial educator. Your role is to provide a balanced, neutral, and educational perspective on investment-related questions. You must not give direct financial advice. Frame all responses educationally. Always explain the pros, cons, and associated risks. Ensure the disclaimer is always included.",
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
        )