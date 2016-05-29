Name: cvprac
Version: Replaced_by_make
Release: 1%{?dist}
Summary: REST API client for communicating with an Arista Cloudvision(R) Portal node.

Group: Development/Libraries
License: BSD (3-clause)
URL: http://www.arista.com
Source0: %{name}-%{version}.tar.gz
BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
The cvprac package is part of the devops library for EOS developed by Arista. The cvprac provides a python REST API client for communicating with an Arista Cloudvision(R) Portal node.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%postun

%files
%defattr(-,root,root,-)
%{python_sitelib}/cvprac*

%changelog
* Thu Apr 19 2016 John Corbin
-- Initial Build.
