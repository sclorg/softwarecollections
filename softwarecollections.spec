%global  scls_statedir %{_localstatedir}/scls
%global  scls_confdir  %{_sysconfdir}/softwarecollections
%global  cron_confdir  %{_sysconfdir}/cron.d
%global  httpd_confdir %{_sysconfdir}/httpd/conf.d
%global  httpd_group   apache

Name:              softwarecollections
Version:           0.7
Release:           1%{?dist}

Summary:           Software Collections Management Website and Utils
Group:             System Environment/Daemons
License:           TODO
URL:               http://softwarecollections.org/
Source0:           http://github.srcurl.net/misli/%{name}/%{version}/%{name}-%{version}.tar.gz

BuildArch:         noarch

BuildRequires:     python3-devel
BuildRequires:     python3-setuptools

Requires:          createrepo_c
Requires:          cronie
Requires:          flite
Requires:          httpd
Requires:          mod_ssl
Requires:          python3-django >= 1.6
Requires:          python3-django-markdown2
Requires:          python3-django-sekizai
Requires:          python3-django-simple-captcha
Requires:          python3-django-south
Requires:          python3-django-tagging
Requires:          python3-flock
Requires:          python3-mod_wsgi
Requires:          python3-openid
Requires:          python3-pillow
Requires:          python3-requests
Requires:          rpm-build
Requires:          yum-utils
Requires:          MTA

%description
Software Collections Management Website and Utils


%prep
%setup -q


%build
rm %{name}/localsettings-development.py
mv %{name}/localsettings-production.py localsettings
mv %{name}/wsgi.py htdocs/
%{__python3} setup.py build


%install
# install python package
%{__python3} setup.py install --skip-build --root %{buildroot}

# install conf file as target of localsettings.py symlink
install -p -D -m 0644 localsettings \
    %{buildroot}%{scls_confdir}/localsettings
ln -s %{scls_confdir}/localsettings \
    %{buildroot}%{python3_sitelib}/%{name}/localsettings.py

# install commandline interface with bash completion
install -p -D -m 0755 manage.py %{buildroot}%{_bindir}/%{name}
install -p -D -m 0644 %{name}_bash_completion \
    %{buildroot}%{_sysconfdir}/bash_completion.d/%{name}_bash_completion

# install httpd config file and wsgi config file
install -p -D -m 0644 conf/httpd/%{name}.conf \
    %{buildroot}%{httpd_confdir}/%{name}.conf
install -p -D -m 0644 htdocs/wsgi.py \
    %{buildroot}%{scls_statedir}/htdocs/wsgi.py

# install directories for static content and site media
install -p -d -m 0755 htdocs/static \
    %{buildroot}%{scls_statedir}/htdocs/static
install -p -d -m 0775 htdocs/media \
    %{buildroot}%{scls_statedir}/htdocs/media
install -p -d -m 0775 htdocs/repos \
    %{buildroot}%{scls_statedir}/htdocs/repos

# install separate directory for sqlite db
install -p -d -m 0775 data \
     %{buildroot}%{scls_statedir}/data

# install crontab
install -p -D -m 0644 conf/cron/%{name} \
    %{buildroot}%{cron_confdir}/%{name}

# remove .po files
find %{buildroot} -name "*.po" | xargs rm -f

# create file list
(cd %{buildroot}; find *) | egrep -v '\.mo$' | \
sed -r -e 's|\.py[co]?$|.py*|' -e 's|__pycache__.*$|__pycache__/*|' | sort -u | \
while read FILE; do
    [ -d "%{buildroot}/$FILE" ] && echo "%dir /$FILE" || echo "/$FILE"
done | grep %{python3_sitelib} > %{name}.files

# add language files
# (uncomment next two lines to process language files)
#%find_lang django
#cat django.lang >> %{name}.files

%post
# create secret key
if [ ! -e        %{scls_statedir}/secret_key ]; then
    touch        %{scls_statedir}/secret_key
    chown apache %{scls_statedir}/secret_key
    chgrp apache %{scls_statedir}/secret_key
    chmod 0400   %{scls_statedir}/secret_key
    dd bs=1k  of=%{scls_statedir}/secret_key if=/dev/urandom count=5
fi

# link default certificate
if [ ! -e               %{_sysconfdir}/pki/tls/certs/softwarecollections.org.crt ]; then
    ln -s localhost.crt %{_sysconfdir}/pki/tls/certs/softwarecollections.org.crt
fi

# link default private key
if [ ! -e               %{_sysconfdir}/pki/tls/private/softwarecollections.org.key ]; then
    ln -s localhost.key %{_sysconfdir}/pki/tls/private/softwarecollections.org.key
fi

service httpd condrestart
su apache - -s /bin/bash -c "softwarecollections syncdb --migrate --noinput"
softwarecollections collectstatic --noinput

%files -f %{name}.files
%doc LICENSE README.md
%{_bindir}/%{name}
%{_sysconfdir}/bash_completion.d/%{name}_bash_completion
%config(noreplace) %{cron_confdir}/%{name}
%config(noreplace) %{httpd_confdir}/%{name}.conf
%config(noreplace) %{scls_confdir}/localsettings
%{scls_statedir}/htdocs/wsgi.py*
%dir %{scls_statedir}/htdocs/static
%attr(775,root,%{httpd_group}) %dir %{scls_statedir}/htdocs/repos
%attr(775,root,%{httpd_group}) %dir %{scls_statedir}/htdocs/media
%attr(775,root,%{httpd_group}) %dir %{scls_statedir}/data


%changelog
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

