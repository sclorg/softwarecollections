"""Settings utilities for working with environment variables"""

import re
import os
from distutils.util import strtobool
from urllib.parse import urlparse, uses_netloc
from pathlib import Path
from typing import Optional, Pattern, Sequence, Tuple
from warnings import warn

import dj_database_url
from django.core.management.utils import get_random_secret_key

# Extra types
EmailSequence = Sequence[Tuple[str, str]]

# E-mail parsing
EMAIL_SEPARATOR = re.compile(r",\s?")
EMAIL_PARTS = re.compile(r"(?P<fullname>[\w\s]+)<(?P<email>[^@]+@[^@]+\.[^@]+)>")

# Cache URL support
CACHE_BACKEND = {
    "memcached": "django.core.cache.backends.memcached.MemcachedCache",
    "locmem": "django.core.cache.backends.locmem.LocMemCache",
}

uses_netloc.extend(CACHE_BACKEND.keys())


def load_boolean(envvar: str, default: bool = False) -> bool:
    """Load boolean environment variable"""

    value = os.getenv(envvar, str(default).lower())
    return strtobool(value)


def load_path(envvar: str, default: Optional[Path] = None) -> Optional[Path]:
    """Load file system path from environment"""

    candidate = os.getenv(envvar, "")
    if candidate:
        return Path(candidate).resolve()
    else:
        return default


def load_sequence(
    envvar: str, separator: Pattern = re.compile(r":"), default: Sequence[str] = ()
) -> Sequence[str]:
    """Load sequence of strings from environment (i.e. PATH)"""

    value = os.getenv(envvar)
    if value is None:
        return default
    else:
        return separator.split(value)


def load_email_sequence(
    envvar: str, default: Sequence[Tuple[str, str]] = []
) -> Sequence[Tuple[str, str]]:
    """Load sequence of e-mail addresses from environment.

    Expected format: User One <a@ex.com>, User Two <b@e.mail>
    """

    value_list = load_sequence(envvar, separator=EMAIL_SEPARATOR)
    match_iter = filter(None, map(EMAIL_PARTS.search, value_list))

    return [(m["fullname"].strip(), m["email"].strip()) for m in match_iter]


def load_secret_key(
    envvar: str, keyfile: Optional[Path] = None, default: Optional[str] = None
) -> str:
    """Load SECRET_KEY from environment or file.

    Priority:
        1. Environment variable.
        2. Contents of key file.
        3. Default value (randomly generated if not provided).
    """

    key = os.getenv(envvar, None)
    if key is not None:
        return key

    if keyfile is not None:
        if keyfile.is_file():
            return keyfile.read_text(encoding="utf-8").strip()
        else:
            warn(
                "Secret key file specified but not found;"
                " falling back to default secret."
            )

    if default is not None:
        return default
    else:
        return get_random_secret_key()


def load_database_url(envvar: str, default: str = "sqlite://:memory:") -> dict:
    """Load and parse database URL.

    Returns: Complete configuration dictionary.
    """

    # just wrap to have a consistent interface
    return dj_database_url.config(env=envvar, default=default)


def load_cache_url(envvar: str, default: str = "locmem://") -> dict:
    """Load and parse cache URL.

    Returns: Complete configuration dictionary.
    """

    parsed = urlparse(os.getenv(envvar, default=default))
    try:
        return {"BACKEND": CACHE_BACKEND[parsed.scheme], "LOCATION": parsed.netloc}
    except KeyError as err:
        message = "Unknown cache type: '{!s}'".format(err)
        raise ValueError(message) from err
