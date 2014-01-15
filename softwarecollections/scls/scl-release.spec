Name:		%{scl_name}-%{repo_name}
Version:	%{repo_version}
Release:	%{repo_release}
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
cat >    %{buildroot}%{_sysconfdir}/yum.repos.d/%{scl_name}.repo <<EOF
[%{scl_name}-%{repo_name}]
name=%{scl_title} - %{repo_name}
baseurl=https://www.softwarecollections.org%{repo_baseurl}
enabled=1
EOF

%files
%config(noreplace) %{_sysconfdir}/yum.repos.d/*

%changelog
* Mon Jan 13 2014 Jakub Dorňák <jdornak@redhat.com> - %{version}-%{release}
- Initial version
