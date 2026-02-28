import logging
import time

from django.core.management.base import BaseCommand

from game.models import Prompt, Word
from game.services.validation import rule_to_q

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Recompute valid_words_count for all prompts using current Word entries"

    def handle(self, *args, **options):
        start = time.time()
        prompts = list(Prompt.objects.all())
        total_updated = 0
        for p in prompts:
            rule = p.rule or {}
            q = rule_to_q(rule)
            # perform the count in SQL using Django ORM
            count = Word.objects.filter(q).count()
            p.valid_words_count = count
            p.save(update_fields=["valid_words_count"])
            total_updated += 1
            logger.info("Prompt %s updated with %d matches", p.id, count)

        elapsed = time.time() - start
        self.stdout.write(self.style.SUCCESS(f"Updated {total_updated} prompts in {elapsed:.2f}s"))
