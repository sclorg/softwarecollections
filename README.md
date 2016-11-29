softwarecollections
===================

Software Collections Management Website


Installation
------------

Enable yum repository from copr:

```
    sudo dnf copr enable jdornak/SoftwareCollections
```

Install package softwarecollections:

```
    sudo dnf install softwarecollections
```


Configuration (production instance)
-----------------------------------

Check the configuration in config files:

```
    sudo vim /etc/softwarecollections/localsettings
    sudo vim /etc/httpd/conf.d/softwarecollections.conf
```


Development instance
--------------------

Follow the **installation steps**. You do not need package
*softwarecollections* itself, but you need all it's requirements.

Clone the git repository:

```
    git clone git@github.com:sclorg/softwarecollections.git
    cd softwarecollections
```

Clone the packaging-guide repository

```
    git clone git@github.com:pmkovar/packaging-guide.git
```

Import packaging-guide

```
    ./guide-build  packaging-guide
    ./guide-import packaging-guide
```

Create local configuration:

```
    cp softwarecollections/localsettings{-development,}.py
```

Initialize development database:

```
    ./manage.py migrate
```

Run development server:

```
    ./manage.py runserver
```

Voilà!

No registration of user is required.
You may simply [login](http://127.0.0.1:8000/login) if You have
[FAS](https://admin.fedoraproject.org/accounts/) account.

If You want to access the [admin site](http://127.0.0.1:8000/admin/),
first make Yourself a superuser:

```
    ./manage.py makesuperuser $USER
```

To update your code and database to the last available version run:

```
    git pull --rebase
    ./manage.py migrate
```

You may also need to install some new requirements (see the spec file).


RPM build
---------

To build RPM you need **tito** package. To release the RPM in Copr,
you need **copr-cli** package.

```
    sudo dnf install tito copr-cli
```

To build RPM locally type:

```
    tito build --rpm        # builds RPM from the latest tagged release
    tito build --rpm --test # builds RPM from the latest commit
```

To build RPM in Copr type:

```
    tito release copr       # submits build from the latest tagged release
    tito release copr-test  # submits build from the latest commit
```


Data migration from one server to another one
---------------------------------------------

1. Dump all data on the old system:

```
    softwarecollections dumpdata > data.json
```

2. Move data.json to the new system to location accessible by softwarecollections user.

```
    rsync old:data.json /var/scls/data.json
```

3. Delete automaticaly generated tables and load all data from json file:

```
    echo "delete from auth_permission;" | softwarecollections dbshell
    echo "delete from django_content_type;" | softwarecollections dbshell
    softwarecollections loaddata /var/scls/data.json
```


Voilà!


Help
----

If this is Your first time working with Django application, read through the
[Django Tutorial](https://docs.djangoproject.com/en/1.9/intro/tutorial01/).

For the detailed information about all aspect of using Django see the
[Django Documentation](https://docs.djangoproject.com/en/1.9/).

