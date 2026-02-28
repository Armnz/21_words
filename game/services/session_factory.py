import logging
from datetime import timedelta

from django.utils import timezone

from game.models import Session
from game.selectors import get_random_prompts

logger = logging.getLogger(__name__)


class NotEnoughPromptsError(Exception):
    pass


def create_session(*, duration_seconds: int = 60, target_words: int = 21) -> Session:
    prompts = get_random_prompts(target_words)
    if len(prompts) < target_words:
        raise NotEnoughPromptsError("Not enough prompts to create a session.")

    started_at = timezone.now()
    expires_at = started_at + timedelta(seconds=duration_seconds)
    prompt_snapshots = [
        {
            "prompt_id": prompt.id,
            "description": prompt.description,
            "rule": prompt.rule,
            "valid_words_count": prompt.valid_words_count,
        }
        for prompt in prompts
    ]

    session = Session.objects.create(
        started_at=started_at,
        expires_at=expires_at,
        duration_seconds=duration_seconds,
        target_words=target_words,
        status="active",
        current_ordinal=1,
        total_score=0,
        prompts=prompt_snapshots,
        answers=[],
    )
    logger.info(
        "Created session=%s duration=%s target_words=%s",
        session.id,
        duration_seconds,
        target_words,
    )
    return session
