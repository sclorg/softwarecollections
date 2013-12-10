"""
Django settings for softwarecollections project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# import ugettext_lazy to avoid circular module import
from django.utils.translation import ugettext_lazy as _

# localsettings is used to store site depandant settings
from .localsettings import \
    BASE_DIR, SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASES, \
    LANGUAGE_CODE, TIME_ZONE, LANGUAGES, \
    MEDIA_ROOT, MEDIA_URL, STATIC_ROOT, STATIC_URL


TEMPLATE_DEBUG = True


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tagging',
    'softwarecollections',
    'softwarecollections.scls',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
)

ROOT_URLCONF = 'softwarecollections.urls'

WSGI_APPLICATION = 'softwarecollections.wsgi.application'


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True

# COPR

COPR_API_URL = 'http://copr-fe.cloud.fedoraproject.org/api/'

##################
# AUTHENTICATION #
##################

AUTH_USER_MODEL = 'auth.User'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'softwarecollections.fas.backend.FasBackend',
)

LOGIN_URL = '/login/'

LOGOUT_URL = '/logout/'

LOGIN_REDIRECT_URL = '/'

# The number of days a password reset link is valid for
PASSWORD_RESET_TIMEOUT_DAYS = 3

#SOCIAL_AUTH_LOGIN_ERROR_URL = '/'
