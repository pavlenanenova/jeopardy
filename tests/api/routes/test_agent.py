from unittest.mock import patch


@patch("app.services.ai_verifier.verify_answer", return_value=(True, "Correct!"))
@patch("app.api.routes.agent.attempt_answer", return_value="What is Copernicus?")
def test_agent_play_returns_valid_response(mock_attempt, mock_verify, client):
    response = client.post("/agent-play/", json={"round": "Jeopardy!", "value": "$200", "skill_level": "intermediate"})
    assert response.status_code == 200
    data = response.json()
    assert "agent_name" in data
    assert "question" in data
    assert "ai_answer" in data
    assert "is_correct" in data


@patch("app.services.ai_verifier.verify_answer", return_value=(True, "Correct!"))
@patch("app.api.routes.agent.attempt_answer", return_value="What is Copernicus?")
def test_agent_play_beginner_skill_level(mock_attempt, mock_verify, client):
    response = client.post("/agent-play/", json={"round": "Jeopardy!", "value": "$200", "skill_level": "beginner"})
    assert response.status_code == 200
    assert response.json()["agent_name"] == "Rookie-Bot"


@patch("app.services.ai_verifier.verify_answer", return_value=(True, "Correct!"))
@patch("app.api.routes.agent.attempt_answer", return_value="What is Copernicus?")
def test_agent_play_expert_skill_level(mock_attempt, mock_verify, client):
    response = client.post("/agent-play/", json={"round": "Jeopardy!", "value": "$200", "skill_level": "expert"})
    assert response.status_code == 200
    assert response.json()["agent_name"] == "Master-Bot"


@patch("app.services.ai_verifier.verify_answer", return_value=(True, "Correct!"))
@patch("app.api.routes.agent.attempt_answer", return_value="What is Vatican City?")
def test_agent_play_final_jeopardy_without_value(mock_attempt, mock_verify, client):
    response = client.post("/agent-play/", json={"round": "Final Jeopardy!"})
    assert response.status_code == 200
    data = response.json()
    assert "agent_name" in data
    assert "question" in data
    assert "ai_answer" in data
    assert "is_correct" in data


def test_agent_play_invalid_round_returns_422(client):
    response = client.post("/agent-play/", json={"round": "Invalid Round!", "value": "$200"})
    assert response.status_code == 422


def test_agent_play_invalid_skill_level_returns_422(client):
    response = client.post("/agent-play/", json={"round": "Jeopardy!", "value": "$200", "skill_level": "godlike"})
    assert response.status_code == 422


@patch("app.api.routes.agent.attempt_answer", side_effect=Exception("Gemini unavailable"))
def test_agent_play_ai_failure_returns_503(mock_attempt, client):
    response = client.post("/agent-play/", json={"round": "Jeopardy!", "value": "$200"})
    assert response.status_code == 503