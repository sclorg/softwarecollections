"""py.test global configuration"""

import pytest
from pkg_resources import get_distribution, parse_version

from django.core.management import call_command
from django.db import connection

DJANGO_VERSION = get_distribution("Django").parsed_version


@pytest.fixture(scope="session")
def django_db_use_migrations(django_db_use_migrations):
    """Older Django (<2.0) has trouble with migrations on newer SQLite.

    The current workaround is to disable migrations on Django 1.*.
    Possibly related Django issue: https://code.djangoproject.com/ticket/29182
    """

    if DJANGO_VERSION < parse_version("2.0"):
        return False
    else:
        return django_db_use_migrations


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create testing database with example data."""

    with django_db_blocker.unblock():

        # Drop pre-generated values also contained in example data
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM auth_permission;")
            cursor.execute("DELETE FROM django_content_type;")

        # Load the example data
        call_command("loaddata", "example-data.yaml")
