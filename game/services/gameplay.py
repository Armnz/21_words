import logging
from datetime import datetime

from django.utils import timezone

from game.models import Session, Word
from game.selectors import get_top_100_candidate
from game.services.scoring import calculate_time_bonus, calculate_word_points
from game.services.validation import matches_rule, normalize_word

logger = logging.getLogger(__name__)


class SessionExpiredError(Exception):
    pass


class SessionNotActiveError(Exception):
    pass


def get_current_prompt_payload(session: Session) -> dict | None:
    if session.status != "active":
        return None

    idx = session.current_ordinal - 1
    if idx < 0 or idx >= len(session.prompts):
        return None

    current = session.prompts[idx]
    return {
        "ordinal": session.current_ordinal,
        "prompt_id": current["prompt_id"],
        "description": current["description"],
        "rule": current["rule"],
        "valid_words_count": current.get("valid_words_count"),
    }


def _get_time_left_ms(*, expires_at: datetime, now: datetime) -> int:
    delta_ms = int((expires_at - now).total_seconds() * 1000)
    return max(0, delta_ms)


def _make_response(
    *,
    session: Session,
    now: datetime,
    is_valid: bool,
    error_code: str | None,
    just_scored: dict | None,
    is_finished: bool,
    finished_reason: str | None,
) -> dict:
    is_candidate, threshold = get_top_100_candidate(session.total_score)
    time_left_ms = session.time_left_ms
    if time_left_ms is None and session.status == "active":
        time_left_ms = _get_time_left_ms(expires_at=session.expires_at, now=now)

    return {
        "session_id": str(session.id),
        "is_valid": is_valid,
        "error_code": error_code,
        "total_score": session.total_score,
        "current_ordinal": session.current_ordinal,
        "target_words": session.target_words,
        "time_left_ms": time_left_ms,
        "just_scored": just_scored,
        "prompt": get_current_prompt_payload(session),
        "is_finished": is_finished,
        "finished_reason": finished_reason,
        "leaderboard": {
            "is_top_100_candidate": is_candidate,
            "min_score_for_top_100": threshold,
        },
    }


def process_attempt(*, session: Session, raw_word: str, now: datetime | None = None) -> dict:
    now = now or timezone.now()

    if session.status == "submitted":
        raise SessionNotActiveError("Session already submitted.")
    if session.status == "expired":
        raise SessionExpiredError("Session expired.")

    if now > session.expires_at:
        session.status = "expired"
        session.save(update_fields=["status"])
        raise SessionExpiredError("Session expired.")

    prompt_payload = get_current_prompt_payload(session)
    if prompt_payload is None:
        raise SessionNotActiveError("No active prompt available for this session.")

    normalized_word = normalize_word(raw_word or "")
    if not normalized_word:
        return _make_response(
            session=session,
            now=now,
            is_valid=False,
            error_code="empty",
            just_scored=None,
            is_finished=False,
            finished_reason=None,
        )

    used_words = {answer.get("normalized_word") for answer in session.answers}
    if normalized_word in used_words:
        return _make_response(
            session=session,
            now=now,
            is_valid=False,
            error_code="duplicate",
            just_scored=None,
            is_finished=False,
            finished_reason=None,
        )

    if not Word.objects.filter(word=normalized_word).exists():
        return _make_response(
            session=session,
            now=now,
            is_valid=False,
            error_code="not_in_dictionary",
            just_scored=None,
            is_finished=False,
            finished_reason=None,
        )

    if not matches_rule(normalized_word, prompt_payload["rule"]):
        return _make_response(
            session=session,
            now=now,
            is_valid=False,
            error_code="rule_mismatch",
            just_scored=None,
            is_finished=False,
            finished_reason=None,
        )

    points = calculate_word_points(ordinal=session.current_ordinal, word_length=len(normalized_word))
    answer_row = {
        "ordinal": session.current_ordinal,
        "prompt_id": prompt_payload["prompt_id"],
        "prompt_description": prompt_payload["description"],
        "word": raw_word,
        "normalized_word": normalized_word,
        "points_index": points["index_points"],
        "points_length": points["length_points"],
        "points_total": points["total"],
        "created_at": now.isoformat(),
    }
    session.answers = [*session.answers, answer_row]
    session.total_score += points["total"]
    session.current_ordinal += 1

    is_finished = False
    finished_reason = None
    if session.current_ordinal > session.target_words:
        is_finished = True
        finished_reason = "completed"
        time_left_ms = _get_time_left_ms(expires_at=session.expires_at, now=now)
        bonus = calculate_time_bonus(time_left_ms)
        session.total_score += bonus
        session.time_left_ms = time_left_ms
        session.submitted_at = now
        session.status = "submitted"

    session.save(
        update_fields=[
            "answers",
            "total_score",
            "current_ordinal",
            "status",
            "time_left_ms",
            "submitted_at",
        ]
    )
    logger.info(
        "Attempt accepted session=%s ordinal=%s score=%s status=%s",
        session.id,
        answer_row["ordinal"],
        session.total_score,
        session.status,
    )
    return _make_response(
        session=session,
        now=now,
        is_valid=True,
        error_code=None,
        just_scored=points,
        is_finished=is_finished,
        finished_reason=finished_reason,
    )
