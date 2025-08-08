from ..entities.intent_classification import IntentClassification

class RouteQueryService:
    def __init__(self, client):
        self.client = client

    def route_query(self, query: str) -> IntentClassification:
        """Classifies the user's intent to route them to the correct tool either for a specific stock/company or a general finance/economic topic."""
        print("Routing user query...")
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=IntentClassification,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at classifying user queries in the financial domain. Determine if the user is asking about a specific stock/company, a general finance/economic topic, or is asking for investment advice ('should I...', 'is it a good idea to...').",
                },
                {"role": "user", "content": query},
            ],
        )
