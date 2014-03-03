import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from softwarecollections.scls.models import SoftwareCollection


class Command(BaseCommand):
    args = '<destdir>'
    help = 'Sync SCLs with copr repos'

    def handle(self, *args, **options):
        failed = 0
        for scl in SoftwareCollection.objects.filter(need_sync=True):
            try:
                self.stdout.write('Syncing {}'.format(scl.slug))
                scl.sync()
                if not scl.auto_sync:
                    scl.need_sync = False
                    scl.save()
            except Exception as e:
                self.stderr.write(str(e))
                failed += 1

        if failed:
            raise CommandError("Done ({} failed)".format(failed))
        self.stdout.write("Done (0 failed)")
