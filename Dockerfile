FROM mattdm/fedora:f19

RUN yum -y install git wget
RUN wget -O /etc/yum.repos.d/SoftwareCollections.repo http://copr-fe.cloud.fedoraproject.org/coprs/mstuchli/SoftwareCollections/repo/fedora-19-x86_64/
# hackishly install dependencies without the actual package
RUN yum -y install softwarecollections
RUN yum -y remove softwarecollections

WORKDIR /srv
ADD . /srv/softwarecollections

EXPOSE 8000
RUN useradd test
USER test

CMD cd /srv/softwarecollections; \
cp softwarecollections/localsettings{-development,}.py; \
./manage.py syncdb --migrate --noinput; \
ls data/db.sqlite3 || echo -e "test\ntest@test.com\ntest\ntest\n" | ./manage.py createsuperuser; \
./manage.py makesuperuser test; \
chmod a+w data/db.sqlite3; \
./manage.py runserver 0.0.0.0:8000
