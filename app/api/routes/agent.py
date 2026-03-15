import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.utils import get_random_question
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.ai_agent import AGENT_NAMES, attempt_answer
from app.services.ai_verifier import verify_answer

log = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/agent-play/",
    response_model=AgentResponse,
    summary="Let an AI agent play a question",
    description=(
        "An AI agent selects and attempts to answer a random Jeopardy question. "
        "The agent's skill level controls how often it gets the answer right. "
        "Available skill levels: **beginner** (makes frequent mistakes), "
        "**intermediate** (occasionally wrong), **expert** (almost always correct). "
        "For Final Jeopardy! omit the value field."
    ),
)
def agent_play(body: AgentRequest, db: Session = Depends(get_db)):
    log.info("POST /agent-play/ round=%s value=%s skill_level=%s", body.round.value, body.value, body.skill_level.value)
    question = get_random_question(round=body.round.value, value=body.value, db=db)
    log.info("Agent attempting question id=%d", question.id)

    try:
        ai_answer = attempt_answer(
            question=question.question,
            category=question.category,
            skill_level=body.skill_level.value,
        )
        is_correct, _ = verify_answer(
            question=question.question,
            correct_answer=question.answer,
            user_answer=ai_answer,
        )
        log.info("Agent answered question id=%d is_correct=%s", question.id, is_correct)
    except Exception as e:
        log.error("AI agent failed for question id=%d: %s", question.id, e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service is temporarily unavailable. Please try again later.")

    return AgentResponse(
        agent_name=AGENT_NAMES[body.skill_level.value],
        question=question.question,
        ai_answer=ai_answer,
        is_correct=is_correct,
    )