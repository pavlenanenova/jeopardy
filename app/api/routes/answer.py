import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.question import Question
from app.schemas.answer import AnswerRequest, AnswerResponse
from app.services.ai_verifier import verify_answer

log = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/verify-answer/",
    response_model=AnswerResponse,
    summary="Verify a user's answer",
    description=(
        "Checks whether a user's free-text answer is correct using AI. "
        "Handles spelling mistakes, partial answers, and answers phrased as 'What is X' or 'Who is X'. "
        "Use the **question_id** returned from the GET /question/ endpoint."
    ),
)
def verify_user_answer(body: AnswerRequest, db: Session = Depends(get_db)):
    log.info("POST /verify-answer/ question_id=%d", body.question_id)
    question = db.query(Question).filter(Question.id == body.question_id).first()

    if not question:
        log.warning("Question id=%d not found", body.question_id)
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        is_correct, ai_response = verify_answer(
            question=question.question,
            correct_answer=question.answer,
            user_answer=body.user_answer,
        )
        log.info("Answer verified for question_id=%d is_correct=%s", body.question_id, is_correct)
    except Exception as e:
        log.error("AI verification failed for question_id=%d: %s", body.question_id, e)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI service is temporarily unavailable. Please try again later.")

    return AnswerResponse(is_correct=is_correct, ai_response=ai_response)