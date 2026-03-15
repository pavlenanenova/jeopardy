from pydantic import BaseModel, Field, field_validator


class QuestionResponse(BaseModel):
    question_id: int = Field(..., description="Use this ID to verify an answer via POST /verify-answer/")
    round: str = Field(..., description="Jeopardy!, Double Jeopardy!, or Final Jeopardy!")
    category: str = Field(..., description="The question category e.g. HISTORY")
    value: str | None = Field(None, description="Dollar value e.g. $200. Null for Final Jeopardy!")
    question: str = Field(..., description="The clue text shown on the board")

    model_config = {"from_attributes": True}

    @field_validator("value")
    @classmethod
    def value_required_unless_final_jeopardy(cls, v, info):
        """Value is expected unless round is Final Jeopardy!"""
        if info.data.get("round") != "Final Jeopardy!" and v is None:
            raise ValueError("Value is required unless round is Final Jeopardy!")
        return v