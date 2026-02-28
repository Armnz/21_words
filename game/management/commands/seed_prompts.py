import logging

from django.core.management.base import BaseCommand

from game.models import Prompt

logger = logging.getLogger(__name__)


PRESET_PROMPTS = [
    ("Vārdi, kas sākas ar 'a'", {"type": "starts_with", "value": "a"}),
    ("Vārdi, kas sākas ar 'ā'", {"type": "starts_with", "value": "ā"}),
    ("Vārdi, kas sākas ar 'e'", {"type": "starts_with", "value": "e"}),
    ("Vārdi, kas sākas ar 'ē'", {"type": "starts_with", "value": "ē"}),
    ("Vārdi, kas sākas ar 'i'", {"type": "starts_with", "value": "i"}),
    ("Vārdi, kas sākas ar 'ī'", {"type": "starts_with", "value": "ī"}),
    ("Vārdi, kas sākas ar 'u'", {"type": "starts_with", "value": "u"}),
    ("Vārdi, kas sākas ar 'ū'", {"type": "starts_with", "value": "ū"}),
    ("Vārdi, kas sākas ar 'š'", {"type": "starts_with", "value": "š"}),
    ("Vārdi, kas sākas ar 'ž'", {"type": "starts_with", "value": "ž"}),
    ("Vārdi, kas beidzas ar 's'", {"type": "ends_with", "value": "s"}),
    ("Vārdi, kas beidzas ar 'š'", {"type": "ends_with", "value": "š"}),
    ("Vārdi, kas satur 'ie'", {"type": "contains", "value": "ie"}),
    ("Vārdi, kas satur 'au'", {"type": "contains", "value": "au"}),
    ("Vārdi, kas satur 'šķ'", {"type": "contains", "value": "šķ"}),
    ("Vārdi ar dubultu 'll'", {"type": "contains_double", "value": "ll"}),
    ("Vārdi ar dubultu 'ss'", {"type": "contains_double", "value": "ss"}),
    ("Vārdi ar dubultu 'nn'", {"type": "contains_double", "value": "nn"}),
    ("Vārdi ar dubultu 'rr'", {"type": "contains_double", "value": "rr"}),
    ("Vārdi ar diakritisku burtu (ā,č,ē,ģ,ī,ķ,ļ,ņ,š,ū,ž)", {"type": "contains_diacritic"}),
    ("Vārdi, kas sākas ar 'č'", {"type": "starts_with", "value": "č"}),
    ("Vārdi, kas sākas ar 'ķ'", {"type": "starts_with", "value": "ķ"}),
    ("Vārdi, kas sākas ar 'ģ'", {"type": "starts_with", "value": "ģ"}),
    ("Vārdi, kas sākas ar 'ļ'", {"type": "starts_with", "value": "ļ"}),
    ("Vārdi, kas sākas ar 'ņ'", {"type": "starts_with", "value": "ņ"}),
    ("Vārdi, kas satur 'ou'", {"type": "contains", "value": "ou"}),
    ("Vārdi, kas satur 'ai'", {"type": "contains", "value": "ai"}),
    ("Vārdi, kas beidzas ar 'a'", {"type": "ends_with", "value": "a"}),
    ("Vārdi, kas beidzas ar 'i'", {"type": "ends_with", "value": "i"}),
]


class Command(BaseCommand):
    help = "Seed a reasonable set of Latvian prompts into the DB"

    def handle(self, *args, **options):
        created = 0
        for desc, rule in PRESET_PROMPTS:
            obj, was_created = Prompt.objects.get_or_create(description=desc, rule=rule)
            if was_created:
                created += 1
        logger.info("Seeded %d prompts", created)
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} prompts"))
