import logging

from app.services.gemini_client import model

log = logging.getLogger(__name__)

SKILL_PROMPTS = {
    "beginner": (
        "You are a Jeopardy contestant with limited general knowledge. "
        "You often get answers wrong, give vague responses, or confuse similar facts. "
        "Attempt to answer but make plausible mistakes about a third of the time."
    ),
    "intermediate": (
        "You are a Jeopardy contestant with decent general knowledge. "
        "You usually get answers right but occasionally make mistakes or misremember details."
    ),
    "expert": (
        "You are an expert Jeopardy contestant with deep knowledge across all topics. "
        "You almost always answer correctly and precisely."
    ),
}

AGENT_NAMES = {
    "beginner": "Rookie-Bot",
    "intermediate": "AI-Bot",
    "expert": "Master-Bot",
}


def attempt_answer(question: str, category: str, skill_level: str) -> str:
    """Use Gemini to attempt a Jeopardy answer at the given skill level.

    Args:
        question: The Jeopardy clue text shown on the board.
        category: The question category (e.g. HISTORY). Included in the prompt for context.
        skill_level: One of 'beginner', 'intermediate', 'expert'. Controls how accurately the agent answers.

    Returns:
        The agent's answer as a string, phrased as 'What is X' or 'Who is X'.

    Raises:
        RuntimeError: If the Gemini API call fails.
    """
    prompt = (
        f"{SKILL_PROMPTS[skill_level]}\n\n"
        f"Category: {category}\n"
        f"Question: {question}\n\n"
        f"Give only your answer, nothing else. "
        f"Answer in the form 'What is X' or 'Who is X' as in real Jeopardy."
    )

    log.debug("Calling Gemini for skill_level=%s", skill_level)
    try:
        response = model.generate_content(prompt)
    except Exception as e:
        log.error("Gemini API call failed: %s", e)
        raise RuntimeError(f"Gemini API call failed: {e}") from e

    return response.text.strip()