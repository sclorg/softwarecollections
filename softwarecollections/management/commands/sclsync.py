import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from softwarecollections.scls.models import SoftwareCollection


class Command(BaseCommand):
    args = '<destdir>'
    help = 'Sync SCLs with copr repos'

    def handle(self, *args, **options):
        try:
            destdir = args[0]
        except:
            raise CommandError('need exactly 1 argument')

        for scl in SoftwareCollection.objects.filter(need_sync=True):
            scl.copr.reposync(os.path.join(destdir,
                              "{}-{}".format(scl.maintainer, scl.name)))
            scl.need_sync = False
            scl.save()

        self.stdout.write("Done")
