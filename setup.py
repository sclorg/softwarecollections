#!/usr/bin/env python
# encoding: utf-8

import softwarecollections
from distutils.core import setup

setup(
    name         = "softwarecollections",
    version      = '.'.join(map(str, softwarecollections.VERSION)),
    description  = "Software Collection Management Website and Utils",
    author       = "Jakub Dorňák",
    author_email = "jdornak@redhat.com",
    url          = "https://github.com/misli/softwarecollections",
    packages     = [
        "softwarecollections",
        "softwarecollections.management",
        "softwarecollections.management.commands",
    ],
)
