%global  scls_statedir %{_localstatedir}/scls
%global  secret_key    %{scls_statedir}/secret_key
%global  scls_confdir  %{_sysconfdir}/softwarecollections
%global  cron_confdir  %{_sysconfdir}/cron.d
%global  httpd_confdir %{_sysconfdir}/httpd/conf.d
%global  user_name     softwarecollections
%global  group_name    softwarecollections
%global  guide_name    packaging-guide
%global  guide_version 1

Name:              softwarecollections
Version:           0.17
Release:           1%{?dist}

Summary:           Software Collections Management Website and Utils
Group:             System Environment/Daemons
License:           BSD
URL:               http://softwarecollections.org/
Source0:           https://github.srcurl.net/sclorg/%{name}/v%{version}/%{name}-%{version}.tar.gz
# Additional sources are not yet supported by tito
# TODO: uncomment next line
#Source1:          %#{guide_name}-%#{guide_version}.tar.gz

BuildArch:         noarch

BuildRequires:     publican
BuildRequires:     python3-devel
BuildRequires:     python3-setuptools
BuildRequires:     python3-pytest-runner
BuildRequires:     systemd

Requires:          createrepo_c
Requires:          cronie
Requires:          flite
Requires:          httpd
Requires:          memcached
Requires:          mod_ssl
Requires:          policycoreutils-python-utils
Requires:          postgresql
Requires(pre):     postgresql
Requires:          postgresql-server
Requires(pre):     postgresql-server
Requires:          python3-defusedxml
Requires:          python3-django >= 1.8
Requires:          python3-django-fas
Requires:          python3-django-markdown2
Requires:          python3-django-sekizai
Requires:          python3-django-simple-captcha
Requires:          python3-django-tagging
Requires:          python3-flock
Requires:          python3-memcached
Requires:          python3-mod_wsgi
Requires:          python3-openid
Requires:          python3-pillow
Requires:          python3-psycopg2
Requires:          python3-pylibravatar
Requires:          python3-requests
Requires:          rpm-build
Requires:          rsync-daemon
Requires:          yum-utils
Requires:          MTA
# systemd
Requires:            systemd
Requires(pre):       systemd
Requires(posttrans): systemd
%{?systemd_requires: %systemd_requires}

%description
Software Collections Management Website and Utils


%prep
%setup -q
# Additional sources are not yet supported by tito
# TODO: uncomment next line
#%%setup -qn %%{name}-%%{version} -D -T -a 1


%build
rm %{name}/localsettings-development.py
mv %{name}/localsettings-production.py localsettings
mv %{name}/wsgi.py htdocs/

# Additional sources are not yet supported by tito
# TODO: remove next line
tar -xzf       %{guide_name}-%{guide_version}.tar.gz
./guide-build  %{guide_name}-%{guide_version}
./guide-import %{guide_name}-%{guide_version}

%{__python3} setup.py build


%install
# install python package
%{__python3} setup.py install --skip-build --root %{buildroot}

# install conf file as target of localsettings.py symlink
install -p -D -m 0644 localsettings \
    %{buildroot}%{scls_confdir}/localsettings
ln -s %{scls_confdir}/localsettings \
    %{buildroot}%{python3_sitelib}/%{name}/localsettings.py

# install commandline interface
install -p -D -m 0755 manage.py %{buildroot}%{_bindir}/%{name}
install -p -D -m 0755 %{name}-db-setup %{buildroot}%{_bindir}/%{name}-db-setup
install -p -D -m 0755 %{name}-services-setup %{buildroot}%{_bindir}/%{name}-services-setup

# install bash completion script
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
install -m 0644 -p conf/bash-completion/softwarecollections \
  %{buildroot}%{_datadir}/bash-completion/completions/softwarecollections

# install httpd config file and wsgi config file
install -p -D -m 0644 conf/httpd/%{name}.conf \
    %{buildroot}%{httpd_confdir}/%{name}.conf
install -p -D -m 0644 htdocs/wsgi.py \
    %{buildroot}%{scls_statedir}/htdocs/wsgi.py

# install directories for static content and site media
install -p -d -m 0775 htdocs/static \
    %{buildroot}%{scls_statedir}/htdocs/static
install -p -d -m 0775 htdocs/media \
    %{buildroot}%{scls_statedir}/htdocs/media
install -p -d -m 0775 htdocs/repos \
    %{buildroot}%{scls_statedir}/htdocs/repos

# install separate directory for sqlite db
install -p -d -m 0775 db \
     %{buildroot}%{scls_statedir}/db

# install crontab
install -p -D -m 0644 conf/cron/%{name} \
    %{buildroot}%{cron_confdir}/%{name}

# install rsyncd.conf
install -p -D -m 0644 conf/rsyncd/rsyncd.conf \
    %{buildroot}%{scls_confdir}/rsyncd.conf

# install softwarecollections-rsyncd.service
install -p -D -m 0644 conf/rsyncd/softwarecollections-rsyncd.service \
    %{buildroot}%{_unitdir}/softwarecollections-rsyncd.service

# create ghost secret_key
touch %{buildroot}%{scls_statedir}/secret_key


%check
# not all test deps are packaged in Fedora
# %%{__python3} setup.py test


%pre
/usr/sbin/groupadd --system %{group_name} &>/dev/null || :
/usr/sbin/useradd --system --home-dir /var/scls \
    --gid %{group_name} --groups postgres \
    %{user_name} &>/dev/null || :


%post
# systemd
%systemd_post softwarecollections-rsyncd.service

# create secret key
test -e %{secret_key} || (
    umask 077
    dd bs=1k of=%{secret_key} if=/dev/urandom count=5
)
chown %{user_name}:%{user_name} %{secret_key}
chmod 0400 %{secret_key}

# link default certificate
if [ ! -e               %{_sysconfdir}/pki/tls/certs/softwarecollections.org.crt ]; then
    ln -s localhost.crt %{_sysconfdir}/pki/tls/certs/softwarecollections.org.crt
fi

# link default private key
if [ ! -e               %{_sysconfdir}/pki/tls/private/softwarecollections.org.key ]; then
    ln -s localhost.key %{_sysconfdir}/pki/tls/private/softwarecollections.org.key
fi

# link default chain file
if [ ! -e               %{_sysconfdir}/pki/tls/certs/softwarecollections.org.CA.crt ]; then
    ln -s localhost.crt %{_sysconfdir}/pki/tls/certs/softwarecollections.org.CA.crt
fi

# set selinux context
semanage fcontext -a -t httpd_sys_content_t  '%{scls_statedir}/htdocs(/.*)?'
semanage fcontext -a -t httpd_sys_content_t  '%{scls_statedir}/secret_key'
semanage fcontext -a -t postgresql_var_run_t '%{scls_statedir}/db(/\..*)?'
restorecon -R                                '%{scls_statedir}'
setsebool -P httpd_can_network_connect on
setsebool -P rsync_full_access on
setsebool -P nis_enabled on
setsebool -P httpd_unified on

service httpd condrestart

%{name}-db-setup
%{name} migrate       --noinput               || :
%{name} collectstatic --noinput --verbosity=1 || :
%{name} makeerrorpages                        || :
%{name}-services-setup


%preun
%systemd_preun softwarecollections-rsyncd.service

%postun
%systemd_postun_with_restart softwarecollections-rsyncd.service



%files
%doc LICENSE README.md
%{_bindir}/%{name}
%{_bindir}/%{name}-db-setup
%{_bindir}/%{name}-services-setup
%{_datadir}/bash-completion/completions/softwarecollections
%{python3_sitelib}/softwarecollections*
%config(noreplace) %{cron_confdir}/%{name}
%config(noreplace) %{httpd_confdir}/%{name}.conf
%config(noreplace) %{scls_confdir}/localsettings
%config(noreplace) %{scls_confdir}/rsyncd.conf
%{_unitdir}/softwarecollections-rsyncd.service
%{scls_statedir}/htdocs/wsgi.py*
%attr(755,root,root) %dir %{scls_statedir}/htdocs/static
%attr(775,root,%{group_name}) %dir %{scls_statedir}/htdocs/repos
%attr(775,root,%{group_name}) %dir %{scls_statedir}/htdocs/media
%attr(750,postgres,%{group_name}) %dir %{scls_statedir}/db
%ghost %{scls_statedir}/secret_key


%changelog
* Tue Sep 25 2018 Jan Staněk <jstanek@redhat.com> 0.17-1
- Make the codebase comaptible with Django 2.1
- Add basic/sanity test suite

* Tue Sep 04 2018 Jan Staněk <jstanek@redhat.com> 0.16-1
- Filter logging of DisallowedHost (jstanek@redhat.com)
- Add jstanek to admins (jstanek@redhat.com)

* Mon May 21 2018 Miroslav Suchý <msuchy@redhat.com> 0.15-1
- Update packaging-guide-1.tar.gz (pkovar@redhat.com)
- use more processes (msuchy@redhat.com)
- Make makesuperuser command compatible with Django 1.11 (jstanek@redhat.com)
- Fix of a typo, https://bugzilla.redhat.com/show_bug.cgi?id=1552615
  (mschorm@redhat.com)
- use django.shortcuts.render instead of render_to_response
  (jakub.dornak@misli.cz)
- Sort collections from newest by default (hhorak@redhat.com)
- Do not show downloads if there are none (hhorak@redhat.com)

* Thu Aug 24 2017 Miroslav Suchý <msuchy@redhat.com> 0.14-1
- Update packaging-guide (pkovar@redhat.com)
- typo in pagination.html (jakub.dornak@misli.cz)
- Update packaging-guide (pkovar@redhat.com)
- Add Dockerfile for development and a test that executes it
  (hhorak@redhat.com)
- Make sure pagination persists search options (cwt137@gmail.com)

* Wed Dec 14 2016 Jakub Dorňák <jakub.dornak@misli.cz> 0.13-1
- updated contact information and project url (jakub.dornak@misli.cz)
- softwarecollections-services-setup (jakub.dornak@misli.cz)
- added information on data migration (jdornak@redhat.com)
- deleted obsolete instruction (jdornak@redhat.com)
- copr can now build directly (msuchy@redhat.com)
- fixed url namespace (jakub.dornak@misli.cz)
- updated links in the footer (jakub.dornak@misli.cz)
- fixed error pages (jakub.dornak@misli.cz)
- Fedora 25 compatibility (jakub.dornak@misli.cz)
- new version of packaging guide (jakub.dornak@misli.cz)
- updated README.md (jdornak@redhat.com)
- Docs update per #90 (pkovar@redhat.com)
- default values for OtherRepo (jdornak@redhat.com)
- do not require input in %%post (jdornak@redhat.com)
- fixed has_content with other repos (jdornak@redhat.com)
- change CentOSRepo to OtherRepo (jdornak@redhat.com)
- change text of Issue Tracker (jdornak@redhat.com)
- do not delete synced repositories from disk (jdornak@redhat.com)
- new policy also needs httpd_unified to be on (jdornak@redhat.com)
- new Copr url (jdornak@redhat.com)
- set selinux nis_enabled on (jdornak@redhat.com)
- allow cron to enable temporarily disabled entries (jdornak@redhat.com)
- hide headlines for empty fields (jdornak@redhat.com)
- do not fail if Copr is not available (jdornak@redhat.com)
- drop bluehost logo (jdornak@redhat.com)
- first collect data, than open file for writing (jdornak@redhat.com)
- use logger instance instead of logging module (jdornak@redhat.com)
- Change suggested contact to mailing list (hhorak@redhat.com)
- prevent sclsync from running concurrently (jdornak@redhat.com)

* Fri Dec 11 2015 Jakub Dorňák <jdornak@redhat.com> 0.12-1
- CentOS repos (jdornak@redhat.com)
- Repo.get_download_url (jdornak@redhat.com)
- get_icon_url with param does not belong to Repo (jdornak@redhat.com)
- settings.TEMPLATES for Django > 1.8 (jdornak@redhat.com)
- allow rsync to serve files (jdornak@redhat.com)
- do not delete, it deletes *-release.rpm (jdornak@redhat.com)
- new option --all for command sclsync (jdornak@redhat.com)
- create repo directories if does not exist (jdornak@redhat.com)
- drop symlinking, it is not needed any more (jdornak@redhat.com)
- less irrelevant log output (jdornak@redhat.com)
- fixed selinux contexts (jdornak@redhat.com)
- fixed adduser and requirements in spec (jdornak@redhat.com)

* Fri Nov 27 2015 Jakub Dorňák <jdornak@redhat.com> 0.11-1
- switch production to postgresql (jdornak@redhat.com)
- ghost db.sqlite3 and secret_key, packaging (jdornak@redhat.com)
- softwarecollections-rsyncd.service (jdornak@redhat.com)

* Fri Oct 02 2015 Miroslav Suchý <msuchy@redhat.com> 0.10-1
- Fix remote exec flaw (misc@redhat.com)
- fix HttpResponse arg: mimetype > content_type (jdornak@redhat.com)
- don't check pkg signature in rpm query (asamalik@redhat.com)
- Change verbosity from string to int (asamalik@redhat.com)
- show downloads for every distro (asamalik@redhat.com)
- use import_string instead of import_by_path (jdornak@redhat.com)
- Requires python3-defusedxml (jdornak@redhat.com)
- Default value of 'RedirectView.permanent' will change from True to False in
  Django 1.9. (jdornak@redhat.com)
- updated index-header.html and index-footer.html (jdornak@redhat.com)
- replace deprecated requires_model_validation (jdornak@redhat.com)
- use default url template tag (jdornak@redhat.com)
- new bash-completion (jdornak@redhat.com)
- Fedora 22 compatibility (jdornak@redhat.com)
- set groups correctly (jdornak@redhat.com)
- disable cron by default (jdornak@redhat.com)
- include hostname in SERVER_MAIL (jdornak@redhat.com)
- use KEY_PREFIX for Memcache (jdornak@redhat.com)
- Update packaging-guide-1.tar.gz (pkovar@redhat.com)
- use FAS backend from separate package (jdornak@redhat.com)
- Update packaging-guide-1.tar.gz (pkovar@redhat.com)
- Add more links in faq.html (pkovar@redhat.com)
- Edits in add-to-catalogue.html (pkovar@redhat.com)
- Update docs.html (pkovar@redhat.com)
- Minor edits in about.html (pkovar@redhat.com)
- Minor edit in en.html (pkovar@redhat.com)
- httpd config: btter ssl security (asamalik@redhat.com)
- Update packaging-guide-1.tar.gz (pkovar@redhat.com)
- update of review instructions (asamalik@redhat.com)
- passing --delete to reposync (asamalik@redhat.com)
- createrepo fix (asamalik@redhat.com)
- scl toolbar reordered (asamalik@redhat.com)
- repeat createrepo if failed (asamalik@redhat.com)
- corrections (asamalik@redhat.com)
- help tooltip for approved tag (asamalik@redhat.com)
- Review process (asamalik@redhat.com)
- Add link to SO. (rkratky@redhat.com)
- Lang. and mark up corrections. (rkratky@redhat.com)
- scl toolbar, scl sections and buttons update (asamalik@redhat.com)
- set success_url after permission verification resolves #79
  (jdornak@redhat.com)
- breadcrumbs and improved toolbar in scl detail/edit/... (asamalik@redhat.com)
- refering to the StackOverflow instead of askbot (asamalik@redhat.com)
- scl instructions updated (asamalik@redhat.com)
- User detail improvement (asamalik@redhat.com)
- use memcached for caching and sessions resolves #76 (jdornak@redhat.com)
- use sort directly without cat (jdornak@redhat.com)
- Policy models updated (noncommittal). (rkratky@redhat.com)
- HP text corrections, additions. (rkratky@redhat.com)
- round borders on the homepage (asamalik@redhat.com)
- search box in the main menu (asamalik@redhat.com)
- docs & guides -> guides (rkratky@redhat.com)
- Remove target=blank from links. (rkratky@redhat.com)
- FAQ moved into docs (asamalik@redhat.com)
- using Red Hat Enterprise Linux instead of RHEL on the homepage
  (asamalik@redhat.com)
- Adding a new collection updated (asamalik@redhat.com)
- licensing guide moved into docs (asamalik@redhat.com)
- DeveloperWeek Award baner changed (asamalik@redhat.com)
- quick start section links (asamalik@redhat.com)
- New quick start by Robert Kratky (asamalik@redhat.com)
- homepage update (asamalik@redhat.com)
- [guide] breadcrumbs (asamalik@redhat.com)
- making paginator more intuitive (asamalik@redhat.com)
- allow to turn on/off DEBUG mode by environment var (jdornak@redhat.com)
- SERVER_EMAIL with application name and hostname (jdornak@redhat.com)
- use dump_provides() to get has_content resolves #74 (jdornak@redhat.com)
- Update guide-templatize (pkovar@redhat.com)
- Update packaging guide archive file (pkovar@redhat.com)
- Rename software-collections-guide to packaging-guide (pkovar@redhat.com)
- using breadcrumbs (asamalik@redhat.com)
- using unified color in the menu and on buttons (asamalik@redhat.com)
- login menu update (asamalik@redhat.com)
- Download repo buttons fix (asamalik@redhat.com)
- using h2 scl list (asamalik@redhat.com)
- css update - making the guide readable (asamalik@redhat.com)
- simplify guide import, skip front page (jdornak@redhat.com)
- use guide with format html-single (jdornak@redhat.com)
- Detail view: Approved, Report a bug and Report abuse icons changed
  (asamalik@redhat.com)
- quicktart page: scl guide link update (asamalik@redhat.com)
- use included source, build and import guide before setup.py build
  (jdornak@redhat.com)
- use explicitly utf-8 encoding for sys.std* in guide-templatize
  (jdornak@redhat.com)
- always expect AttributeError when calling del on cached_property resolves #66
  (jdornak@redhat.com)
- include software-collections-guide-1.tar.gz (for tito to be able to find it
  §:o( (jdornak@redhat.com)
- add software-collections-guide (jdornak@redhat.com)
- scl search form help + bootstrap tooltips enabled (asamalik@redhat.com)
- scl filter form updated (asamalik@redhat.com)
- scls list line fix (asamalik@redhat.com)
- DeveloperWeek Award on the homepage (asamalik@redhat.com)
- homepage polishing (asamalik@redhat.com)
- Merging with Robert's design changes (mstuchli@redhat.com)
- layout redesign pre-alpha (asamalik@redhat.com)
- Fix a minor typo (mstuchli@redhat.com)
- New title (asamalik@redhat.com)
- fedora logo update (asamalik@redhat.com)
- docs page divided + menu item macro (asamalik@redhat.com)
- generic instructions resolves #56 (jdornak@redhat.com)
- install database correctly (jdornak@redhat.com)
- create repo directory and symlink during repo creation (jdornak@redhat.com)
- drop repos cache correctly (jdornak@redhat.com)
- use the quotes consistently within the whole file (jdornak@redhat.com)
- Copr.detail and other (cached_)properties (jdornak@redhat.com)
- ft=python (jdornak@redhat.com)
- do not forget to commit the changes you do on the server (jdornak@redhat.com)
- updated README instructions, rel-eng/releasers.conf.template
  (jdornak@redhat.com)
- use cached_property (jdornak@redhat.com)
- update tito.props (jdornak@redhat.com)
- prevent command line interface from being run as root (jdornak@redhat.com)
- help texts (jdornak@redhat.com)
- check_call_log logging command line (jdornak@redhat.com)
- drop scl.copr_* fields, add {scl,repo}.has_contentfields, add form to manage
  attached Copr projects resolves #61 and #57 (jdornak@redhat.com)
- Yum Repositories table reorganized (asamalik@redhat.com)
- TableRenderer text correction (asamalik@redhat.com)
- policy texts simplified (asamalik@redhat.com)
- scl detail: moving owner's menu (asamalik@redhat.com)
- scl list redesign (asamalik@redhat.com)
- new model Copr to allow multiple Copr projects for one SCL
  (jdornak@redhat.com)
- branding in the admin site (jdornak@redhat.com)
- copy data after sync and remove download directory (msuchy@redhat.com)
- Link to symlink release RPM, not latest (dcleal@redhat.com)
- id for repo must be unique (msuchy@redhat.com)
- nice and responisve footer (jdornak@redhat.com)
- use icons instead of buttons for reporting resolves #54 (jdornak@redhat.com)
- remove left offset (col-sm-offset-1) resolves  #51 (jdornak@redhat.com)
- froms: use explicitly CheckboxFieldRenderer, RadioFieldRenderer
  (jdornak@redhat.com)
- Move and rename link to upstream (mstuchli@redhat.com)
- Add a link to ask.softwarecollection to topmost menu (mstuchli@redhat.com)
- use scl.get_copr_url (jdornak@redhat.com)
- append OK or FAILED to the log (jdornak@redhat.com)
- new command sclcreaterepo (and typo in commands sclrelated and sclrpms)
  (jdornak@redhat.com)
- log.exception instead log.error (jdornak@redhat.com)
- Add link to upstream to collection details (mstuchli@redhat.com)
- Optimize images (mstuchli@redhat.com)
- Enable compression in Apache (mstuchli@redhat.com)
- Add link to COPR repo to detailed view (mstuchli@redhat.com)
- log result code (msuchy@redhat.com)
- Create %%name.rpm symlink to release RPM for each repo (dcleal@redhat.com)
- fixed error handling in management commands (jdornak@redhat.com)
- LoggingBaseCommand (jdornak@redhat.com)
- exception handling and slug support in management commands
  (jdornak@redhat.com)
- admin action request_sync (jdornak@redhat.com)
- add last_synced (jdornak@redhat.com)
- Add migration adding issue_tracker (mstuchli@redhat.com)
- Add missing bracket (mstuchli@redhat.com)
- Add link to SCL.org COPR repo to footer (mstuchli@redhat.com)
- Add issue tracker field and button (mstuchli@redhat.com)
- SCL Admin: SCL detail link (jdornak@redhat.com)
- allow sync of particular SCL(s) (specified by slug) from commandline
  (jdornak@redhat.com)
- New Admin for SCLs: More information in the list, filtering, approving, etc.
  (jdornak@redhat.com)
- if commands succed, then we want to save the data (msuchy@redhat.com)
- sometimes the dir is just yum-<random> (msuchy@redhat.com)
- sync also sources from Copr (msuchy@redhat.com)
- rm production.js (empty file) (jdornak@redhat.com)
- added gpgcheck=0 (jdornak@redhat.com)
- Add link to website source code (dcleal@redhat.com)
- Use service, not init.d directly (dcleal@redhat.com)
- do not suggest to run yum -y (msuchy@redhat.com)
- fix broken link (msuchy@redhat.com)
- static error pages generated using templates (jdornak@redhat.com)

* Wed Apr 23 2014 Jakub Dorňák <jdornak@redhat.com> 0.9-1
- command sclprovides (jdornak@redhat.com)
- list related collections on collection detail (jdornak@redhat.com)
- find related collections (jdornak@redhat.com)
- dummy migration related to 0c75cfcbf9c093554db748fea872c80339a6e044
  (jdornak@redhat.com)
- sclsync with multiprocessing generates lists of RPM provides
  (jdornak@redhat.com)
- share yum.config for all repos in one collection (jdornak@redhat.com)
- fix workaround to really work (jdornak@redhat.com)
- delete synced RPMs on repo.delete() (jdornak@redhat.com)
- do not display browse link until synced (jdornak@redhat.com)
- _new => _blank (jdornak@redhat.com)
- rpmbuild params for EPEL5 packages (jdornak@redhat.com)
- menu item active for all subpages (jdornak@redhat.com)
- nice index header and current year in footer (jdornak@redhat.com)
- fix chain file path (jdornak@redhat.com)
- AddIcon rpm.png .rpm (jdornak@redhat.com)

* Wed Apr 09 2014 Miroslav Suchý <msuchy@redhat.com> 0.8-1
- add google analytics code (msuchy@redhat.com)
- license (jdornak@redhat.com)
- add SSLCertificateChainFile to the config file (jdornak@redhat.com)

* Tue Apr 08 2014 Miroslav Suchý <msuchy@redhat.com> 0.7-1
- add Licensing Guidelines (msuchy@redhat.com)
- redirect scl.org to www.scl.org, which better corresponds to the certificate
  values (jdornak@redhat.com)
- yet again fix policies (msuchy@redhat.com)
- fix typo (msuchy@redhat.com)
- ServerAlias *, ServerAdmin admin@softwarecollections.org (jdornak@redhat.com)
- invalid syntax in policy texts (jdornak@redhat.com)
- nice, branded directory listing (jdornak@redhat.com)
- change policy texts one more time (msuchy@redhat.com)
- filter by distro, distro-version, arch (jdornak@redhat.com)
- Revert "send email as admin@softwarecollections.org" (jdornak@redhat.com)
- Bluehost logo (jdornak@redhat.com)
- send email as admin@softwarecollections.org (msuchy@redhat.com)
- use a temp dir for storing/accessing yum-cache (msuchy@redhat.com)
- workaround BZ 1079387 (msuchy@redhat.com)
- make debugging easier (msuchy@redhat.com)
- Links to mailing list (tradej@redhat.com)
- Pretty pagination (tradej@redhat.com)
- do not include insecure content (jdornak@redhat.com)
- copyright year adjusted to current year (jdornak@redhat.com)
- drop www subdomain and unnecessary SSL directives (jdornak@redhat.com)
- add redirection of softwarecollections.org without www (jdornak@redhat.com)
- Requires: python3-django-simple-captcha (jdornak@redhat.com)
- change policy labels (msuchy@redhat.com)
- move scls related commands to the right place (jdornak@redhat.com)
- sync request after the import (jdornak@redhat.com)
- we should not call the maintainer "Author" (jdornak@redhat.com)
- add captcha to ComplainForm (jdornak@redhat.com)
- use form's self.object (jdornak@redhat.com)
- allow user to mark "bad content" (jdornak@redhat.com)
- Redesigned collections list + added download count (tradej@redhat.com)
- allow + in the name (jdornak@redhat.com)
- Mailing list mention on home page (tradej@redhat.com)
- Code indentation on home page (tradej@redhat.com)
- DeveloperWeek Award (tradej@redhat.com)
- merge scls/static/scls/style.css to static/stylesheets/custom.css
  (jdornak@redhat.com)
- always sync all repos, user may enable / disable repos any time
  (jdornak@redhat.com)
- use truncate tag instead of truncate filter (jdornak@redhat.com)
- truncate_tags (jdornak@redhat.com)
- new command sclrpms (jdornak@redhat.com)
- just comments (jdornak@redhat.com)
- also add username to rpmname (jdornak@redhat.com)
- allow more repos of the same collection to be installed (jdornak@redhat.com)
- truncating markdown text may lead to wrong markdown parsing, truncate the
  final html instead (jdornak@redhat.com)
- notify managers on approval request (jdornak@redhat.com)
- Fixed the voting stars appearance (tradej@redhat.com)
- Approved collections show as such (tradej@redhat.com)
- display message about success after any action (jdornak@redhat.com)
- do not limit the lenght of tags (jdornak@redhat.com)
- safe markdown (jdornak@redhat.com)
- fixed scls:download reverse (jdornak@redhat.com)
- Don't refresh copr projects list if it's already loaded (bkabrda@redhat.com)
- validate_name (jdornak@redhat.com)
- Refactor JS for importing/editing SCL: (bkabrda@redhat.com)
- always order by 'approved' flag, default order by download_count
  (jdornak@redhat.com)
- Merge pull request #31 from sochotnicky/feature-docs-rework
  (jdornak@redhat.com)
- End the repo file download url with rpm name (sochotnicky@redhat.com)
- [docs] Rework documentation and quickstart (sochotnicky@redhat.com)
- rename scls/preview.html to scls/softwarecollection_preview.html
  (jdornak@redhat.com)
- class page-header in forms (jdornak@redhat.com)
- auto_sync help_text (jdornak@redhat.com)
- collaborators explanation text (TODO) (jdornak@redhat.com)
- move button 'delete' from the beginning to the end (jdornak@redhat.com)
- fix title in sync_req.html (jdornak@redhat.com)
- review_req form (jdornak@redhat.com)
- sync_req form (jdornak@redhat.com)
- scl.get_copr_url() (jdornak@redhat.com)
- use repo.disro.title() in ReposForm (jdornak@redhat.com)
- Use jQuery for stars manipulation (bkabrda@redhat.com)
- Merge pull request #25 from bkabrda/master (bkabrda@redhat.com)
- Truncated description in listing (tradej@redhat.com)
- Removed stray div (tradej@redhat.com)
- Fix Dockerfile to properly create 'test' user (bkabrda@redhat.com)
- display tags on collection detail only (jdornak@redhat.com)
- Add Dockerfile for development and some instructions on how to build/run it
  (bkabrda@redhat.com)
- Fixed fonts (tradej@redhat.com)
- less auto tags (jdornak@redhat.com)
- fix obj / scl renaming (jdornak@redhat.com)
- default policy DEV (jdornak@redhat.com)
- remove back button from import form (jdornak@redhat.com)
- allow user to leave all edit forms without saving (jdornak@redhat.com)
- Use form for deleting (jdornak@redhat.com)
- help_texts (jdornak@redhat.com)
- allow user to enable / disable particular repos (jdornak@redhat.com)
- do not process language files (we do not provide translations yet)
  (jdornak@redhat.com)
- Beautified the Collaborators form (tomas@radej.cz)
- Repo URL in detail (tomas@radej.cz)
- Fixed fonts (tomas@radej.cz)
- featured scl forms (jdornak@redhat.com)
- fix error messages in scl forms (jdornak@redhat.com)
- sample doc text for import (TODO) (jdornak@redhat.com)
- copr > Copr (and spaces) (jdornak@redhat.com)
- collaborators.add.help_text (jdornak@redhat.com)
- drop locale files (containing bad translation) (jdornak@redhat.com)
- Filtering by policies (tomas@radej.cz)
- Pretty policy table (tomas@radej.cz)
- Typo in repo list (tomas@radej.cz)
- Button colours changed to grey (tomas@radej.cz)
- configure logging (jdornak@redhat.com)
- apache must be able to manage repos (jdornak@redhat.com)
- add ADMINS and SERVER_EMAIL to localsettings.py (jdornak@redhat.com)
- generate unique SECURE_KEY during installation (jdornak@redhat.com)
- Polishing (tradej@redhat.com)
- Merge remote-tracking branch 'origin/master' (tradej@redhat.com)
- Polishing (tradej@redhat.com)
- New Collection form (tradej@redhat.com)
- New Collection form (tradej@redhat.com)
- add collaborator by username (select may be too long) (jdornak@redhat.com)
- rework deleting, allow copr change, help_texts (jdornak@redhat.com)
- New Collection page (tradej@redhat.com)
- SCL toolbar (tradej@redhat.com)
- Collections (tradej@redhat.com)
- Sticky footer (tradej@redhat.com)
- CSS fixes (tradej@redhat.com)
- FAQ bug (tradej@redhat.com)
- Top menu + Jumbotron fixed (tradej@redhat.com)
- Link to Manage collaborators (msimacek@redhat.com)
- Allow managing comaintainers (msimacek@redhat.com)
- Fix edit collection title (msimacek@redhat.com)
- Markup fix in quick_start (msimacek@redhat.com)
- Replaced old Bootstrap with 3.1.1 (tradej@redhat.com)
- acquire exclusive lock on repos while syncing repos (jdornak@redhat.com)
- delete repo in scl.delete() (jdornak@redhat.com)
- cronjob for deleting files (msimacek@redhat.com)
- command to delete collections marked for deletion (msimacek@redhat.com)
- delete possible zombie scl when creating new (msimacek@redhat.com)
- mark collections for deletion by delete field (msimacek@redhat.com)
- allow user to delete collection (msimacek@redhat.com)
- fix dangling links on homepage (msimacek@redhat.com)
- drop last_sync_date, use last_modified from copr (jdornak@redhat.com)
- createrepo_c is MUCH better (msuchy@redhat.com)
- require cron (msuchy@redhat.com)
- 5 per page was just for testing (jdornak@redhat.com)
- fix order option names (jdornak@redhat.com)
- add ordering (jdornak@redhat.com)
- drop unused configuration option (jdornak@redhat.com)
- use nice url using srcurl.net (jdornak@redhat.com)
- scl.download_count: increment on download, recalculate on sync
  (jdornak@redhat.com)
- error pages (jdornak@redhat.com)
- pagination (jdornak@redhat.com)
- attach style to list of collections (jdornak@redhat.com)
- simple search / filter form (jdornak@redhat.com)
- distro icons for epel and fedora (jdornak@redhat.com)
- fixed migration (jdornak@redhat.com)
- [doc] Update documentation by sclo-build package. (mmaslano@redhat.com)
- count downloads (jdornak@redhat.com)
- distro version as part of RPM name - it may be string ('rawhide')
  (jdornak@redhat.com)
- add field repo.slug (jdornak@redhat.com)
- print name of collection when starting sync (jdornak@redhat.com)
- create yum config RPMs (jdornak@redhat.com)
- sclsync to provide some error information (jdornak@redhat.com)
- shorter /var/scls instead of /var/lib/softwarecollections
  (jdornak@redhat.com)
- we do not need createsamplecollections any more (jdornak@redhat.com)
- Improve yum cache handling (msrb@redhat.com)
- [doc] Update content of quick-start. (mmaslano@redhat.com)
- Document distribution. (mmaslano@redhat.com)
- auto tags (jdornak@redhat.com)
- macro is called scl_basedir and not _scl_basedir (msuchy@redhat.com)
- macro is called scl_vendor and not _scl_vendor (msuchy@redhat.com)
- browser does not import the font definition, until it is secure
  (jdornak@redhat.com)
- "addtoblock" must be inside "block" (jdornak@redhat.com)
- nice alt texts for stars (jdornak@redhat.com)
- scl-toolbar (needs icons) (jdornak@redhat.com)
- render score input as form field (jdornak@redhat.com)
- use sekizai for page specific javascripts and styles (jdornak@redhat.com)
- new urls (jdornak@redhat.com)
- move form logic from views to forms (jdornak@redhat.com)
- tags really editable (jdornak@redhat.com)
- avoid double / in copr request url (jdornak@redhat.com)
- copr_project with choices (jdornak@redhat.com)
- destdir is part of configuration (jdornak@redhat.com)
- Add support for adding and editing tags in owned collections
  (sochotnicky@redhat.com)
- another big bang (jdornak@redhat.com)
- added scl.repos, some dates and flags (jdornak@redhat.com)
- %%post syncdb and collectstatic (jdornak@redhat.com)
- List user's coprs when creating new scl (msimacek@redhat.com)
- enabled markdown in text fields (jdornak@redhat.com)
- import cleanup (jdornak@redhat.com)
- updated star rating (jdornak@redhat.com)
- add star rating system for collections (msimacek@redhat.com)
- use correct class name (msuchy@redhat.com)
- require Django 1.6 (jdornak@redhat.com)
- display yum repository in details (msuchy@redhat.com)
- production repos are in /var/scl-repos (msuchy@redhat.com)
- add command to manage.py in cron (msuchy@redhat.com)
- maintainer is always collaborator (jdornak@redhat.com)
- renamed 'directory' to 'collections' (jdornak@redhat.com)
- edit view with per object permissions (jdornak@redhat.com)
- softwarecollections.auth handles per object permissions and provides template
  tag 'allowed' (jdornak@redhat.com)
- add real policy texts (msuchy@redhat.com)
- new create form (jdornak@redhat.com)
- single text field for policy, new flag 'accepted' (jdornak@redhat.com)
- requires python3-django-south (jdornak@redhat.com)
- updated README (jdornak@redhat.com)
- cron file under conf dir (jdornak@redhat.com)
- added data directory for the development instance to be more like the
  production one (jdornak@redhat.com)
- repos under the document_root (jdornak@redhat.com)
- added missing requirements (jdornak@redhat.com)
- using messages (need some styles) (jdornak@redhat.com)
- updated README (jdornak@redhat.com)
- start usgin south (jdornak@redhat.com)
- username and name unique (jdornak@redhat.com)
- [spec] restart apache after upgrade (msuchy@redhat.com)
- own /var/scl-repos (msuchy@redhat.com)
- [doc] Make must for /opt/sclo more readable. (mmaslano@redhat.com)
- [doc] In development documentation are now mentioned macros, which can
  redefine installation path. (mmaslano@redhat.com)
- Make the example of metapackage more readable. Add link to documentation
  maintained by documentation guys from Fedora. (mmaslano@redhat.com)
- Update README.md with needed packages. (mmaslano@redhat.com)
- even better handling of scl.copr (jdornak@redhat.com)
- Add cron job (msrb@redhat.com)
- Initial version of django command for synchronizing with copr repos
  (msrb@redhat.com)
- Add "need_sync" column to the scls_softwarecollection table (msrb@redhat.com)
- Add missing Requires to spec file (msrb@redhat.com)
- ensure scl.copr is available if possible (jdornak@redhat.com)
- SoftwareCollection connected with Copr (jdornak@redhat.com)
- cool copr submodule (jdornak@redhat.com)
- SoftwareCollection fields: -name, -version, +copr_user, +copr_project
  (jdornak@redhat.com)
- require login for view scls:list_my (jdornak@redhat.com)
- FAS login without django-social (jdornak@redhat.com)
- tuple urls with namespaces (jdornak@redhat.com)
- unique score for each collection and user (jdornak@redhat.com)
- more on views (jdornak@redhat.com)
- Move DEFAULT_COPR_API_URL to settings.py (mstuchli@redhat.com)
- Exception.args is supposed to be list, not str (jdornak@redhat.com)
- more on views (jdornak@redhat.com)
- use User instead of UserModel (jdornak@redhat.com)
- initial views: detail, create (jdornak@redhat.com)
- new property scl.slug (jdornak@redhat.com)
- validate scl.version (jdornak@redhat.com)
- always include softwarecollections/* (jdornak@redhat.com)
- missing __init__.py in pages submodule (jdornak@redhat.com)
- utils do not need to be executable (jdornak@redhat.com)
- use separate application for collections management (jdornak@redhat.com)
- use separated submodule and template dir for pages (jdornak@redhat.com)
- Add cli subcommand for syncing COPR repos (mstuchli@redhat.com)
- note about makesuperuser and createsamplecollections in README.md
  (jdornak@redhat.com)
- pagination in softwarecollections_list.html (jdornak@redhat.com)
- temporary script for creating sample set of collections in database
  (jdornak@redhat.com)
- get username from openid.sreg.nickname (jdornak@redhat.com)
- new fields and relations: update_freq, rebase_policy, maturity, score,
  maintainer, collaborators (jdornak@redhat.com)
- SoftwareCollection.tags (jdornak@redhat.com)
- cli subcommand to make user a superuser (jdornak@redhat.com)

* Fri Nov 29 2013 Jakub Dorňák <jdornak@redhat.com> 0.6-1
- Document definition of _scl_prefix in For Developers and link it from Quick
  start. (mmaslano@redhat.com)
- fas authentication (jdornak@redhat.com)

* Thu Nov 28 2013 Jakub Dorňák <jdornak@redhat.com> 0.5-1
- fixed BuildRequires to build in copr (mock) (jdornak@redhat.com)
- minimized dependencies (jdornak@redhat.com)
- fix README format (jdornak@redhat.com)
- updated README (jdornak@redhat.com)
- use version in setup.py directly (msuchy@redhat.com)

* Thu Nov 28 2013 Jakub Dorňák <jdornak@redhat.com> 0.4-1
- changed deployment to httpd and mod_wsgi-python3 (jdornak@redhat.com)
- rel-eng releasers (jdornak@redhat.com)

* Wed Nov 27 2013 Jakub Dorňák <jdornak@redhat.com> 0.3-1
- new package built with tito

* Tue Nov 26 2013 Jakub Dorňák <jdornak@redhat.com> - 0.1-2
- use python3 and django-1.6
- use static pages instead of django-cms

* Thu Nov 21 2013 Jakub Dorňák <jdornak@redhat.com> - 0.1-1
- Initial commit

