Name:	        rcm-cloning-tool	
Version:	0.6.1	
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
%setup -q 

%build

%install

rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/local/bin
cp -R src/* $RPM_BUILD_ROOT/usr/local/bin

%{echo $PWD}


%clean
rm -rf $RPM_BUILD_ROOT

%files
%dir /usr/local/bin
%defattr(-,root,root,-)

%changelog
* Wed Jan 03 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.6.1-1
- new package built with tito

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


