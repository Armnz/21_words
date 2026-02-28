from django.contrib import admin

from .models import LeaderboardEntry, Prompt, Session, Word


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ["id", "word"]
    search_fields = ["word"]
    ordering = ["word"]


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ["id", "description", "valid_words_count"]
    search_fields = ["description"]
    list_filter = ["valid_words_count"]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "status",
        "current_ordinal",
        "total_score",
        "created_at",
    ]
    search_fields = ["id"]
    list_filter = ["status", "created_at"]
    readonly_fields = ["id", "created_at"]
    ordering = ["-created_at"]


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ["player_name", "score", "created_at"]
    search_fields = ["player_name"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]
    ordering = ["-score", "created_at"]
