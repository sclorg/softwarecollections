import getpass
from optparse import make_option

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database',
            default=DEFAULT_DB_ALIAS, help='Specifies the database to use. Default is "default".'),
    )
    args = '[ <username> ]'
    help = 'Used to make user a superuser.'

    requires_system_checks = False

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("need exactly one or zero arguments for username")

        if args:
            username, = args
        else:
            username = getpass.getuser()

        UserModel = get_user_model()

        try:
            u = UserModel._default_manager.using(options.get('database')).get(**{
                    UserModel.USERNAME_FIELD: username
                })
        except UserModel.DoesNotExist:
            raise CommandError("user '%s' does not exist" % username)

        self.stdout.write("Making user '%s' a superuser\n" % u)
        u.is_staff     = True
        u.is_superuser = True
        u.save()

        return "User '%s' successfully made a superuser" % u
