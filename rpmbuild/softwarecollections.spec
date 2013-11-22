%global  scls_user     sclsweb
%global  scls_group    %{scls_user}
%global  scls_statedir %{_localstatedir}/lib/softwarecollections
%global  scls_confdir  %{_sysconfdir}/softwarecollections
%global  nginx_confdir %{_sysconfdir}/nginx/sites-available

Name:              softwarecollections
Version:           0.1
Release:           1%{?dist}

Summary:           Software Collections Management Website and Utils
Group:             System Environment/Daemons
License:           TODO
URL:               http://softwarecollections.org/

Source0:           https://github.com/misli/%{name}/archive/%{version}.zip?filename=%{name}-%{version}.zip

BuildArch:         noarch

Requires:          nginx
Requires:          python-django
Requires:          python-django-mptt
Requires:          python-django-south
Requires:          python-flup
Requires:          python-html5lib
Requires:          python-pillow
Requires:          python-setproctitle
Requires:          python-simplejson
Requires:          python-six

BuildRequires:     systemd
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd

%description
Software Collections Management Website and Utils


%prep
%setup -q


%build
rm %{name}/localsettings-development.py
mv %{name}/localsettings-production.py localsettings
%{__python} setup.py build


%install
%{__python} setup.py install --skip-build --root %{buildroot}

install -p -D -m 0644 localsettings \
    %{buildroot}%{scls_confdir}/localsettings
ln -s %{scls_confdir}/localsettings \
    %{buildroot}%{python_sitelib}/%{name}/localsettings.py

install -p -D -m 0755 manage.py %{buildroot}%{_bindir}/%{name}

install -p -D -m 0644 conf/systemd/%{name}.service \
    %{buildroot}%{_unitdir}/%{name}.service

install -p -D -m 0644 conf/nginx/%{name}.conf \
    %{buildroot}%{nginx_confdir}/%{name}.conf

install -p -d -m 0755 htdocs/static \
    %{buildroot}%{scls_statedir}/htdocs/static

install -p -d -m 0755 htdocs/media \
    %{buildroot}%{scls_statedir}/htdocs/media

cp -a %{name}/static %{name}/templates \
    %{buildroot}%{python_sitelib}/%{name}/

find %{name}/static %{name}/templates -type f \
    | sed 's|^|%{python_sitelib}/|' > files

%pre
getent group  %{scls_group} > /dev/null || \
    groupadd -r %{scls_group}
getent passwd %{scls_user}  > /dev/null || \
    useradd -r -d %{scls_statedir} -g %{scls_group} \
    -s /sbin/nologin -c "Software Collections Management Website" %{scls_user}
groups nginx | grep -q '\b%{scls_group}\b' || \
    usermod nginx -a -G %{scls_group}
exit 0


%post
%systemd_post softwarecollections.service


%preun
%systemd_preun softwarecollections.service


%postun
%systemd_postun softwarecollections.service


%files -f files
%doc LICENSE README.md
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%{nginx_confdir}/%{name}.conf
%config(noreplace) %{scls_confdir}/localsettings
%dir %{python_sitelib}/%{name}
%{python_sitelib}/%{name}/*.py*
%dir %{python_sitelib}/%{name}/management
%{python_sitelib}/%{name}/management/*.py*
%dir %{python_sitelib}/%{name}/management/commands
%{python_sitelib}/%{name}/management/commands/*.py*
%{python_sitelib}/*.egg-info
%attr(770,root,%{scls_group}) %dir %{scls_statedir}
%dir %{scls_statedir}/htdocs/static
%attr(770,root,%{scls_group}) %dir %{scls_statedir}/htdocs/media


%changelog
* Thu Nov 21 2013 Jakub Dorňák <jdornak@redhat.com> - 0.1-1
- Initial commit

