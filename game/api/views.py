from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from game.models import Session
from game.selectors import get_leaderboard_entries
from game.services.gameplay import (
    SessionExpiredError,
    SessionNotActiveError,
    get_current_prompt_payload,
    process_attempt,
)
from game.services.leaderboard import (
    AlreadyPublishedError,
    InvalidPlayerNameError,
    NotTop100Error,
    SessionNotSubmittedError,
    publish_session,
)
from game.services.session_factory import NotEnoughPromptsError, create_session


def _serialize_session(session: Session) -> dict:
    return {
        "id": str(session.id),
        "status": session.status,
        "started_at": session.started_at,
        "expires_at": session.expires_at,
        "duration_seconds": session.duration_seconds,
        "target_words": session.target_words,
        "current_ordinal": session.current_ordinal,
        "total_score": session.total_score,
        "submitted_at": session.submitted_at,
        "time_left_ms": session.time_left_ms,
        "answers": session.answers,
        "prompt": get_current_prompt_payload(session),
    }


@api_view(["GET"])
def health_check(request):
    """Health check endpoint."""
    return Response({"status": "ok"})


class SessionCreateView(APIView):
    def post(self, request):
        try:
            session = create_session(duration_seconds=60, target_words=21)
        except NotEnoughPromptsError:
            return Response(
                {"detail": "At least 21 prompts are required before starting a game."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "id": str(session.id),
                "server_time": timezone.now(),
                "started_at": session.started_at,
                "expires_at": session.expires_at,
                "duration_seconds": session.duration_seconds,
                "target_words": session.target_words,
                "current_ordinal": session.current_ordinal,
                "prompt": get_current_prompt_payload(session),
            },
            status=status.HTTP_201_CREATED,
        )


class SessionDetailView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(Session, id=session_id)
        return Response(_serialize_session(session), status=status.HTTP_200_OK)


class SessionAttemptView(APIView):
    def post(self, request, session_id):
        with transaction.atomic():
            session = get_object_or_404(Session.objects.select_for_update(), id=session_id)
            try:
                payload = process_attempt(session=session, raw_word=request.data.get("word", ""))
            except SessionExpiredError:
                return Response({"detail": "Session expired."}, status=status.HTTP_409_CONFLICT)
            except SessionNotActiveError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(payload, status=status.HTTP_200_OK)


class SessionPublishView(APIView):
    def post(self, request, session_id):
        with transaction.atomic():
            session = get_object_or_404(Session.objects.select_for_update(), id=session_id)
            try:
                entry, rank = publish_session(
                    session=session,
                    player_name=request.data.get("player_name", ""),
                )
            except InvalidPlayerNameError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            except SessionNotSubmittedError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
            except AlreadyPublishedError:
                return Response(
                    {"detail": "Session already published."},
                    status=status.HTTP_409_CONFLICT,
                )
            except NotTop100Error:
                return Response({"detail": "Not in top 100."}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {"leaderboard_entry_id": entry.id, "rank": rank},
            status=status.HTTP_201_CREATED,
        )


class LeaderboardView(APIView):
    def get(self, request):
        limit_raw = request.query_params.get("limit", "100")
        try:
            limit = int(limit_raw)
        except ValueError:
            limit = 100
        limit = max(1, min(limit, 100))

        entries = get_leaderboard_entries(limit=limit)
        items = [
            {
                "rank": idx,
                "player_name": entry.player_name,
                "score": entry.score,
                "created_at": entry.created_at,
            }
            for idx, entry in enumerate(entries, start=1)
        ]
        return Response({"items": items}, status=status.HTTP_200_OK)
