import logging

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.question import Question

log = logging.getLogger(__name__)


def get_random_question(round: str, value: str | None, db: Session) -> Question:
    """Fetch a random question filtered by round and value.

    Args:
        round: The Jeopardy round string e.g. 'Jeopardy!'.
        value: Dollar value e.g. '400'. Pass None for Final Jeopardy! to match NULL rows.
        db: SQLAlchemy database session.

    Returns:
        A randomly selected Question matching the filters.

    Raises:
        HTTPException: 404 if no matching question is found.
    """
    query = db.query(Question).filter(Question.round == round)

    if value is not None:
        query = query.filter(Question.value == value)
    else:
        query = query.filter(Question.value.is_(None))

    question = query.order_by(func.random()).first()

    if not question:
        log.warning("No question found for round=%r value=%r", round, value)
        raise HTTPException(status_code=404, detail="No question found for the given round and value")

    return question