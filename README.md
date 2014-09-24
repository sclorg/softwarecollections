softwarecollections
===================

Software Collections Management Website


Installation
------------

Enable yum repository from copr:

    sudo wget -O /etc/yum.repos.d/SoftwareCollections.repo http://copr-fe.cloud.fedoraproject.org/coprs/mstuchli/SoftwareCollections/repo/fedora-19-x86_64/

Install package softwarecollections:

    sudo yum -y install softwarecollections


Configuration (production instance)
-----------------------------------

Check the configuration in config files:

    sudo vim /etc/softwarecollections/localsettings
    sudo vim /etc/httpd/conf.d/softwarecollections.conf

If you have changed the configuration of database connection
(which is recommended for production), initialize the database with:

    sudo softwarecollections syncdb --migrate --noinput


Development instance
--------------------

Follow the **installation steps**. You do not need package
*softwarecollections* itself, but you need all it's requirements.

Clone the git repository:

    git clone git@github.com:misli/softwarecollections.git
    cd softwarecollections

Create local configuration:

    cp softwarecollections/localsettings{-development,}.py

Initialize development database:

    ./manage.py syncdb --all
    ./manage.py migrate --fake

Run development server:

    ./manage.py runserver

Voilà!

No registration of user is required.
You may simply [login](http://127.0.0.1:8000/login) if You have
[FAS](https://admin.fedoraproject.org/accounts/) account.

If You want to access the [admin site](http://127.0.0.1:8000/admin/),
first make Yourself a superuser:

    ./manage.py makesuperuser $USER

To update your code and database to the last available version run:

    git pull --rebase
    ./manage.py syncdb --migrate --noinput

You may also need to install some new requirements (see the spec file).


RPM build
---------

To create and build RPM from the latest tagged release type:

    tito build --rpm
    tito release copr

To create RPM from the last commit (it does not have to be pushed to the repo) type:

    tito build --rpm --test
    tito release copr-test

Note that you need rel-eng/releasers.conf:

    sed "s/<USERNAME>/$USERNAME/" < rel-eng/releasers.conf.template > rel-eng/releasers.conf


Help
----

If this is Your first time working with Django application, read through the
[Django Tutorial](https://docs.djangoproject.com/en/1.6/intro/tutorial01/).

For the detailed information about all aspect of using Django see the
[Django Documentation](https://docs.djangoproject.com/en/1.6/).

If You have changed some model and You want to create migrations, see the
[South Tutorial](http://south.readthedocs.org/en/latest/tutorial/part1.html).
