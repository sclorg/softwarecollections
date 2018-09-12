"""py.test global configuration"""

import pytest

from django.core.management import call_command
from django.db import connection


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
