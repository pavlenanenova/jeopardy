import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.utils import get_random_question
from app.models.enums import Round
from app.schemas.question import QuestionResponse

log = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/question/",
    response_model=QuestionResponse,
    summary="Get a random question",
    description=(
        "Returns a random Jeopardy question filtered by round and value. "
        "For Final Jeopardy! omit the value parameter. "
        "Available rounds: **Jeopardy!**, **Double Jeopardy!**, **Final Jeopardy!**. "
        "Available values: **$200**, **$400**, **$600**, **$800**, **$1000**, **$1200**."
    ),
)
def get_question(
    round: Round = Query(..., description="Jeopardy!, Double Jeopardy!, or Final Jeopardy!"),
    value: str | None = Query(None, description="e.g. $200. Not required for Final Jeopardy!"),
    db: Session = Depends(get_db),
):
    log.info("GET /question/ round=%s value=%s", round.value, value)
    question = get_random_question(round=round.value, value=value, db=db)
    log.info("Returning question id=%d", question.id)

    return QuestionResponse(
        question_id=question.id,
        round=question.round,
        category=question.category,
        value=question.value,
        question=question.question,
    )