#!/usr/bin/env python3
# encoding: utf-8

import os

from setuptools import find_packages, setup

REPO_DIR = os.path.dirname(os.path.abspath(__file__))

METADATA = {
    "name": "softwarecollections",
    "author": "Jakub Dorňák",
    "author_email": "jakub.dornak@misli.cz",
    "maintainer": "Jan Staněk",
    "maintainer_email": "jstanek@redhat.com",
    "url": "https://github.com/sclorg/softwarecollections",
}

# Basic/common package dependencies
REQUIRES = [
    "dj-database-url",
    "django~=2.2.10",
    "django-fas",
    "django-markdown2",
    "django-sekizai",
    "django-simple-captcha",
    "django-tagging",
    "flock",
    "gunicorn[eventlet]",
    "eventlet<0.30.3",  # https://github.com/benoitc/gunicorn/pull/2581
    "psycopg2<2.9",  # https://code.djangoproject.com/ticket/32856
    "py3dns",  # pylibravatar missing dependency workaround
    "pylibravatar",
    "python3-memcached",
    "python3-openid",
    "requests",
    "whitenoise",
]

# Extra dependencies for testing
TEST_REQUIRES = ["pytest", "pytest-django", "pyyaml"]


def rpm_compat_version():
    """Constructs RPM-compatible version identifier"""

    def rpm_version_scheme(version):
        if version.exact:
            return version.format_with("{tag}")
        else:
            return version.format_with("{tag}.dev{distance}")

    return {"version_scheme": rpm_version_scheme}


with open(os.path.join(REPO_DIR, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    **METADATA,
    use_scm_version=rpm_compat_version,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3",
    setup_requires=["pytest-runner", "setuptools_scm"],
    install_requires=REQUIRES,
    tests_require=TEST_REQUIRES,
)
