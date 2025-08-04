from pydantic import BaseModel, Field

class GeneralKnowledgeResponse(BaseModel):
    concept_name: str = Field(
        ..., description="The name of the financial concept being explained."
    )
    definition: str = Field(
        ..., description="A clear, concise definition of the concept."
    )
    importance: str = Field(
        ...,
        description="An explanation of why this concept is important to investors or in finance.",
    )
    example: str = Field(
        ..., description="A simple, illustrative example of the concept in action."
    )
