"""Test loading information from environment vars"""

import importlib
from pathlib import Path

import pytest
from django.utils.encoding import force_text


def env_fixture(envvar: str, *values):
    """Generate fixture for environment variable variants."""

    @pytest.fixture(name=envvar, params=values)
    def _env_fixture(request, monkeypatch):
        if request.param is None:
            monkeypatch.delenv(envvar, raising=False)
        else:
            monkeypatch.setenv(envvar, force_text(request.param))
        return request.param

    return _env_fixture


@pytest.fixture
def scl_settings():
    """Force load SCL settings from disk"""

    spec = importlib.util.find_spec("softwarecollections.settings")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


SCL_BASE_DIR = env_fixture("SCL_BASE_DIR", None, "/var/scls")
SCL_SECRET_KEY = env_fixture("SCL_SECRET_KEY", None, b"abcdef" * 4)
SCL_DEBUG = env_fixture("SCL_DEBUG", None, "true", "false")
SCL_DBDEBUG = env_fixture("SCL_DBDEBUG", None, "true", "false")
SCL_ALLOWED_HOSTS = env_fixture("SCL_ALLOWED_HOSTS", None, "single", "one:two:three")
SCL_ADMINS = env_fixture(
    "SCL_ADMINS",
    None,
    "One <one@example.com>",
    "One <one@example.com>, Two <two@example.com>",
)
SCL_DATABASE_URL = env_fixture(
    "SCL_DATABASE_URL", None, "postgres://user:password@%2fvar%2fscls:5432/scldb"
)
SCL_DATABASE_PASSWORD = env_fixture("SCL_DATABASE_PASSWORD", None, "overriden")
SCL_CACHE_URL = env_fixture("SCL_CACHE_URL", None, "memcached://localhost:11211")


@pytest.fixture(params=[None, b"aa" * 8])
def SCL_SECRET_KEY_FILE(request, monkeypatch, tmpdir):
    if request.param is None:
        monkeypatch.delenv("SCL_SECRET_KEY_FILE", raising=False)
        return None
    else:
        path = tmpdir.mkdir("scls").join("secret_key")
        path.write(request.param)
        monkeypatch.setenv("SCL_SECRET_KEY_FILE", str(path))
        return str(path)


def test_base_dir(SCL_BASE_DIR, scl_settings):
    """The BASE_DIR is set to expected value"""

    if SCL_BASE_DIR is None:
        expected = Path(__file__).parents[1]
    else:
        expected = Path(SCL_BASE_DIR)

    assert scl_settings.BASE_DIR == expected


def test_secret_key_is_loaded(SCL_SECRET_KEY, SCL_SECRET_KEY_FILE, scl_settings):
    """The secret key is loaded from external source"""

    if SCL_SECRET_KEY is not None:
        assert scl_settings.SECRET_KEY == SCL_SECRET_KEY
        return  # Ignore other relevant environment variables

    if SCL_SECRET_KEY_FILE is not None:
        assert scl_settings.SECRET_KEY == Path(SCL_SECRET_KEY_FILE).read_bytes()
        return  # Ignore default

    # if both envvars are not set, assert that it still has non-empty value
    assert scl_settings.SECRET_KEY


def test_debug(SCL_DEBUG, scl_settings):
    """Expected debug parameter is set"""

    if SCL_DEBUG == "true" or SCL_DEBUG is None:
        assert scl_settings.DEBUG
    else:
        assert not scl_settings.DEBUG


def test_dbdebug(SCL_DBDEBUG, scl_settings):
    """Expected database debug parameter is set"""

    if SCL_DBDEBUG == "true":
        assert scl_settings.DBDEBUG
    else:
        assert not scl_settings.DBDEBUG


def test_allowed_hosts(SCL_ALLOWED_HOSTS, scl_settings):
    """Allowed hosts are set as expected"""

    if SCL_ALLOWED_HOSTS is None:
        assert scl_settings.ALLOWED_HOSTS == ["*"]
    else:
        assert scl_settings.ALLOWED_HOSTS == SCL_ALLOWED_HOSTS.split(":")


def test_admin_emails(SCL_ADMINS, scl_settings):
    """Administrator addresses are set as expected"""

    assert isinstance(scl_settings.ADMINS, list)

    if SCL_ADMINS is None:
        assert len(scl_settings.ADMINS) == 0
    else:
        assert len(scl_settings.ADMINS) >= 1
        assert scl_settings.ADMINS[0] == ("One", "one@example.com")


def test_database(SCL_DATABASE_URL, scl_settings):
    """Database configuration is loaded from an URL"""

    if SCL_DATABASE_URL is None:
        expected = {
            "ENGINE": "django.db.backends.sqlite3",
            "HOST": "",
            "USER": "",
            "PASSWORD": "",
            "NAME": str(scl_settings.BASE_DIR / "data" / "db.sqlite3"),
            "PORT": "",
            "CONN_MAX_AGE": 0,
        }
    elif SCL_DATABASE_URL.startswith("postgres"):
        expected = {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "HOST": "/var/scls",
            "USER": "user",
            "PASSWORD": "password",
            "NAME": "scldb",
            "PORT": 5432,
            "CONN_MAX_AGE": 0,
        }

    assert scl_settings.DATABASES["default"] == expected


def test_database_with_extra_password(
    SCL_DATABASE_URL, SCL_DATABASE_PASSWORD, scl_settings
):
    """Database configuration expects explicit password settings"""

    # if an URL is provided, the password should be taken from it first
    expected_password = "" if SCL_DATABASE_URL is None else "password"

    # explicit extra password overrides the one from URL
    if SCL_DATABASE_PASSWORD is not None:
        expected_password = SCL_DATABASE_PASSWORD

    assert scl_settings.DATABASES["default"]["PASSWORD"] == expected_password


def test_cache(SCL_CACHE_URL, scl_settings):
    """Cache URL is parsed properly"""

    if SCL_CACHE_URL is None:
        expected = {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "scl-devel",
            "KEY_PREFIX": "softwarecollections",
        }
    elif SCL_CACHE_URL.startswith("memcached"):
        expected = {
            "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
            "LOCATION": "localhost:11211",
            "KEY_PREFIX": "softwarecollections",
        }

    assert scl_settings.CACHES["default"] == expected
