import pytest
from django.core.management import call_command

from game.models import Word


@pytest.mark.django_db
def test_import_words_creates_words(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Ābols\nābols\napple\napple\n multi word\n\n")

    call_command("import_words", f"--path={p}")

    words = set(Word.objects.values_list("word", flat=True))
    # normalized lowercase expected
    assert "ābols" in words
    assert "apple" in words
    # multi word should be ignored
    assert all(" " not in w for w in words)
