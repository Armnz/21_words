import logging

from game.models import LeaderboardEntry, Session
from game.selectors import get_rank_for_entry, get_top_100_candidate, leaderboard_queryset

logger = logging.getLogger(__name__)


class PublishError(Exception):
    pass


class SessionNotSubmittedError(PublishError):
    pass


class InvalidPlayerNameError(PublishError):
    pass


class AlreadyPublishedError(PublishError):
    pass


class NotTop100Error(PublishError):
    pass


def _prune_leaderboard(max_size: int = 100) -> None:
    ranked_ids = list(leaderboard_queryset().values_list("id", flat=True))
    if len(ranked_ids) <= max_size:
        return

    stale_ids = ranked_ids[max_size:]
    LeaderboardEntry.objects.filter(id__in=stale_ids).delete()


def publish_session(*, session: Session, player_name: str) -> tuple[LeaderboardEntry, int]:
    if session.status != "submitted":
        raise SessionNotSubmittedError("Session is not submitted.")

    normalized_name = (player_name or "").strip()
    if not 1 <= len(normalized_name) <= 64:
        raise InvalidPlayerNameError("Player name must be 1 to 64 characters.")

    if LeaderboardEntry.objects.filter(session=session).exists():
        raise AlreadyPublishedError("Session already published.")

    is_candidate, _ = get_top_100_candidate(session.total_score)
    if not is_candidate:
        raise NotTop100Error("Not in top 100.")

    entry = LeaderboardEntry.objects.create(
        session=session,
        player_name=normalized_name,
        score=session.total_score,
    )
    _prune_leaderboard(max_size=100)

    rank = get_rank_for_entry(entry.id)
    if rank is None:
        raise NotTop100Error("Not in top 100.")

    logger.info(
        "Published leaderboard entry session=%s entry_id=%s score=%s rank=%s",
        session.id,
        entry.id,
        session.total_score,
        rank,
    )
    return entry, rank
