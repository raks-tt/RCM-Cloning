Name:	        rcm-cloning-tool	
Version:	0.5.1	
Release:	1%{?dist}
Summary:	A collection of scripts used by RCM for cloning JIRA Tickets	

License:       GPLv3+ 		
URL:   		https://github.com/raks-tt/RCM-Cloning.git 	 
Source0:       %{name}-%{version}.tar.gz	

BuildArch: noarch
BuildRequires: python
Requires: python
Requires: bash

%description
A collection of scripts used by RCM for cloning JIRA Tickets

%prep
%setup -cn rcm-cloning-tool  

%build

%install
mkdir -p "$RPM_BUILD_ROOT/%{_bindir}" 
%{echo $PWD}
cp -R /%{name}-%{version}/src/* "$RPM_BUILD_ROOT/%{_bindir}"


%clean
rm -rf $RPM_BUILD_ROOT

%files
%doc README.md
%doc src/README.md
%docdir src/*.md
%license LICENSE

%changelog
* Tue Jan 02 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.5.1-1
- new package built with tito

* Tue Jan 02 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.4.1-1
- new package built with tito

* Tue Jan 02 2018 Raksha Rajashekar <rrajashe@redhat.com>
- new package built with tito

* Tue Jan 02 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.3.1-1
- new package built with tito

* Tue Jan 02 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.2.1-1
- new package built with tito

* Fri Dec 29 2017 Raksha Rajashekar <rrajashe@redhat.com> 0.1.1-1
- new package built with tito

* Wed Dec 27 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.2.0-1
- new package built with tito

* Tue Dec 26 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.1.0-1
- new package built with tito


