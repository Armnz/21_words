from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from game.models import LeaderboardEntry, Session


def _create_session(*, score: int, status: str = "submitted") -> Session:
    now = timezone.now()
    return Session.objects.create(
        started_at=now - timedelta(seconds=60),
        expires_at=now,
        duration_seconds=60,
        target_words=21,
        status=status,
        current_ordinal=22 if status == "submitted" else 1,
        total_score=score,
        submitted_at=now if status == "submitted" else None,
        prompts=[],
        answers=[],
    )


def _seed_leaderboard(count: int, start_score: int = 1000) -> None:
    for i in range(count):
        session = _create_session(score=start_score - i, status="submitted")
        LeaderboardEntry.objects.create(
            session=session,
            player_name=f"Player {i}",
            score=session.total_score,
        )


@pytest.mark.django_db
def test_publish_success_for_top_100_candidate():
    session = _create_session(score=500, status="submitted")
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/publish/",
        data={"player_name": "Ieva"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["leaderboard_entry_id"] > 0
    assert body["rank"] == 1
    assert LeaderboardEntry.objects.filter(session=session).exists()


@pytest.mark.django_db
def test_publish_rejected_for_non_candidate():
    _seed_leaderboard(100, start_score=100)
    session = _create_session(score=0, status="submitted")
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/publish/",
        data={"player_name": "NotTop"},
        format="json",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not in top 100."
    assert not LeaderboardEntry.objects.filter(session=session).exists()


@pytest.mark.django_db
def test_publish_rejected_if_session_not_submitted():
    session = _create_session(score=100, status="active")
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/publish/",
        data={"player_name": "Late"},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Session is not submitted."


@pytest.mark.django_db
def test_publish_prunes_leaderboard_to_100_entries():
    _seed_leaderboard(100, start_score=200)
    session = _create_session(score=999, status="submitted")
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/publish/",
        data={"player_name": "TopOne"},
        format="json",
    )

    assert response.status_code == 201
    assert LeaderboardEntry.objects.count() == 100


@pytest.mark.django_db
def test_leaderboard_ordering_desc_score_then_created_at():
    session_a = _create_session(score=50, status="submitted")
    session_b = _create_session(score=50, status="submitted")
    session_c = _create_session(score=70, status="submitted")
    LeaderboardEntry.objects.create(session=session_a, player_name="A", score=50)
    LeaderboardEntry.objects.create(session=session_b, player_name="B", score=50)
    LeaderboardEntry.objects.create(session=session_c, player_name="C", score=70)
    client = APIClient()

    response = client.get("/api/v1/leaderboard/?limit=3")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["player_name"] for item in items] == ["C", "A", "B"]
