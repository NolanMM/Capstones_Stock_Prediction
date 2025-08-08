from pydantic import BaseModel, Field
from .user_intent import UserIntent

class IntentClassification(BaseModel):
    intent: UserIntent = Field(
        ..., description="The classification of the user's query."
    )