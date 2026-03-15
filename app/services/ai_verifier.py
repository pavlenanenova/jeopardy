import logging

from app.services.gemini_client import model

log = logging.getLogger(__name__)


def verify_answer(question: str, correct_answer: str, user_answer: str) -> tuple[bool, str]:
    """Use Gemini to check whether the user's answer matches the correct answer.

    Accepts free-text answers including spelling mistakes and Jeopardy-style phrasing
    such as 'What is X' or 'Who is X'.

    Args:
        question: The Jeopardy clue text shown on the board.
        correct_answer: The expected answer stored in the database.
        user_answer: The free-text answer provided by the user or agent.

    Returns:
        A tuple of (is_correct, ai_response) where is_correct is a bool and
        ai_response is a one-sentence explanation in the style of Alex Trebek.

    Raises:
        RuntimeError: If the Gemini API call fails.
    """
    prompt = (
        f"You are Alex Trebek hosting Jeopardy. A contestant has just given their answer.\n\n"
        f"Question: {question}\n"
        f"Correct answer: {correct_answer}\n"
        f"Contestant's answer: {user_answer}\n\n"
        f"Rules:\n"
        f"- Accept answers that are close enough, including minor spelling mistakes\n"
        f"- Accept answers phrased as 'The answer is X' or 'Who is X' etc.\n"
        f"- Respond with 'CORRECT' or 'INCORRECT' on the first line\n"
        f"- On the second line, respond in character as Alex Trebek would on the show — \n"
        f"  warm and encouraging for correct answers, gently sympathetic for wrong ones. \n"
        f"  Keep it to one sentence. Reference the correct answer naturally."
    )

    log.debug("Calling Gemini to verify answer")
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        log.error("Gemini API call failed: %s", e)
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    response_text = response.text.strip()
    lines = response_text.splitlines()

    first_line = lines[0].strip().upper() if lines else ""
    if first_line not in ("CORRECT", "INCORRECT"):
        log.error("Unexpected Gemini response format, first line was: %r", first_line)
        raise RuntimeError(f"Unexpected response format from Gemini: {first_line!r}")

    is_correct = first_line == "CORRECT"
    ai_response = lines[1].strip() if len(lines) > 1 else response_text

    log.debug("Parsed response: is_correct=%s ai_response=%r", is_correct, ai_response)
    return is_correct, ai_response