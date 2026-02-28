import pytest
from rest_framework.test import APIClient

from game.models import Prompt, Session


def _create_prompts(count: int) -> None:
    for i in range(1, count + 1):
        Prompt.objects.create(
            description=f"Prompt {i}",
            rule={"type": "starts_with", "value": "a"},
            valid_words_count=10,
        )


@pytest.mark.django_db
def test_create_session_creates_21_prompt_snapshots():
    _create_prompts(21)
    client = APIClient()

    response = client.post("/api/v1/sessions/", data={}, format="json")

    assert response.status_code == 201
    body = response.json()
    assert body["current_ordinal"] == 1
    assert body["target_words"] == 21
    assert body["prompt"]["ordinal"] == 1
    assert body["started_at"]
    assert body["expires_at"]
    assert body["server_time"]

    session = Session.objects.get(id=body["id"])
    assert session.status == "active"
    assert len(session.prompts) == 21
    assert session.answers == []


@pytest.mark.django_db
def test_create_session_returns_503_if_not_enough_prompts():
    _create_prompts(20)
    client = APIClient()

    response = client.post("/api/v1/sessions/", data={}, format="json")

    assert response.status_code == 503
    assert "detail" in response.json()


@pytest.mark.django_db
def test_get_session_returns_current_prompt_and_answers():
    _create_prompts(21)
    client = APIClient()
    create_response = client.post("/api/v1/sessions/", data={}, format="json")
    session_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/sessions/{session_id}/")

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["id"] == session_id
    assert body["status"] == "active"
    assert body["current_ordinal"] == 1
    assert body["prompt"]["ordinal"] == 1
    assert body["answers"] == []
