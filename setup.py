#!/usr/bin/env python3
# encoding: utf-8

import os
from setuptools import setup, find_packages

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

METADATA = {
    "name": "softwarecollections",
    "version": "0.16",
    "author": "Jakub Dorňák",
    "author_email": "jakub.dornak@misli.cz",
    "maintainer": "Jan Staněk",
    "maintainer_email": "jstanek@redhat.com",
    "url": "https://github.com/sclorg/softwarecollections",
}

# Basic/common package dependencies
REQUIRES = [
    "django-fas",
    "django-markdown2",
    "django-sekizai",
    "django-simple-captcha",
    "django-tagging",
    "django<1.11",
    "flock",
    "py3dns",  # pylibravatar missing dependency workaround
    "pylibravatar",
    "python3-memcached",
    "python3-openid",
    "requests",
]

# Extra dependencies for production
PROD_REQUIRES = [
    "mod_wsgi",
    "psycopg2",
]
# Extra dependencies for testing
TEST_REQUIRES = [
    "pytest",
    "pytest-django",
    "pyyaml",
]


with open(os.path.join(REPO_DIR, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    **METADATA,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3",
    setup_requires=["pytest-runner"],
    install_requires=REQUIRES,
    tests_require=TEST_REQUIRES,
    extras_require={
        "production": PROD_REQUIRES,
    },
)
