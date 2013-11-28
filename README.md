softwarecollections
===================

Software Collections Management Website

Installation
------------

  1. Enable yum repository from copr

    wget -O /etc/yum.repos.d/SoftwareCollections.repo http://copr-fe.cloud.fedoraproject.org/coprs/mstuchli/SoftwareCollections/repo/fedora-19-x86_64/

  2. Install package softwarecollections

    yum -y install softwarecollections


Configuration
-------------

  1. Check the configuration in config files:

    vim /etc/softwarecollections/localsettings
    vim /etc/httpd/conf.d/softwarecollections.conf

  2. Initialize database

    softwarecollections syncdb

  3. If using sqlite, make sure httpd has write access to it

    chgrp apache /var/lib/softwarecollections/data/db.sqlite3
    chmod g+w    /var/lib/softwarecollections/data/db.sqlite3

  4. Prepare static content

    softwarecollections collectstatic

  5. Reload httpd configuration

    service httpd reload


Development instance
--------------------

  1. Clone the git repository

    git clone git@github.com:misli/softwarecollections.git
    cd softwarecollections

  2. Create local configuration

    cp softwarecollections/localsettings{-development,}.py

  3. Initialize development database

    ./manage.py syncdb

  4. Run development server

    ./manate.py runserver


RPM build
---------

To create RPM from the latest tagged release type:

    tito build --rpm

To create RPM from the last commit (it does not have to be pushed to the repo) type:

    tito build --rpm --test


Help
----

For more information about using commandline interface just type

    ./manage.py help

or visit [Django Documentation](https://docs.djangoproject.com/en/1.6/).
