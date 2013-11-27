%global  scls_user     sclsweb
%global  scls_group    %{scls_user}
%global  scls_statedir %{_localstatedir}/lib/softwarecollections
%global  scls_confdir  %{_sysconfdir}/softwarecollections
%global  nginx_confdir %{_sysconfdir}/nginx/sites-available

Name:              softwarecollections
Version:           0.2
Release:           1%{?dist}

Summary:           Software Collections Management Website and Utils
Group:             System Environment/Daemons
License:           TODO
URL:               http://softwarecollections.org/

Source0:           https://codeload.github.com/misli/%{name}/tar.gz/%{version}?filename=%{name}-%{version}.tar.gz

BuildArch:         noarch

Requires:          nginx
Requires:          python3-django
Requires:          python3-django-sekizai
Requires:          python3-flup
Requires:          python3-setproctitle

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
%{__python3} setup.py build


%install
%{__python3} setup.py install --skip-build --root %{buildroot}

install -p -D -m 0644 localsettings \
    %{buildroot}%{scls_confdir}/localsettings
ln -s %{scls_confdir}/localsettings \
    %{buildroot}%{python3_sitelib}/%{name}/localsettings.py

install -p -D -m 0755 manage.py %{buildroot}%{_bindir}/%{name}

install -p -D -m 0644 conf/systemd/%{name}.service \
    %{buildroot}%{_unitdir}/%{name}.service

install -p -D -m 0644 conf/nginx/%{name}.conf \
    %{buildroot}%{nginx_confdir}/%{name}.conf

install -p -d -m 0755 htdocs/static \
    %{buildroot}%{scls_statedir}/htdocs/static

install -p -d -m 0755 htdocs/media \
    %{buildroot}%{scls_statedir}/htdocs/media


# remove .po files
find %{buildroot} -name "*.po" | xargs rm -f

# create file list
(cd %{buildroot}; find *) | egrep -v '\.mo$' | sed -r 's/\.py[co]?$/.py*/' | sort -u | \
while read FILE; do
    [ -d "%{buildroot}/$FILE" ] && echo "%dir /$FILE" || echo "/$FILE"
done | grep %{python3_sitelib} > %{name}.files

# add language files
%find_lang django
cat django.lang >> %{name}.files


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


%files -f %{name}.files
%doc LICENSE README.md
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%{nginx_confdir}/%{name}.conf
%config(noreplace) %{scls_confdir}/localsettings
%attr(770,root,%{scls_group}) %dir %{scls_statedir}
%attr(770,root,%{scls_group}) %dir %{scls_statedir}/htdocs/media
%attr(750,root,%{scls_group}) %dir %{scls_statedir}/htdocs/static


%changelog
* Tue Nov 26 2013 Jakub Dorňák <jdornak@redhat.com> - 0.1-2
- use python3 and django-1.6
- use static pages instead of django-cms

* Thu Nov 21 2013 Jakub Dorňák <jdornak@redhat.com> - 0.1-1
- Initial commit

