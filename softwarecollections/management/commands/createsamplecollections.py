from optparse import make_option

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from softwarecollections.copr import CoprProxy, COPR_API_URL
from softwarecollections.scls.models import SoftwareCollection, Score, MATURITY, REBASE_POLICY, UPDATE_FREQ
from random import randint, sample, choice

class Command(BaseCommand):
    help = 'Creates sample collections.'

    option_list = BaseCommand.option_list + (
        make_option('--apiurl', help='Override COPR API URL', default=COPR_API_URL),
    )

    def handle(self, *args, **options):
        copr_proxy = CoprProxy()
        User = get_user_model()
        users = User.objects.all()

        if len(users) == 0:
            raise CommandError('need at least one user')

        self.stdout.write('Creating set of sample collections')
        for username in ['msuchy','msrb']:
            for copr in copr_proxy.coprs(username):
                self.stdout.write('Creating sample collection: %s' % copr.slug)
                scl = SoftwareCollection(copr=copr)
                scl.update_freq  = choice(list(UPDATE_FREQ))
                scl.rebase_policy= choice(list(REBASE_POLICY))
                scl.maturity     = choice(list(MATURITY))
                scl.maintainer   = choice(users)
                scl.save()
                scl.tags         = ' '.join([scl.username, scl.name, scl.maintainer.get_username()])
                for user in users:
                    s = Score()
                    s.user  = user
                    s.scl   = scl
                    s.score = randint(1, 10)
                    s.save()

