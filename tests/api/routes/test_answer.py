from unittest.mock import patch


@patch("app.api.routes.answer.verify_answer", return_value=(True, "That is correct! Copernicus proposed the heliocentric theory."))
def test_verify_correct_answer(mock_verify, client):
    response = client.post("/verify-answer/", json={"question_id": 1, "user_answer": "Copernicus"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["ai_response"] != ""


@patch("app.api.routes.answer.verify_answer", return_value=(False, "Sorry, the correct answer was Copernicus."))
def test_verify_incorrect_answer(mock_verify, client):
    response = client.post("/verify-answer/", json={"question_id": 1, "user_answer": "Galileo"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is False


def test_verify_answer_invalid_question_id_returns_404(client):
    response = client.post("/verify-answer/", json={"question_id": 9999, "user_answer": "Copernicus"})
    assert response.status_code == 404


def test_verify_answer_missing_fields_returns_422(client):
    response = client.post("/verify-answer/", json={"question_id": 1})
    assert response.status_code == 422


@patch("app.api.routes.answer.verify_answer", side_effect=Exception("Gemini unavailable"))
def test_verify_answer_ai_failure_returns_503(mock_verify, client):
    response = client.post("/verify-answer/", json={"question_id": 1, "user_answer": "Copernicus"})
    assert response.status_code == 503