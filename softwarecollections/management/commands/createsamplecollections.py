from optparse import make_option

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from softwarecollections.scls.models import SoftwareCollection, Score, MATURITY, REBASE_POLICY, UPDATE_FREQ
from random import randint, sample, choice

class Command(BaseCommand):
    args = '[ <username> ]'
    help = 'Used to make user a superuser.'

    requires_model_validation = False

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("need exactly one argument for username")
        username, = args
        UserModel = get_user_model()
        try:
            maintainer = UserModel.objects.get(**{UserModel.USERNAME_FIELD: username})
        except UserModel.DoesNotExist:
            raise CommandError("user '%s' does not exist" % username)
        self.stdout.write("Creating set of sample collections maintained by user '%s'\n" % maintainer)
        for name in [
            'flexmock', 'rake', 'minitest', 'mocha', 'i18n', 'tzinfo', 'builder',
            'rack', 'thor', 'sepx_processor', 'ruby_parser', 'ruby2ruby', 'ZenTest',
            'RubyInline', 'ParseTree', 'diff-lcs', 'activesupport', 'activemodel',
            'sqlite3', 'arel', 'activerecord', 'rspec-core', 'rspec-mocks', 'regin',
            'rack-mount', 'tilt', 'sinatra', 'rspec', 'abstract', 'erubis', 'railties',
            'mime-types', 'treetop', 'mail', 'bundler', 'actionmailer']:
            scl_name = 'stack_rails_3.0_rubygem-%s' % name
            for version in sample(['0.9.3', '0.11'], randint(1,2)):
                self.stdout.write("Creating sample collection: %s %s\n" % (scl_name, version))
                scl              = SoftwareCollection()
                scl.name         = scl_name
                scl.version      = version
                scl.summary      = 'a software collection with name %s and version %s' % (scl.name, scl.version)
                scl.description  = ', '.join([scl.summary for i in range(3)])
                scl.update_freq  = choice(list(UPDATE_FREQ))
                scl.rebase_policy= choice(list(REBASE_POLICY))
                scl.maturity     = choice(list(UPDATE_FREQ))
                scl.maintainer   = maintainer
                scl.save()
                for user in UserModel.objects.all():
                    s = Score()
                    s.user  = user
                    s.scl   = scl
                    s.score = randint(1, 10)
                    s.save()

