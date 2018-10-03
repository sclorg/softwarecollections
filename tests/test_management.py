"""Tests for custom management commands"""

from django.core.management import call_command


def test_makeerrorpages(tmpdir, settings):
    """makeerrorpages produce expected error pages"""

    EXPECTED_PAGES = "400.html", "403.html", "404.html", "500.html"

    root = tmpdir.mkdir("media")
    settings.MEDIA_ROOT = root
    settings.ADMINS = [("Admin", "admin@example.com")]

    call_command("makeerrorpages")

    assert all(
        root.join(page).check(file=True) for page in EXPECTED_PAGES
    ), root.listdir()
