"""Django settings for softwarecollections project.

The configuration is read from various SCL_* environment variables.
The provided defaults are geared towards development instances
and should be changed in production.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import logging
import os
import re
from pathlib import Path

from pkg_resources import get_distribution
from pkg_resources import parse_version

from . import env_util as env

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Compatibility detection for external dependencies
whitenoise_version = get_distribution("whitenoise").parsed_version


# Build paths inside the project like this: BASE_DIR / "subdir" / ...
BASE_DIR = env.load_path(envvar="SCL_BASE_DIR", default=Path(__file__).parents[2])

# SECURITY WARNING: keep the secret key used in production secret!
# Priority: SCL_SECRET_KEY, SCL_SECRET_KEY_FILE, random string for each invocation
SECRET_KEY = env.load_secret_key(
    envvar="SCL_SECRET_KEY", keyfile=env.load_path(envvar="SCL_SECRET_KEY_FILE")
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.load_boolean("SCL_DEBUG", default=True)
DBDEBUG = env.load_boolean("SCL_DBDEBUG", default=False)

if get_distribution("django-sekizai").parsed_version < parse_version("0.10.0"):
    TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = env.load_sequence("SCL_ALLOWED_HOSTS", default=["*"])

# If trusted proxies are provided, turn on HTTP Forwarded middleware
HTTP_FORWARDED_TRUSTED_PROXY_SET = env.load_sequence(
    "SCL_TRUSTED_PROXIES", separator=re.compile(r"\s*,\s*"),
)
if HTTP_FORWARDED_TRUSTED_PROXY_SET:
    USE_HTTP_FORWARDED = True

# Emails
# https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-ADMINS
# https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-MANAGERS
# https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-SERVER_EMAIL
# Expected format: Admin One <adm1@example.com>, Admin Two <adm2@example.com>
ADMINS = env.load_email_sequence("SCL_ADMINS", default=[])
MANAGERS = ADMINS
SERVER_EMAIL = "SoftwareCollections @ {} <admin@softwarecollections.org>".format(
    os.uname().nodename
)

# COPR
COPR_URL = "https://copr.fedorainfracloud.org"
COPR_API_URL = COPR_URL + "/api"
COPR_COPRS_URL = COPR_URL + "/coprs"

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
DATABASES = {
    "default": env.load_database_url(
        "SCL_DATABASE_URL",
        default="sqlite:///{!s}".format(BASE_DIR / "data" / "db.sqlite3"),
    )
}
for db, conf in DATABASES.items():
    logger.info(
        "Using database %(db)s: %(host)s/%(name)s",
        {"db": db, "host": conf.get("HOST", ""), "name": conf.get("NAME")},
    )
# Overwrite/add password to the database credentials
default_db_password = env.load_string("SCL_DATABASE_PASSWORD")
if default_db_password:
    DATABASES["default"]["PASSWORD"] = default_db_password

# Session cache
CACHES = {
    "default": dict(
        env.load_cache_url("SCL_CACHE_URL", default="locmem://scl-devel"),
        KEY_PREFIX="softwarecollections",
    )
}
for name, conf in CACHES.items():
    logger.info("Using cache %s: %s", name, conf.get("LOCATION"))

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en"

TIME_ZONE = "UTC"

LANGUAGES = (
    ("en", "English"),
    # ('cs', 'Čeština'),
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = BASE_DIR / "htdocs" / "media"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = "/media/"

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = BASE_DIR / "htdocs" / "static"

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = "/static/"

if whitenoise_version < parse_version("4.1"):
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Absolute path to the directory repos should be synced to.
REPOS_ROOT = BASE_DIR / "htdocs" / "repos"

# URL prefix for repo.
REPOS_URL = "/repos/"

# Absolute path to the directory used by yum cache
YUM_CACHE_ROOT = Path("/tmp/softwarecollections-yum-cache")

# Absolute path to the directory to be used as rpm _topdir
RPMBUILD_TOPDIR = Path("/tmp/softwarecollections-rpmbuild")

# Application definition

INSTALLED_APPS = [
    "softwarecollections",
    "softwarecollections.scls",
    "softwarecollections.auth",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_markdown2",
    "tagging",
    "sekizai",
    "captcha",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "softwarecollections.middleware.forwarded.HttpForwardedMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Older whitenoise does not support MIDDLEWARE setting
if whitenoise_version < parse_version("3.2"):
    MIDDLEWARE_CLASSES = MIDDLEWARE
    del MIDDLEWARE

ROOT_URLCONF = "softwarecollections.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sekizai.context_processors.sekizai",
            ]
        },
    }
]

WSGI_APPLICATION = "softwarecollections.wsgi.application"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler"},
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "": {
            "handlers": DEBUG and ["console"] or ["console", "mail_admins"],
            "level": DEBUG and "DEBUG" or "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.db.backends": {
            "level": DBDEBUG and "DEBUG" or "INFO",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "handlers": [] if DEBUG else ["null"],
            "propagate": False,
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True

##################
# AUTHENTICATION #
##################

AUTH_USER_MODEL = "auth.User"

AUTHENTICATION_BACKENDS = (
    "softwarecollections.auth.backend.PerObjectModelBackend",
    "fas.backend.FasBackend",
)

LOGIN_URL = "/login/"

LOGOUT_URL = "/logout/"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# The number of days a password reset link is valid for
PASSWORD_RESET_TIMEOUT_DAYS = 3

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

CAPTCHA_FONT_SIZE = 32
CAPTCHA_LETTER_ROTATION = None
CAPTCHA_BACKGROUND_COLOR = "#ffffff"
CAPTCHA_FOREGROUND_COLOR = "#001100"
CAPTCHA_CHALLENGE_FUNCT = "captcha.helpers.math_challenge"
CAPTCHA_NOISE_FUNCTIONS = ()
CAPTCHA_FILTER_FUNCTIONS = ()
CAPTCHA_FLITE_PATH = "/usr/bin/flite"
CAPTCHA_TIMEOUT = 20
