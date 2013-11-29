#!/usr/bin/env python3
# encoding: utf-8

import softwarecollections
#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name         = "softwarecollections",
    version      = '0.5',
    description  = "Software Collection Management Website and Utils",
    author       = "Jakub Dorňák",
    author_email = "jdornak@redhat.com",
    url          = "https://github.com/misli/softwarecollections",
    packages     = find_packages(),
    include_package_data = True,
)
