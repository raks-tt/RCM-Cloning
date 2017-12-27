Name:	        rcm-cloning-tool	
Version:	1.2.0	
Release:	1%{?dist}
Summary:	A collection of scripts used by RCM for cloning JIRA Tickets	

License:       GPLv2+ 		
URL:   		https://github.com/raks-tt/RCM-Cloning.git 	 
Source0:       %{name}-%{version}.tar.gz	

BuildArch: noarch
Requires: python >= 2

%description
A collection of scripts used by RCM for cloning JIRA Tickets

%prep
%setup -q


%build


%install
mkdir -p $RPM_BUILD_ROOT/usr/bin/
cp -r src/* $RPM_BUILD_ROOT/usr/bin/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
/usr/bin/*
%{_mandir}/man1/product-proxy-*.1*


%changelog
* Wed Dec 27 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.2.0-1
- new package built with tito

* Tue Dec 26 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.1.0-1
- new package built with tito


