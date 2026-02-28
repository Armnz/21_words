import random

from game.models import LeaderboardEntry, Prompt


def get_random_prompts(limit: int) -> list[Prompt]:
    prompt_ids = list(Prompt.objects.values_list("id", flat=True))
    if len(prompt_ids) < limit:
        return []

    selected_ids = random.sample(prompt_ids, limit)
    prompts_by_id = {prompt.id: prompt for prompt in Prompt.objects.filter(id__in=selected_ids)}
    return [prompts_by_id[prompt_id] for prompt_id in selected_ids]


def leaderboard_queryset():
    return LeaderboardEntry.objects.order_by("-score", "created_at")


def get_leaderboard_entries(limit: int = 100):
    return leaderboard_queryset()[:limit]


def get_top_100_threshold() -> int | None:
    scores = list(get_leaderboard_entries(100).values_list("score", flat=True))
    if len(scores) < 100:
        return None
    return scores[-1]


def get_top_100_candidate(score: int) -> tuple[bool, int | None]:
    threshold = get_top_100_threshold()
    if threshold is None:
        return True, None
    return score >= threshold, threshold


def get_rank_for_entry(entry_id: int) -> int | None:
    ranked_ids = list(leaderboard_queryset().values_list("id", flat=True))
    for idx, current_id in enumerate(ranked_ids, start=1):
        if current_id == entry_id:
            return idx
    return None
