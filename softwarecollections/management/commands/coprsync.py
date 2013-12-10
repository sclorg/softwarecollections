from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from softwarecollections.copr import CoprProxy, COPR_API_URL

class Command(BaseCommand):
    args = '<username> <coprname> <destdir>'
    help = 'Synces COPR repo to specified directory.'

    option_list = BaseCommand.option_list + (
        make_option('--apiurl', help='Override COPR API URL', default=COPR_API_URL),
    )

    def handle(self, *args, **options):
        try:
            username, coprname, destdir = args
        except:
            raise CommandError('need exactly 3 arguments')

        try:
            copr_proxy = CoprProxy(options.get('apiurl'))
            copr = copr_proxy.copr(username, coprname)
            self.stdout.write('Syncing {} to {}'.format(copr, destdir))
            copr.reposync(destdir)
            self.stdout.write('Done')
        except Exception as e:
            raise CommandError(e)
