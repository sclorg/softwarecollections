#!/usr/bin/env python3
# encoding: utf-8

import softwarecollections
#from distutils.core import setup
from setuptools import setup

setup(
    name         = "softwarecollections",
    version      = '0.4',
    description  = "Software Collection Management Website and Utils",
    author       = "Jakub Dorňák",
    author_email = "jdornak@redhat.com",
    url          = "https://github.com/misli/softwarecollections",
    packages     = [
        "softwarecollections",
        "softwarecollections.management",
        "softwarecollections.management.commands",
    ],
    include_package_data = True,
)
