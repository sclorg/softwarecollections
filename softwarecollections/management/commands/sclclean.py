import os, shutil
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Delete files belonging to deleted collections"

    def handle(self, *args, **options):
        for path in filter(os.path.isdir, map(lambda name: os.path.join(settings.REPOS_ROOT, name), os.listdir(settings.REPOS_ROOT))):
            for name in filter(lambda n: n.startswith('.') and n.endswith('.deleted'), os.listdir(path)):
                    shutil.rmtree(os.path.join(path, name), ignore_errors=True)
