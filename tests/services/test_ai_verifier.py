from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_verifier import verify_answer


@patch("app.services.ai_verifier.model")
def test_verify_correct_answer(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="CORRECT\nWell done! Copernicus proposed the heliocentric theory."
    )
    is_correct, ai_response = verify_answer(
        question="Galileo was under house arrest for espousing this man's theory",
        correct_answer="Copernicus",
        user_answer="Copernicus",
    )
    assert is_correct is True
    assert "Copernicus" in ai_response


@patch("app.services.ai_verifier.model")
def test_verify_incorrect_answer(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="INCORRECT\nSorry, the correct answer was Copernicus, not Galileo."
    )
    is_correct, ai_response = verify_answer(
        question="Galileo was under house arrest for espousing this man's theory",
        correct_answer="Copernicus",
        user_answer="Galileo",
    )
    assert is_correct is False
    assert ai_response != ""


@patch("app.services.ai_verifier.model")
def test_verify_answer_with_spelling_mistake(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="CORRECT\nDespite the spelling, that clearly refers to Copernicus."
    )
    is_correct, _ = verify_answer(
        question="Galileo was under house arrest for espousing this man's theory",
        correct_answer="Copernicus",
        user_answer="Copernics",
    )
    assert is_correct is True


@patch("app.services.ai_verifier.model")
def test_verify_answer_with_who_is_phrasing(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="CORRECT\nThat is right, Copernicus proposed the heliocentric model."
    )
    is_correct, _ = verify_answer(
        question="Galileo was under house arrest for espousing this man's theory",
        correct_answer="Copernicus",
        user_answer="Who is Copernicus?",
    )
    assert is_correct is True


@patch("app.services.ai_verifier.model")
def test_verify_answer_fallback_when_no_second_line(mock_model):
    mock_model.generate_content.return_value = MagicMock(text="CORRECT")
    is_correct, ai_response = verify_answer(
        question="Some question",
        correct_answer="Some answer",
        user_answer="Some answer",
    )
    assert is_correct is True
    assert ai_response == "CORRECT"


@patch("app.services.gemini_client._base_model")
def test_verify_answer_retries_on_failure_then_succeeds(mock_base_model):
    """Test that a single failure is retried and eventually succeeds."""
    mock_base_model.generate_content.side_effect = [
        Exception("Temporary failure"),  # First attempt fails
        MagicMock(text="CORRECT\nExcellent answer!"),  # Second attempt succeeds
    ]
    is_correct, ai_response = verify_answer(
        question="Some question",
        correct_answer="Correct answer",
        user_answer="Correct answer",
    )
    assert is_correct is True
    assert "Excellent" in ai_response


@patch("app.services.ai_verifier.model")
def test_verify_answer_raises_on_api_failure(mock_model):
    mock_model.generate_content.side_effect = Exception("Rate limit exceeded")
    with pytest.raises(Exception):
        verify_answer(
            question="Some question",
            correct_answer="Some answer",
            user_answer="Some answer",
        )