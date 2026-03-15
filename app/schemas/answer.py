from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    question_id: int = Field(..., description="The ID of the question returned by GET /question/")
    user_answer: str = Field(..., description="Free-text answer. Spelling mistakes and phrases like 'What is X' are accepted.")


class AnswerResponse(BaseModel):
    is_correct: bool
    ai_response: str