import logging
from pathlib import Path

from django.core.management.base import BaseCommand

from game.models import Word
from game.services.validation import normalize_word

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import words from a UTF-8 file, one word per line. Usage: import_words --path /path/to/file.txt"

    def add_arguments(self, parser):
        parser.add_argument("--path", required=True, help="Path to UTF-8 words file")
        parser.add_argument("--batch", type=int, default=5000, help="Batch size for bulk inserts")

    def handle(self, *args, **options):
        path = Path(options["path"]).expanduser()
        batch = options["batch"]
        if not path.exists():
            raise FileNotFoundError(path)

        inserted = 0
        to_create = []
        seen = set()
        self.stdout.write(f"Reading {path}")
        with path.open("r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, start=1):
                raw = line.strip()
                if not raw:
                    continue
                # skip multi-word entries
                if " " in raw:
                    continue
                w = normalize_word(raw)
                if not w:
                    continue
                if w in seen:
                    continue
                seen.add(w)
                to_create.append(Word(word=w))
                if len(to_create) >= batch:
                    Word.objects.bulk_create(to_create, ignore_conflicts=True)
                    inserted += len(to_create)
                    self.stdout.write(f"Inserted {inserted}...")
                    to_create = []

        if to_create:
            Word.objects.bulk_create(to_create, ignore_conflicts=True)
            inserted += len(to_create)
        self.stdout.write(self.style.SUCCESS(f"Import complete. Approx inserted: {inserted}"))
