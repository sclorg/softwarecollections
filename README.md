softwarecollections
===================

Software Collections Website

Installation
------------

### Requirements

* [python3](http://python.org/download/releases/3.0/)
* [django16](https://www.djangoproject.com/download/)
* [django-sekizai](https://pypi.python.org/pypi/django-sekizai/0.7)

### Configuration

Create local settings file (no changes needed for development instance):

    cp softwarecollections/localsettings-template.py cp softwarecollections/localsettings.py

Initialize the database:

    ./manage.py syncdb

Usage
-----

To start the development instance, just type:

    ./manage.py runserver

For more information type:

    ./manage.py

or visit Django documentation at https://docs.djangoproject.com/en/1.6/.
