softwarecollections
===================

Software Collections Website

Installation
------------

### Requirements

* [classytags](https://pypi.python.org/pypi/django-classy-tags/0.4)
* [cms](https://github.com/divio/django-cms)
* [django](https://pypi.python.org/pypi/Django/1.5.5)
* [djangocms_text_ckeditor](https://github.com/divio/djangocms-text-ckeditor)
* [menus](https://github.com/divio/django-cms)
* [mptt](https://pypi.python.org/pypi/django-mptt/0.6.0)
* [sekizai](https://pypi.python.org/pypi/django-sekizai/0.7)
* [six](https://pypi.python.org/pypi/six/1.4.1)
* [south](https://pypi.python.org/pypi/South/0.8.4)
* [html5lib](https://pypi.python.org/pypi/html5lib/0.99)

All these python modules must be available in your PYTHON_PATH.

### Configuration

Create local settings file (no changes needed for development instance):

    cp softwarecollections/localsettings-template.py cp softwarecollections/localsettings.py

Initialize the database:

    ./manage.py syncdb
    ./manage.py migrate

Usage
-----

To start the development instance, just type:

    ./manage.py runserver

Software Collections Website is based on [Django 1.5](https://www.djangoproject.com/) and [django CMS 3.0](https://www.django-cms.org/).
For more information see the documentation at https://docs.djangoproject.com/en/1.5/ and http://docs.django-cms.org/en/develop/.
