# -*- coding: utf-8 -*-
"""
Django settings for softwarecollections project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# import ugettext_lazy to avoid circular module import
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = '/var/scls'

# SECURITY WARNING: keep the secret key used in production secret!
with open(os.path.join(BASE_DIR, 'secret_key'), 'rb') as f:
    SECRET_KEY = repr(f.read())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['www.softwarecollections.org']

# Emails
# https://docs.djangoproject.com/en/1.6/ref/settings/#std:setting-ADMINS
# https://docs.djangoproject.com/en/1.6/ref/settings/#std:setting-MANAGERS
# https://docs.djangoproject.com/en/1.6/ref/settings/#std:setting-SERVER_EMAIL
ADMINS = (
    ('Jakub Dorňák',   'jdornak@redhat.com'),
    ('Miroslav Suchý', 'msuchy@redhat.com'),
)
MANAGERS = ADMINS
SERVER_EMAIL = 'root@softwarecollections.org'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'data', 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

LANGUAGES = (
    ('en', 'English'),
    #('cs', 'Čeština'),
)

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'htdocs', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'htdocs', 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Absolute path to the directory repos should be synced to.
REPOS_ROOT = os.path.join(BASE_DIR, 'htdocs', 'repos')

# URL prefix for repo.
REPOS_URL  = '/repos/'

# Absolute path to the directory used by yum cache
YUM_CACHE_ROOT = '/tmp/softwarecollections-yum-cache'

# Absolute path to the directory to be used as rpm _topdir
RPMBUILD_TOPDIR = '/tmp/softwarecollections-rpmbuild'

