from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from softwarecollections.utils import get_copr, generate_repo_config, run_reposync

class Command(BaseCommand):
    args = '<username> <coprname> <destdir>'
    help = 'Synces COPR repo to specified directory.'

    option_list = BaseCommand.option_list + (
            make_option('--apiurl', help='Override COPR API URL',
                        default=settings.DEFAULT_COPR_API_URL),
            )

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("need exactly 3 arguments")

        username, coprname, destdir = args
        self.stdout.write("Syncing {}-{} to {}".format(*args))

        copr = get_copr(username, coprname, options.get('apiurl'))
        configs = generate_repo_config(copr, username)
        run_reposync(configs, destdir)

        self.stdout.write("Done")
