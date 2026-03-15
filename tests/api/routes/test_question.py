def test_get_question_returns_valid_response(client):
    response = client.get("/question/", params={"round": "Jeopardy!", "value": "$200"})
    assert response.status_code == 200
    data = response.json()
    assert data["round"] == "Jeopardy!"
    assert data["value"] == "$200"
    assert "question_id" in data
    assert "category" in data
    assert "question" in data


def test_get_question_double_jeopardy(client):
    response = client.get("/question/", params={"round": "Double Jeopardy!", "value": "$400"})
    assert response.status_code == 200
    data = response.json()
    assert data["round"] == "Double Jeopardy!"


def test_get_final_jeopardy_without_value(client):
    response = client.get("/question/", params={"round": "Final Jeopardy!"})
    assert response.status_code == 200
    data = response.json()
    assert data["round"] == "Final Jeopardy!"
    assert data["value"] is None


def test_get_question_invalid_round_returns_422(client):
    response = client.get("/question/", params={"round": "Invalid Round!", "value": "$200"})
    assert response.status_code == 422


def test_get_question_invalid_value_returns_404(client):
    response = client.get("/question/", params={"round": "Jeopardy!", "value": "$999"})
    assert response.status_code == 404


def test_get_question_missing_round_returns_422(client):
    response = client.get("/question/", params={"value": "$200"})
    assert response.status_code == 422