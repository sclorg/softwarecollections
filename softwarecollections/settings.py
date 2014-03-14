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
from .localsettings import (
    BASE_DIR, SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASES,
    ADMINS, MANAGERS, SERVER_EMAIL,
    COPR_URL, COPR_API_URL, COPR_COPRS_URL,
    LANGUAGE_CODE, TIME_ZONE, LANGUAGES,
    MEDIA_ROOT, MEDIA_URL, STATIC_ROOT, STATIC_URL, REPOS_ROOT, REPOS_URL,
    YUM_CACHE_ROOT, RPMBUILD_TOPDIR
)


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
    'django_markdown2',
    'tagging',
    'sekizai',
    'softwarecollections',
    'softwarecollections.scls',
    'softwarecollections.auth',
    'south',
    'captcha',
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
    'sekizai.context_processors.sekizai',
)

ROOT_URLCONF = 'softwarecollections.urls'

WSGI_APPLICATION = 'softwarecollections.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

USE_I18N = True

USE_L10N = True

USE_TZ = True

##################
# AUTHENTICATION #
##################

AUTH_USER_MODEL = 'auth.User'

AUTHENTICATION_BACKENDS = (
    'softwarecollections.auth.backend.PerObjectModelBackend',
    'softwarecollections.fas.backend.FasBackend',
)

LOGIN_URL = '/login/'

LOGOUT_URL = '/logout/'

LOGIN_REDIRECT_URL = '/'

# The number of days a password reset link is valid for
PASSWORD_RESET_TIMEOUT_DAYS = 3

CAPTCHA_FONT_SIZE        = 32
CAPTCHA_LETTER_ROTATION  = None
CAPTCHA_BACKGROUND_COLOR = '#ffffff'
CAPTCHA_FOREGROUND_COLOR = '#001100'
CAPTCHA_CHALLENGE_FUNCT  = 'captcha.helpers.math_challenge'
CAPTCHA_NOISE_FUNCTIONS  = ()
CAPTCHA_FILTER_FUNCTIONS = ()
CAPTCHA_FLITE_PATH       = '/usr/bin/flite'
CAPTCHA_TIMEOUT          = 20

