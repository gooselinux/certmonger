%{!?_with_check: %global pcheck 0}
%{?_with_check: %global pcheck 1}

Name:		certmonger
Version:	0.24
Release:	4%{?dist}
Summary:	Certificate status monitor and PKI enrollment client

Group:		System Environment/Daemons
License:	GPLv3+
URL:		http://certmonger.fedorahosted.org
Source0:	http://fedorahosted.org/released/certmonger/certmonger-%{version}.tar.gz
Patch0:		certmonger-0.24-pidfile.patch
Patch1:		certmonger-0.24-initscript.patch
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	dbus-devel, nspr-devel, nss-devel, openssl-devel
BuildRequires:	libtalloc-devel, libtevent-devel
BuildRequires:	xmlrpc-c-devel
%if 0%{?pcheck}
# Required for 'make check':
#  for diff and cmp
BuildRequires:	diffutils
#  for expect
BuildRequires:	expect
#  for mktemp, which was absorbed into coreutils at some point
BuildRequires:	mktemp
#  for certutil and pk12util
BuildRequires:	nss-tools
#  for openssl
BuildRequires:	openssl
%endif
Requires(post):	/sbin/chkconfig, /sbin/service
Requires(preun):	/sbin/chkconfig, /sbin/service

%description
Certmonger is a service which is primarily concerned with getting your
system enrolled with a certificate authority (CA) and keeping it enrolled.

%prep
%setup -q
%patch0 -p1 -b .pidfile
%patch1 -p1 -b .initscript

%build
%configure --with-file-store-dir=%{_localstatedir}/lib/certmonger
# For some reason, Fedora's xmlrpc-c-config just tells us about
# libxmlrpc_client, but in F13 we need all of them.  Workaround.
make %{?_smp_mflags} XMLRPC_LIBS="-lxmlrpc_client -lxmlrpc_util -lxmlrpc"

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lib/certmonger/{cas,requests}
%if 0%{?fedora} <= 9 || 0%{?rhel} < 6
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
install -m755 src/certmonger.init $RPM_BUILD_ROOT/%{_initrddir}/certmonger
%else
mkdir -p $RPM_BUILD_ROOT/%{_initddir}
install -m755 src/certmonger.init $RPM_BUILD_ROOT/%{_initddir}/certmonger
%endif

%{find_lang} %{name}

%check
%if 0%{?pcheck}
make check
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add certmonger

%postun
if test $1 -gt 0 ; then
	/sbin/service certmonger condrestart 2>&1 > /dev/null
fi
exit 0

%preun
if test $1 -eq 0 ; then
	/sbin/service certmonger stop 2>&1 > /dev/null
	/sbin/chkconfig --del certmonger
fi
exit 0

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README LICENSE STATUS doc/*.txt
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/*
%dir %{_sysconfdir}/certmonger
%config(noreplace) %{_sysconfdir}/certmonger/certmonger.conf
%if 0%{?fedora} <= 9 || 0%{?rhel} < 6
%{_initrddir}/certmonger
%else
%{_initddir}/certmonger
%endif
%{_bindir}/*
%{_sbindir}/certmonger
%{_mandir}/man*/*
%{_libexecdir}/%{name}
%{_localstatedir}/lib/certmonger

%changelog
* Mon Jun 28 2010 Nalin Dahyabhai <nalin@redhat.com> 0.24-4
- init script: ensure that the subsys lock is created whenever we're called to
  "start" when we're already running (even more of #596719)

* Tue Jun 15 2010 Nalin Dahyabhai <nalin@redhat.com> 0.24-3
- more gracefully handle manual daemon startups and cleaning up of unexpected
  crashes (still more of #596719)

* Thu Jun 10 2010 Nalin Dahyabhai <nalin@redhat.com> 0.24-2
- don't create the daemon pidfile until after we've connected to the D-Bus
  (still more of #596719)

* Tue Jun  8 2010 Nalin Dahyabhai <nalin@redhat.com> 0.24-1
- update to 0.24
  - keep the lock on the pid file, if we have one, when we fork, and cancel
    daemon startup if we can't gain ownership of the lock (the rest of #596719)
  - make the man pages note which external configuration files we consult when
    submitting requests to certmaster and ipa CAs

* Thu May 27 2010 Nalin Dahyabhai <nalin@redhat.com> 0.23-1
- update to 0.23
  - new translations
    - pl by Piotr Drąg!
  - cancel daemon startup if we can't gain ownership of our well-known
    service name on the DBus (#596719)

* Fri May 14 2010 Nalin Dahyabhai <nalin@redhat.com> 0.22-1
- update to 0.22
  - new translations
    - de by Fabian Affolter!
  - certmaster-submit: don't fall over when we can't find a certmaster.conf
    or a minion.conf (i.e., certmaster isn't installed) (#588932)
  - when reading extension values from certificates, prune out duplicate
    principal names, email addresses, and hostnames

* Tue May  4 2010 Nalin Dahyabhai <nalin@redhat.com> 0.21-1
- update to 0.21
  - getcert/*-getcert: relay the desired CA to the local service, whether
    specified on the command line (in getcert) or as a built-in hard-wired
    default (in *-getcert) (#584983)
  - flesh out the default certmonger.conf so that people can get a feel for
    the expected formatting (Jenny Galipeau)

* Wed Apr 21 2010 Nalin Dahyabhai <nalin@redhat.com> 0.20-1
- update to 0.20
  - correctly parse certificate validity periods given in years (spotted by
    Stephen Gallagher)
  - setup for translation
    - es by Héctor Daniel Cabrera!
    - ru by Yulia Poyarkova!
    - uk by Yuri Chornoivan!
  - fix unpreprocessed defaults in certmonger.conf's man page
  - tweak the IPA-specific message that indicates a principal name also needs
    to be specified if we're not using the default subject name (#579542)
  - make the validity period of self-signed certificates into a configuration
    setting and not a piece of the state information we track about the signer
  - init script: exit with status 2 instead of 1 when invoked with an
    unrecognized argument (#584517)

* Tue Mar 23 2010 Nalin Dahyabhai <nalin@redhat.com> 0.19-1
- update to 0.19
  - correctly initialize NSS databases that need to be using a PIN
  - add certmonger.conf, for customizing notification timings and settings,
    and use of digests other than the previously-hard-coded SHA256, and
    drop those settings from individual requests
  - up the default self-sign validity interval from 30 days to 365 days
  - drop the first default notification interval from 30 days to 28 days
    (these two combined to create a fun always-reissuing loop earlier)
  - record the token which contains the key or certificate when we're
    storing them in an NSS database, and report it
  - improve handling of cases where we're supposed to use a PIN but we
    either don't have one or we have the wrong one
  - teach getcert to accept a PIN file's name or a PIN value when adding
    a new entry
  - update the IPA submission helper to use the new 'request_cert' signature
    that's landing soon
  - more tests

* Fri Feb 12 2010 Nalin Dahyabhai <nalin@redhat.com> 0.18-1
- update to 0.18
  - add support for using encrypted storage for keys, using PIN values
    supplied directly or read from files whose names are supplied
  - don't choke on NSS database locations that use the "sql:" or "dbm:"
    prefix

* Mon Jan 25 2010 Nalin Dahyabhai <nalin@redhat.com> 0.17-2
- make the D-Bus configuration file (noreplace) (#541072)
- make the %%check section and the deps we have just for it conditional on
  the same macro (#541072)

* Wed Jan  6 2010 Nalin Dahyabhai <nalin@redhat.com> 0.17-1
- update to 0.17
  - fix a hang in the daemon (Rob Crittenden)
  - documentation updates
  - fix parsing of submission results from IPA (Rob Crittenden)

* Fri Dec 11 2009 Nalin Dahyabhai <nalin@redhat.com> 0.16-1
- update to 0.16
  - set a umask at startup (Dan Walsh)

* Tue Dec  8 2009 Nalin Dahyabhai <nalin@redhat.com> 0.15-1
- update to 0.15
  - notice that a directory with a trailing '/' is the same location as the
    directory without it
  - fix handling of the pid file when we write one (by actually giving it
    contents)

* Wed Nov 24 2009 Nalin Dahyabhai <nalin@redhat.com> 0.14-1
- update to 0.14
  - check key and certificate location at add-time to make sure they're
    absolute paths to files or directories, as appropriate
  - IPA: dig into the 'result' item if the named result value we're looking
    for isn't in the result struct

* Tue Nov 24 2009 Nalin Dahyabhai <nalin@redhat.com> 0.13-1
- update to 0.13
  - change the default so that we default to trying to auto-refresh
    certificates unless told otherwise
  - preemptively enforce limitations on request nicknames so that they
    make valid D-Bus object path components

* Tue Nov 24 2009 Nalin Dahyabhai <nalin@redhat.com> 0.12-1
- update to 0.12
  - add a crucial bit of error reporting when CAs reject our requests
  - count the number of configured CAs correctly

* Mon Nov 23 2009 Nalin Dahyabhai <nalin@redhat.com> 0.11-1
- update to 0.11
  - add XML-RPC submission for certmaster and IPA
  - prune entries with duplicate names from the data store

* Fri Nov 13 2009 Nalin Dahyabhai <nalin@redhat.com> 0.10-1
- update to 0.10
  - add some compiler warnings and then fix them

* Fri Nov 13 2009 Nalin Dahyabhai <nalin@redhat.com> 0.9-1
- update to 0.9
  - run external submission helpers correctly
  - fix signing of signing requests generated for keys stored in files
  - only care about new interface and route notifications from netlink,
    and ignore notifications that don't come from pid 0
  - fix logic for determining expiration status
  - correct the version number in self-signed certificates

* Tue Nov 10 2009 Nalin Dahyabhai <nalin@redhat.com> 0.8-1
- update to 0.8
  - encode windows UPN values in requests correctly
  - watch for netlink routing changes and restart stalled submission requests
  - 'getcert resubmit' can force a regeneration of the CSR and submission

* Fri Nov  6 2009 Nalin Dahyabhai <nalin@redhat.com> 0.7-1
- update to 0.7
  - first cut at a getting-started document
  - refactor some internal key handling with NSS
  - check for duplicate request nicknames at add-time

* Tue Nov  3 2009 Nalin Dahyabhai <nalin@redhat.com> 0.6-1
- update to 0.6
  - man pages
  - 'getcert stop-tracking' actually makes the server forget now
  - 'getcert request -e' was redundant, dropped the -e option
  - 'getcert request -i' now sets the request nickname
  - 'getcert start-tracking -i' now sets the request nickname

* Mon Nov  2 2009 Nalin Dahyabhai <nalin@redhat.com> 0.5-1
- update to 0.5
  - packaging fixes
  - add a selfsign-getcert client
  - self-signed certs now get basic constraints and their own serial numbers
  - accept id-ms-kp-sc-logon as a named EKU value in a request

* Thu Oct 29 2009 Nalin Dahyabhai <nalin@redhat.com> 0.4-1
- update to 0.4

* Thu Oct 22 2009 Nalin Dahyabhai <nalin@redhat.com> 0.1-1
- update to 0.1

* Sun Oct 18 2009 Nalin Dahyabhai <nalin@redhat.com> 0.0-1
- initial package
