%global  scls_statedir %{_localstatedir}/lib/softwarecollections
%global  scls_confdir  %{_sysconfdir}/softwarecollections
%global  httpd_confdir %{_sysconfdir}/httpd/conf.d
%global  httpd_group   apache

Name:              softwarecollections
Version:           0.6
Release:           1%{?dist}

Summary:           Software Collections Management Website and Utils
Group:             System Environment/Daemons
License:           TODO
URL:               http://softwarecollections.org/

Source0:           https://codeload.github.com/misli/%{name}/tar.gz/%{version}?filename=%{name}-%{version}.tar.gz

BuildArch:         noarch

BuildRequires:     python3-devel
BuildRequires:     python3-setuptools

Requires:          httpd
Requires:          mod_ssl
Requires:          python3-mod_wsgi
Requires:          python3-django
Requires:          python3-django-tagging
Requires:          createrepo
Requires:          yum-utils

%description
Software Collections Management Website and Utils


%prep
%setup -q


%build
rm %{name}/localsettings-development.py
mv %{name}/localsettings-production.py localsettings
mv %{name}/wsgi.py htdocs/
%{__python3} setup.py build
mkdir data


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

# install separate directory for sqlite db
install -p -d -m 0775 data \
     %{buildroot}%{scls_statedir}/data

# install crontab
install -p -D -m 0644 sclsync-cron \
    %{buildroot}%{_sysconfdir}/cron.d/sclsync

# remove .po files
find %{buildroot} -name "*.po" | xargs rm -f

# create file list
(cd %{buildroot}; find *) | egrep -v '\.mo$' | \
sed -r -e 's|\.py[co]?$|.py*|' -e 's|__pycache__.*$|__pycache__/*|' | sort -u | \
while read FILE; do
    [ -d "%{buildroot}/$FILE" ] && echo "%dir /$FILE" || echo "/$FILE"
done | grep %{python3_sitelib} > %{name}.files

# add language files
%find_lang django
cat django.lang >> %{name}.files


%files -f %{name}.files
%doc LICENSE README.md
%{_bindir}/%{name}
%{_sysconfdir}/bash_completion.d/%{name}_bash_completion
%config(noreplace) %{httpd_confdir}/%{name}.conf
%config(noreplace) %{scls_confdir}/localsettings
%config(noreplace) %{_sysconfdir}/cron.d/sclsync
%{scls_statedir}/htdocs/wsgi.py*
%dir %{scls_statedir}/htdocs/static
%attr(775,root,%{httpd_group}) %dir %{scls_statedir}/htdocs/media
%attr(775,root,%{httpd_group}) %dir %{scls_statedir}/data


%changelog
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

