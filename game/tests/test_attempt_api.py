from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from game.models import Session, Word


def _prompt_snapshot(*, prompt_id: int, description: str, rule: dict, valid_words_count: int | None = None):
    return {
        "prompt_id": prompt_id,
        "description": description,
        "rule": rule,
        "valid_words_count": valid_words_count,
    }


def _create_session(
    *,
    prompts: list[dict],
    current_ordinal: int = 1,
    target_words: int = 21,
    expires_in_seconds: int = 60,
    answers: list[dict] | None = None,
    total_score: int = 0,
) -> Session:
    now = timezone.now()
    return Session.objects.create(
        started_at=now,
        expires_at=now + timedelta(seconds=expires_in_seconds),
        duration_seconds=60,
        target_words=target_words,
        status="active",
        current_ordinal=current_ordinal,
        total_score=total_score,
        prompts=prompts,
        answers=answers or [],
    )


@pytest.mark.django_db
def test_attempt_empty_word_returns_empty_error():
    session = _create_session(
        prompts=[_prompt_snapshot(prompt_id=1, description="Starts with a", rule={"type": "starts_with", "value": "a"})]
        * 21
    )
    client = APIClient()

    response = client.post(f"/api/v1/sessions/{session.id}/attempt/", data={"word": "   "}, format="json")

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is False
    assert body["error_code"] == "empty"
    session.refresh_from_db()
    assert session.current_ordinal == 1
    assert session.total_score == 0


@pytest.mark.django_db
def test_attempt_dictionary_miss_returns_not_in_dictionary():
    session = _create_session(
        prompts=[_prompt_snapshot(prompt_id=1, description="Starts with a", rule={"type": "starts_with", "value": "a"})]
        * 21
    )
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/attempt/",
        data={"word": "atvars"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["error_code"] == "not_in_dictionary"


@pytest.mark.django_db
def test_attempt_duplicate_detection():
    Word.objects.create(word="aplis")
    session = _create_session(
        prompts=[_prompt_snapshot(prompt_id=1, description="Starts with a", rule={"type": "starts_with", "value": "a"})]
        * 21,
        answers=[
            {
                "ordinal": 1,
                "prompt_id": 1,
                "word": "Aplis",
                "normalized_word": "aplis",
                "points_index": 1,
                "points_length": 9,
                "points_total": 10,
                "created_at": timezone.now().isoformat(),
            }
        ],
    )
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/attempt/",
        data={"word": "Aplis"},
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["error_code"] == "duplicate"


@pytest.mark.django_db
def test_attempt_rule_matching_starts_with_and_contains_diacritic():
    Word.objects.create(word="aplis")
    Word.objects.create(word="šalle")

    starts_with_session = _create_session(
        prompts=[_prompt_snapshot(prompt_id=1, description="Starts with a", rule={"type": "starts_with", "value": "a"})]
        * 21
    )
    diacritic_session = _create_session(
        prompts=[
            _prompt_snapshot(
                prompt_id=2,
                description="Contains diacritic",
                rule={"type": "contains_diacritic"},
            )
        ]
        * 21
    )
    client = APIClient()

    starts_response = client.post(
        f"/api/v1/sessions/{starts_with_session.id}/attempt/",
        data={"word": "Aplis"},
        format="json",
    )
    diacritic_response = client.post(
        f"/api/v1/sessions/{diacritic_session.id}/attempt/",
        data={"word": "Šalle"},
        format="json",
    )

    assert starts_response.status_code == 200
    assert starts_response.json()["is_valid"] is True
    assert diacritic_response.status_code == 200
    assert diacritic_response.json()["is_valid"] is True


@pytest.mark.django_db
def test_attempt_scoring_known_example():
    Word.objects.create(word="wastes")
    prompts = [_prompt_snapshot(prompt_id=i, description=f"P{i}", rule={"type": "starts_with", "value": "w"}) for i in range(1, 22)]
    session = _create_session(prompts=prompts, current_ordinal=5, total_score=0)
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/attempt/",
        data={"word": "WASTES"},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["just_scored"] == {"index_points": 5, "length_points": 15, "total": 20}
    assert body["total_score"] == 20


@pytest.mark.django_db
def test_attempt_completion_applies_time_bonus_and_submits_session():
    Word.objects.create(word="zirgs")
    prompts = [_prompt_snapshot(prompt_id=i, description=f"P{i}", rule={"type": "starts_with", "value": "z"}) for i in range(1, 22)]
    answers = [
        {
            "ordinal": i,
            "prompt_id": i,
            "word": f"z{i}",
            "normalized_word": f"z{i}",
            "points_index": i,
            "points_length": 1,
            "points_total": i + 1,
            "created_at": timezone.now().isoformat(),
        }
        for i in range(1, 21)
    ]
    session = _create_session(
        prompts=prompts,
        current_ordinal=21,
        target_words=21,
        expires_in_seconds=30,
        answers=answers,
        total_score=210,
    )
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/attempt/",
        data={"word": "Zirgs"},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["is_finished"] is True
    assert body["finished_reason"] == "completed"
    assert body["time_left_ms"] > 0
    assert body["total_score"] > (210 + 33)

    session.refresh_from_db()
    assert session.status == "submitted"
    assert session.current_ordinal == 22
    assert session.time_left_ms is not None


@pytest.mark.django_db
def test_attempt_expired_session_returns_409_and_marks_expired():
    Word.objects.create(word="aplis")
    session = _create_session(
        prompts=[_prompt_snapshot(prompt_id=1, description="Starts with a", rule={"type": "starts_with", "value": "a"})]
        * 21,
        expires_in_seconds=-1,
    )
    client = APIClient()

    response = client.post(
        f"/api/v1/sessions/{session.id}/attempt/",
        data={"word": "aplis"},
        format="json",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Session expired."
    session.refresh_from_db()
    assert session.status == "expired"
