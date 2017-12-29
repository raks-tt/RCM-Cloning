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


%build



%clean

%files
%defattr(-,root,root,-)
/usr/bin/*
%doc README.md
%doc src/README.md
%docdir src/*.md
%doc LICENSE

%changelog
* Wed Dec 27 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.2.0-1
- new package built with tito

* Tue Dec 26 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.1.0-1
- new package built with tito


