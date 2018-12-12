import getpass
import logging
from typing import ClassVar

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS


class Command(BaseCommand):
    help: ClassVar[str] = "Make the current or specified user a superuser."

    requires_system_checks: ClassVar[bool] = False

    log: ClassVar[logging.Logger] = logging.getLogger(
        "softwarecollections.management.makesuperuser"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is "default".',
        )
        parser.add_argument(
            "username",
            nargs="?",
            help="Name of the user to promote to superuser. Defaults to current user.",
        )

    def handle(self, *args, **options):
        UserModel = get_user_model()
        username = options.get("username") or getpass.getuser()

        try:
            user = UserModel._default_manager.using(options.get("database")).get(
                **{UserModel.USERNAME_FIELD: username}
            )
        except UserModel.DoesNotExist as err:
            raise CommandError("user '%s' does not exist" % username) from err

        self.log.info("Making user '%s' a superuser", user)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        return "User '%s' successfully made a superuser" % user
