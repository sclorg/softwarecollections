softwarecollections
===================

Software Collections Management Website

Installation
------------

Enable yum repository from copr:

    wget -O /etc/yum.repos.d/SoftwareCollections.repo http://copr-fe.cloud.fedoraproject.org/coprs/mstuchli/SoftwareCollections/repo/fedora-19-x86_64/

Install package softwarecollections:

    yum -y install softwarecollections


Configuration
-------------

Check the configuration in config files:

    vim /etc/softwarecollections/localsettings
    vim /etc/httpd/conf.d/softwarecollections.conf

Initialize database:

    softwarecollections syncdb

If using sqlite, make sure httpd has write access to it:

    chgrp apache /var/lib/softwarecollections/data/db.sqlite3
    chmod g+w    /var/lib/softwarecollections/data/db.sqlite3

Prepare static content:

    softwarecollections collectstatic

Reload httpd configuration:

    service httpd reload


Development instance
--------------------

Clone the git repository:

    git clone git@github.com:misli/softwarecollections.git
    cd softwarecollections

Create local configuration:

    cp softwarecollections/localsettings{-development,}.py

Initialize development database:

    ./manage.py syncdb

Run development server:

    ./manage.py runserver


RPM build
---------

To create RPM from the latest tagged release type:

    tito build --rpm

To create RPM from the last commit (it does not have to be pushed to the repo) type:

    tito build --rpm --test


Help
----

For more information about using commandline interface type:

    ./manage.py help

or visit [Django Documentation](https://docs.djangoproject.com/en/1.6/).
