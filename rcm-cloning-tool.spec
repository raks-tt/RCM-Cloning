Name:	        rcm-cloning-tool	
Version:	0.0.1	
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
mkdir -p $RPM_BUILD_ROOT/%{_bindir} 
mkdir -p $RPM_BUILD_ROOT/usr/lib/%{name}

ldroot}/%{_bindir}/%{name} <<-EOF
#!/bin/bash
/usr/bin/python /usr/lib/%{name}/%{name}.pyc
EOF

chmod 0755 %{buildroot}/%{_bindir}/%{name}

install -m 0644 %{name}.py* %{buildroot}/usr/lib/%{name}/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%doc README.md
%doc src/README.md
%docdir src/*.md
%license LICENSE

%changelog
* Wed Dec 27 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.2.0-1
- new package built with tito

* Tue Dec 26 2017 Raksha Rajashekar <rrajashe@redhat.com> 1.1.0-1
- new package built with tito


