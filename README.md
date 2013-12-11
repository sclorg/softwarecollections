softwarecollections
===================

Software Collections Management Website


Installation
------------

Enable yum repository from copr:

    sudo wget -O /etc/yum.repos.d/SoftwareCollections.repo http://copr-fe.cloud.fedoraproject.org/coprs/mstuchli/SoftwareCollections/repo/fedora-19-x86_64/

Install package softwarecollections:

    sudo yum -y install softwarecollections

Install these python3 packages:

    yum -y install python3-django-tagging python3-requests python3-django-openid python3-openid

Configuration (production instance)
-----------------------------------

Check the configuration in config files:

    sudo vim /etc/softwarecollections/localsettings
    sudo vim /etc/httpd/conf.d/softwarecollections.conf

Initialize database:

    sudo softwarecollections syncdb --noinput
    sudo softwarecollections migrate

If using sqlite, make sure httpd has write access to it:

    chgrp apache /var/lib/softwarecollections/data/db.sqlite3
    chmod g+w    /var/lib/softwarecollections/data/db.sqlite3

Prepare static content:

    umask 022
    sudo softwarecollections collectstatic

Reload httpd configuration:

    sudo service httpd reload


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

    ./manage.py syncdb --noinput
    ./manage.py migrate

Run development server:

    ./manage.py runserver

Login at http://127.0.0.1:8000/login (login uses FAS) and make yourself a superuser:

    ./manage.py makesuperuser $USER

Now You may visit backend admin at http://127.0.0.1:8000/admin/.
You may also create a set of sample collections maintained by you:

    ./manage.py createsamplecollections $USER

To update your code and database to tha last available version run:

    git pull --rebase
    ./manage.py migrate


RPM build
---------

To create RPM from the latest tagged release type:

    tito build --rpm

To create RPM from the last commit (it does not have to be pushed to the repo) type:

    tito build --rpm --test


Help
----

If this is Your first time working with Django application, read through the
[Django Tutorial](https://docs.djangoproject.com/en/1.6/intro/tutorial01/).

For the detailed information about all aspect of using Django see the
[Django Documentation](https://docs.djangoproject.com/en/1.6/).

If You have changed some model and You want to create migrations, see the
[South Tutorial](http://south.readthedocs.org/en/latest/tutorial/part1.html).
