Name:	        rcm-cloning-tool	
Version:	0.8.1	
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
/usr/local/bin/CONTRIBUTING
/usr/local/bin/README
/usr/local/bin/cloner/__init__.py
/usr/local/bin/cloner/cloner.py
/usr/local/bin/cloner/jira_clone_template_rcm.py
/usr/local/bin/cloner/pav_update.py
/usr/local/bin/cloner/ticket.py
/usr/local/bin/cloner/utils.py
/usr/local/bin/tests/test_cloner.py
/usr/local/bin/tests/fake_task_content.json
/usr/local/bin/tests/fake_subtask_content.json
/usr/local/bin/tests/test_utils.py
/usr/local/bin/tests/test_ticket.py
/usr/local/bin/tests/test_jira_clone_template_rcm.py

%changelog
* Wed Jan 03 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.8.1-1
- new package built with tito

* Wed Jan 03 2018 Raksha Rajashekar <rrajashe@redhat.com> 0.7.1-1
- new package built with tito

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


