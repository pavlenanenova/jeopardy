import pytest
from unittest.mock import MagicMock, patch

from app.services.ai_verifier import verify_answer


@patch("app.services.gemini_client.model")
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


@patch("app.services.gemini_client.model")
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


@patch("app.services.gemini_client.model")
def test_verify_answer_with_spelling_mistake(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="CORRECT\nDespite the spelling, that clearly refers to Copernicus."
    )
    is_correct, ai_response = verify_answer(
        question="Galileo was under house arrest for espousing this man's theory",
        correct_answer="Copernicus",
        user_answer="Copernics",
    )
    assert is_correct is True


@patch("app.services.gemini_client.model")
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


@patch("app.services.gemini_client.model")
def test_verify_answer_fallback_when_no_second_line(mock_model):
    mock_model.generate_content.return_value = MagicMock(text="CORRECT")
    is_correct, ai_response = verify_answer(
        question="Some question",
        correct_answer="Some answer",
        user_answer="Some answer",
    )
    assert is_correct is True
    assert ai_response == "CORRECT"


@patch("app.services.gemini_client.model")
def test_verify_answer_raises_on_api_failure(mock_model):
    mock_model.generate_content.side_effect = Exception("Rate limit exceeded")
    with pytest.raises(RuntimeError, match="Gemini API call failed"):
        verify_answer(
            question="Some question",
            correct_answer="Some answer",
            user_answer="Some answer",
        )


@patch("app.services.gemini_client.model")
def test_verify_answer_case_insensitive_correct(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="correct\nWell done!"
    )
    is_correct, _ = verify_answer(
        question="Some question",
        correct_answer="Some answer",
        user_answer="Some answer",
    )
    assert is_correct is True


@patch("app.services.gemini_client.model")
def test_verify_answer_strips_whitespace_from_response(mock_model):
    mock_model.generate_content.return_value = MagicMock(
        text="  CORRECT  \n  Well done, that is right!  "
    )
    is_correct, ai_response = verify_answer(
        question="Some question",
        correct_answer="Some answer",
        user_answer="Some answer",
    )
    assert is_correct is True
    assert ai_response == "Well done, that is right!"