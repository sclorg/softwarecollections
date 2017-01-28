FROM fedora:25

RUN dnf -y install git && dnf clean all
RUN dnf -y install 'dnf-command(copr)' && dnf clean all
RUN dnf -y copr enable jdornak/SoftwareCollections && dnf clean all
# hackishly install dependencies without the actual package
RUN dnf -y install softwarecollections && \
    rpm -e softwarecollections && \
    dnf clean all

# installing pyyaml so we can load example data in yaml format
RUN dnf -y install python3-PyYAML && dnf clean all

WORKDIR /srv
EXPOSE 8000
RUN useradd test

ADD run-devel /usr/bin/
CMD /usr/bin/run-devel

ADD . /srv/softwarecollections
RUN chown -R test:test /srv/softwarecollections
USER test

