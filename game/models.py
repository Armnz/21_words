import uuid

from django.db import models


class Word(models.Model):
    """
    A canonical word entry.
    Stores normalized word forms only (no diacritics variations).
    """

    id = models.BigAutoField(primary_key=True)
    word = models.TextField(unique=True)

    def __str__(self):
        return self.word

    class Meta:
        ordering = ["word"]


class Prompt(models.Model):
    """
    A game prompt/rule that players must find words matching.
    """

    id = models.BigAutoField(primary_key=True)
    description = models.TextField()
    rule = models.JSONField()  # e.g. {"type":"starts_with","value":"a"}
    valid_words_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ["id"]


class Session(models.Model):
    """
    A game session instance.
    Stores prompt and answer snapshots as JSONB to freeze state at play time.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("submitted", "Submitted"),
        ("expired", "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    duration_seconds = models.PositiveIntegerField(default=60)
    target_words = models.PositiveIntegerField(default=21)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    current_ordinal = models.PositiveIntegerField(default=1)  # next prompt ordinal (1..21)
    total_score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_left_ms = models.IntegerField(null=True, blank=True)  # time remaining when submitted

    # snapshot of 21 prompts and their rules captured at session start
    prompts = models.JSONField(
        default=dict
    )  # dict keyed by ordinal or list of {prompt_id, description, rule, valid_words_count}
    # answers = list of successful words with scoring metadata
    answers = models.JSONField(default=list)

    def __str__(self):
        return f"Session {self.id} ({self.status})"

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["status"]),
        ]


class LeaderboardEntry(models.Model):
    """
    Leaderboard entry tied to a session result.
    Supports ranking by score (desc) and then by created_at (asc).
    """

    id = models.BigAutoField(primary_key=True)
    session = models.OneToOneField(
        Session, on_delete=models.CASCADE, related_name="leaderboard_entry"
    )
    player_name = models.CharField(max_length=64)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player_name} - {self.score}"

    class Meta:
        ordering = ["-score", "created_at"]
        indexes = [
            models.Index(fields=["-score", "created_at"]),
        ]
