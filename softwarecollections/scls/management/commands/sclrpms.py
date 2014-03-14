import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from softwarecollections.scls.models import Repo


class Command(BaseCommand):
    help = 'Rebuild all release RPMs'

    def handle(self, *args, **options):
        failed = 0
        for repo in Repo.objects.filter(enabled=True):
            try:
                self.stdout.write('rpmbuild {}'.format(repo.rpmname))
                repo.rpmbuild()
                repo.createrepo()
            except Exception as e:
                self.stderr.write(str(e))
                failed += 1

        if failed:
            raise CommandError("Done ({} failed)".format(failed))
        self.stdout.write("Done (0 failed)")
