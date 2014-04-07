Name:		%{pkg_name}
Version:	%{pkg_version}
Release:	%{pkg_release}
Summary:	%{scl_title} Repository Configuration

Group:		System Environment/Base
License:	BSD
URL:		https://www.softwarecollections.org
BuildArch:	noarch

%description
%{scl_description}

%prep
echo "Nothing to prep"

%build
echo "Nothing to build"

%install
mkdir -p %{buildroot}%{_sysconfdir}/yum.repos.d
cat >    %{buildroot}%{_sysconfdir}/yum.repos.d/%{pkg_name}.repo <<EOF
[%{pkg_name}]
name=%{scl_title} - %{repo_name}
baseurl=https://www.softwarecollections.org%{repo_baseurl}
enabled=1
EOF

%files
%config(noreplace) %{_sysconfdir}/yum.repos.d/*

%changelog
* Tue Mar 11 2014 Jakub Dorňák <jdornak@redhat.com> - 1-1
- Initial package
