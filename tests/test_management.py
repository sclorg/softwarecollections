"""Tests for custom management commands"""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


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


def test_savekey_skips_undefined(monkeypatch, caplog):
    """savekey does nothing if SCL_SECRET_KEY_FILE is not set"""

    monkeypatch.delenv("SCL_SECRET_KEY_FILE", raising=False)

    call_command("savekey")

    # Check that the skip was reported
    assert any("skipping" in record.getMessage() for record in caplog.records)


def test_savekey_keeps_current_key(tmpdir, monkeypatch, caplog):
    """savekey does not overwrite existing key file"""

    ORIGINAL_KEY = "original key"

    path = tmpdir.join("current_key_keyfile")
    path.write_text(ORIGINAL_KEY, encoding="utf-8", ensure=True)
    modified = path.mtime()

    monkeypatch.setenv("SCL_SECRET_KEY_FILE", str(path))

    call_command("savekey")

    assert path.read_text("utf-8") == ORIGINAL_KEY
    assert path.mtime() == modified
    assert any("keeping" in record.getMessage() for record in caplog.records)


def test_savekey_saves_key(tmpdir, monkeypatch):
    """Savekey does save secret key"""

    path = tmpdir.join("saved_key_keyfile")
    monkeypatch.setenv("SCL_SECRET_KEY_FILE", str(path))
    assert path.check(exists=False)

    call_command("savekey")

    assert path.check(file=True) and path.size() > 0


def test_makesuperuser_respects_username(django_user_model):
    """makesuperuser respects specified username"""

    user = django_user_model.objects.create(
        username="will_be_superuser", password="password"
    )

    call_command("makesuperuser", user.username)
    user.refresh_from_db()

    assert user.is_superuser

    # Ensure that no users are present in the database
    django_user_model.objects.all().delete()
    with pytest.raises(CommandError):
        call_command("makesuperuser")
