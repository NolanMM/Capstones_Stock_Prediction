from ..entities.general_knowledge import GeneralKnowledgeResponse

class GeneralKnowledgeServices:
    def __init__(self, client):
        self.client = client

    def handle_general_question(self, query: str) -> GeneralKnowledgeResponse | None:
        print("Handling general knowledge question...")
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=GeneralKnowledgeResponse,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert financial educator. Your goal is to explain complex financial concepts in a simple, clear, and accessible way. Respond using the provided schema.",
                },
                {
                    "role": "user", 
                    "content": f"Please explain the following financial concept: {query}"
                },
            ],
        )