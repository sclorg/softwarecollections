import os
import shutil

from django.core.management.base import BaseCommand, CommandError
from softwarecollections.scls.models import SoftwareCollection

class Command(BaseCommand):
    help = "Delete files belonging to collections marked for deletion"

    def handle(self, *args, **options):
        failed = 0
        for scl in SoftwareCollection.everything.filter(deleted=True):
            try:
                self.stdout.write("Deleting {}".format(scl.slug))
                if os.path.isdir(scl.get_repos_root()):
                    shutil.rmtree(scl.get_repos_root())

                scl.delete()
            except Exception as exception:
                self.stderr.write(str(exception))
                failed += 1
        if failed:
            raise CommandError("Done ({} failed)".format(failed))
        self.stdout.write("Done (0 failed)")
