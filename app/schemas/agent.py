from pydantic import BaseModel, Field

from app.models.enums import Round, SkillLevel


class AgentRequest(BaseModel):
    round: Round = Field(..., description="One of: 'Jeopardy!', 'Double Jeopardy!', 'Final Jeopardy!'")
    value: str | None = Field(
        None,
        description="Dollar value of the question: '$200', '$400', '$600', '$800', '$1000', '$1200'. Leave empty for Final Jeopardy!"
    )
    skill_level: SkillLevel = Field(
        SkillLevel.INTERMEDIATE,
        description="Agent skill level. 'beginner' makes frequent mistakes, 'intermediate' is occasionally wrong, 'expert' almost always correct."
    )


class AgentResponse(BaseModel):
    agent_name: str
    question: str
    ai_answer: str
    is_correct: bool