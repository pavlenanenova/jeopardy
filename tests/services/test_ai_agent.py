from unittest.mock import MagicMock, patch

from app.services.ai_agent import attempt_answer, AGENT_NAMES, SKILL_PROMPTS


@patch("app.services.gemini_client.generate_content")
def test_attempt_answer_returns_string(mock_generate):
    mock_generate.return_value = MagicMock(text="What is the Appian Way?")
    answer = attempt_answer(
        question="Built in 312 B.C. to link Rome & the South of Italy",
        category="HISTORY",
        skill_level="intermediate",
    )
    assert isinstance(answer, str)
    assert len(answer) > 0


@patch("app.services.gemini_client._base_model")
def test_attempt_answer_retries_on_failure_then_succeeds(mock_base_model):
    """Test that a single failure is retried and eventually succeeds."""
    mock_base_model.generate_content.side_effect = [
        Exception("Temporary API failure"),  # First attempt fails
        MagicMock(text="What is the Appian Way?"),  # Second attempt succeeds
    ]
    answer = attempt_answer(
        question="Built in 312 B.C. to link Rome & the South of Italy",
        category="HISTORY",
        skill_level="intermediate",
    )
    assert isinstance(answer, str)
    assert "Appian Way" in answer


@patch("app.services.ai_agent.generate_content")
def test_attempt_answer_passes_skill_prompt_to_model(mock_generate):
    mock_generate.return_value = MagicMock(text="What is Hydrogen?")
    attempt_answer(
        question="This element has the atomic number 1",
        category="SCIENCE",
        skill_level="expert",
    )
    # Mock was called with prompt as first arg and temperature as keyword arg
    assert mock_generate.called
    call_args = mock_generate.call_args[0][0]  # First positional arg is the prompt
    assert SKILL_PROMPTS["expert"] in call_args


@patch("app.services.ai_agent.generate_content")
def test_attempt_answer_strips_whitespace(mock_generate):
    mock_generate.return_value = MagicMock(text="  What is Hydrogen?  \n")
    answer = attempt_answer(
        question="This element has the atomic number 1",
        category="SCIENCE",
        skill_level="beginner",
    )
    assert answer == "What is Hydrogen?"


def test_agent_names_exist_for_all_skill_levels():
    for skill_level in ["beginner", "intermediate", "expert"]:
        assert skill_level in AGENT_NAMES
        assert isinstance(AGENT_NAMES[skill_level], str)


def test_skill_prompts_exist_for_all_skill_levels():
    for skill_level in ["beginner", "intermediate", "expert"]:
        assert skill_level in SKILL_PROMPTS
        assert isinstance(SKILL_PROMPTS[skill_level], str)