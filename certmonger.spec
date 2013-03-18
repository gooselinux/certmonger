%if 0%{?fedora} > 15 || 0%{?rhel} > 6
%global systemd 1
%global	sysvinit 0
%else
%global systemd 0
%global	sysvinit 1
%endif

%if 0%{?fedora} > 14 || 0%{?rhel} > 6
%global tmpfiles 1
%else
%global tmpfiles 0
%endif

%if 0%{?fedora} > 9 || 0%{?rhel} > 5
%global sysvinitdir %{_initddir}
%else
%global sysvinitdir %{_initrddir}
%endif

Name:		certmonger
Version:	0.50
Release:	3%{?dist}
Summary:	Certificate status monitor and PKI enrollment client

Group:		System Environment/Daemons
License:	GPLv3+
URL:		http://certmonger.fedorahosted.org
Source0:	http://fedorahosted.org/released/certmonger/certmonger-%{version}.tar.gz
Source1:	http://fedorahosted.org/released/certmonger/certmonger-%{version}.tar.gz.sig
Patch0:		certmonger-referrer.patch
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	dbus-devel, nspr-devel, nss-devel, openssl-devel
%if 0%{?fedora} >= 12 || 0%{?rhel} >= 6
BuildRequires:  libuuid-devel
%else
BuildRequires:  e2fsprogs-devel
%endif
BuildRequires:	libtalloc-devel, libtevent-devel
BuildRequires:	libxml2-devel, xmlrpc-c-devel
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
#  for dbus-launch
BuildRequires:	/usr/bin/dbus-launch
#  for dos2unix
BuildRequires:	/usr/bin/dos2unix

# we need a running system bus
Requires:	dbus

%if %{systemd}
BuildRequires:	systemd-units
Requires(post):	systemd-units
Requires(preun):	systemd-units
Requires(postun):	systemd-units
Requires(post):	systemd-sysv
%endif

%if %{sysvinit}
Requires(post):	/sbin/chkconfig, /sbin/service
Requires(preun):	/sbin/chkconfig, /sbin/service
%endif

%if 0%{?fedora} >= 15
# Certain versions of libtevent have incorrect internal ABI versions.
Conflicts: libtevent < 0.9.13
%endif

%description
Certmonger is a service which is primarily concerned with getting your
system enrolled with a certificate authority (CA) and keeping it enrolled.

%prep
%setup -q
%patch0 -p1 -b .referrer

%build
%configure \
%if %{systemd}
	--enable-systemd \
%endif
%if %{sysvinit}
	--enable-sysvinit=%{sysvinitdir} \
%endif
%if %{tmpfiles}
	--enable-tmpfiles \
%endif
	--with-tmpdir=/var/run/certmonger
# For some reason, some versions of xmlrpc-c-config in Fedora and RHEL just
# tell us about libxmlrpc_client, but we need more.  Work around.
make %{?_smp_mflags} XMLRPC_LIBS="-lxmlrpc_client -lxmlrpc_util -lxmlrpc"

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_localstatedir}/lib/certmonger/{cas,requests}
install -m755 -d $RPM_BUILD_ROOT/var/run/certmonger
%{find_lang} %{name}

%check
make check

%clean
rm -rf $RPM_BUILD_ROOT

%post
if test $1 -eq 1 ; then
	killall -HUP dbus-daemon 2>&1 > /dev/null
fi
%if %{systemd}
if test $1 -eq 1 ; then
	/bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi
%endif
%if %{sysvinit}
/sbin/chkconfig --add certmonger
%endif

%postun
%if %{systemd}
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
	/bin/systemctl try-restart certmonger.service >/dev/null 2>&1 || :
fi
%endif
%if %{sysvinit}
if test $1 -gt 0 ; then
	/sbin/service certmonger condrestart 2>&1 > /dev/null
fi
%endif
exit 0

%preun
%if %{systemd}
	/bin/systemctl --no-reload disable certmonger.service > /dev/null 2>&1 || :
	/bin/systemctl stop certmonger.service > /dev/null 2>&1 || :
%endif
%if %{sysvinit}
if test $1 -eq 0 ; then
	/sbin/service certmonger stop 2>&1 > /dev/null
	/sbin/chkconfig --del certmonger
fi
%endif
exit 0

%if %{systemd}
%triggerun -- certmonger < 0.43
# Save the current service runlevel info, in case the user wants to apply
# the enabled status manually later, by running
#   "systemd-sysv-convert --apply certmonger".
%{_bindir}/systemd-sysv-convert --save certmonger >/dev/null 2>&1 ||:
# Do this because the old package's %%postun doesn't know we need to do it.
/sbin/chkconfig --del certmonger >/dev/null 2>&1 || :
# Do this because the old package's %%postun wouldn't have tried.
/bin/systemctl try-restart certmonger.service >/dev/null 2>&1 || :
exit 0
%endif

%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README LICENSE STATUS doc/*.txt
%config(noreplace) %{_sysconfdir}/dbus-1/system.d/*
%config(noreplace) %{_datadir}/dbus-1/services/*
%dir %{_sysconfdir}/certmonger
%config(noreplace) %{_sysconfdir}/certmonger/certmonger.conf
%dir /var/run/certmonger
%{_bindir}/*
%{_sbindir}/certmonger
%{_mandir}/man*/*
%{_libexecdir}/%{name}
%{_localstatedir}/lib/certmonger
%if %{sysvinit}
%{sysvinitdir}/certmonger
%endif
%if %{tmpfiles}
%attr(0644,root,root) %config(noreplace) /etc/tmpfiles.d/certmonger.conf
%endif
%if %{systemd}
%config(noreplace) /lib/systemd/system/*
%endif

%changelog
* Tue Nov  1 2011 Nalin Dahyabhai <nalin@redhat.com> 0.50-3
- tweak the patch for #750617 to handle the case where xmlrpc-c doesn't
  offer dont_advertise as an option (Rob Crittenden)

* Tue Nov  1 2011 Nalin Dahyabhai <nalin@redhat.com> 0.50-2
- incorporate patch from Rob Crittenden to start supplying Referer:
  headers when we submit XML-RPC requests (#750617)

* Fri Oct 14 2011 Nalin Dahyabhai <nalin@redhat.com> 0.50-1
- really fix these this time:
 - getcert: error out when "list -c" finds no matching CA (#743488)
 - getcert: error out when "list -i" finds no matching request (#743485)

* Wed Oct 12 2011 Nalin Dahyabhai <nalin@redhat.com> 0.49-1
- when using an NSS database, skip loading the module database (#743042)
- when using an NSS database, skip loading root certs
- generate SPKAC values when generating CSRs, though we don't do anything
  with SPKAC values yet
- internally maintain and use challenge passwords, if we have them
- behave better when certificates have shorter lifetimes
- add/recognize/handle notification type "none"
- getcert: error out when "list -c" finds no matching CA (#743488)
- getcert: error out when "list -i" finds no matching request (#743485)

* Thu Sep 29 2011 Nalin Dahyabhai <nalin@redhat.com> 0.48-1
- don't incorrectly assume that CERT_ImportCerts() returns a NULL-terminated
  array (#742348)

* Tue Sep 27 2011 Nalin Dahyabhai <nalin@redhat.com> 0.47-1
- getcert: distinguish between {stat() succeeds but isn't a directory} and
  {stat() failed} when printing an error message (#739903)
- getcert resubmit/start-tracking: when we're looking for an existing request
  by ID, and we don't find one, note that specifically (#741262)

* Mon Aug 29 2011 Stephen Gallagher <sgallagh@redhat.com> - 0.46-1.1
- Rebuild against fixed libtevent version

* Mon Aug 15 2011 Nalin Dahyabhai <nalin@redhat.com> 0.46-1
- treat the ability to access keys in an NSS database without using a PIN,
  when we've been told we need one, as an error (#692766, really this time)

* Thu Aug 11 2011 Nalin Dahyabhai <nalin@redhat.com> 0.45-1
- modify the systemd .service file to be a proper 'dbus' service (more
  of #718172)

* Thu Aug 11 2011 Nalin Dahyabhai <nalin@redhat.com> 0.44-1
- check specifically for cases where a specified token that we need to
  use just isn't present for whatever reason (#697058)

* Wed Aug 10 2011 Nalin Dahyabhai <nalin@redhat.com> 0.43-1
- add a -K option to ipa-submit, to use the current ccache, which makes
  it easier to test

* Fri Aug  5 2011 Nalin Dahyabhai <nalin@redhat.com>
- if xmlrpc-c's struct xmlrpc_curl_xportparms has a gss_delegate field, set
  it to TRUE when we're doing Negotiate auth (#727864, #727863, #727866)

* Wed Jul 13 2011 Nalin Dahyabhai <nalin@redhat.com>
- treat the ability to access keys in an NSS database without using a PIN,
  when we've been told we need one, as an error (#692766)
- when handling "getcert resubmit" requests, if we don't have a key yet,
  make sure we go all the way back to generating one (#694184)
- getcert: try to clean up tests for NSS and PEM file locations (#699059)
- don't try to set reconnect-on-exit policy unless we managed to connect
  to the bus (#712500)
- handle cases where we specify a token but the storage token isn't
  known (#699552)
- getcert: recognize -i and storage options to narrow down which requests
  the user wants to know about (#698772)
- output hints when the daemon has startup problems, too (#712075)
- add flags to specify whether we're bus-activated or not, so that we can
  exit if we have nothing to do after handling a request received over
  the bus if some specified amount of time has passed
- explicitly disallow non-root access in the D-Bus configuration (#712072)
- migrate to systemd on releases newer than Fedora 15 or RHEL 6 (#718172)
- fix a couple of incorrect calls to talloc_asprintf() (#721392)

* Wed Apr 13 2011 Nalin Dahyabhai <nalin@redhat.com> 0.42-1
- getcert: fix a buffer overrun preparing a request for the daemon when
  there are more parameters to encode than space in the array (#696185)
- updated translations: de, es, id, pl, ru, uk

* Mon Apr 11 2011 Nalin Dahyabhai <nalin@redhat.com> 0.41-1
- read information about the keys we've just generated before proceeding
  to generating a CSR (part of #694184, part of #695675)
- when processing a "resubmit" request from getcert, go back to key
  generation if we don't have keys yet, else go back to CSR generation as
  before (#694184, #695675)
- configure with --with-tmpdir=/var/run/certmonger and own /var/run/certmonger
  (#687899), and add a systemd tmpfiles.d control file for creating
  /var/run/certmonger on Fedora 15 and later
- let session instances exit when they get disconnected from the bus
- use a lock file to make sure there's only one session instance messing
  around with the user's files at a time
- fix errors saving certificates to NSS databases when there's already a
  certificate there with the same nickname (#695672)
- make key and certificate location output from 'getcert list' more properly
  translatable (#7)

* Mon Mar 28 2011 Nalin Dahyabhai <nalin@redhat.com> 0.40-1
- update to 0.40
  - fix validation check on EKU OIDs in getcert (#691351)
  - get session bus mode sorted
  - add a list of recognized EKU values to the getcert-request man page

* Fri Mar 25 2011 Nalin Dahyabhai <nalin@redhat.com> 0.39-1
- update to 0.39
  - fix use of an uninitialized variable in the xmlrpc-based submission
    helpers (#690886)

* Thu Mar 24 2011 Nalin Dahyabhai <nalin@redhat.com> 0.38-1
- update to 0.38
  - catch cases where we can't read a PIN file, but we never have to log
    in to the token to access the private key (more of #688229)

* Tue Mar 22 2011 Nalin Dahyabhai <nalin@redhat.com> 0.37-1
- update to 0.37
  - be more careful about checking if we can read a PIN file successfully
    before we even call an API that might need us to try (#688229)
  - fix strict aliasing warnings

* Tue Mar 22 2011 Nalin Dahyabhai <nalin@redhat.com> 0.36-1
- update to 0.36
  - fix some use-after-free bugs in the daemon (#689776)
  - fix a copy/paste error in certmonger-ipa-submit(8)
  - getcert now suppresses error details when not given its new -v option
    (#683926, more of #681641/#652047)
  - updated translations
    - de, es, pl, ru, uk
    - indonesian translation is now for "id" rather than "in"

* Wed Mar  2 2011 Nalin Dahyabhai <nalin@redhat.com> 0.35.1-1
- fix a self-test that broke because one-year-from-now is now a day's worth
  of seconds further out than it was a few days ago

* Mon Feb 14 2011 Nalin Dahyabhai <nalin@redhat.com> 0.35-1
- update to 0.35
  - self-test fixes to rebuild properly in mock (#670322)

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.34-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Fri Jan 14 2011 Nalin Dahyabhai <nalin@redhat.com> 0.34-1
- update to 0.34
  - explicitly note the number of requests we're tracking in the output of
    "getcert list" (#652049)
  - try to offer some suggestions when we get certain specific errors back
    in "getcert" (#652047)
  - updated translations
    - es

* Thu Dec 23 2010 Nalin Dahyabhai <nalin@redhat.com> 0.33-1
- update to 0.33
  - new translations
    - id by Okta Purnama Rahadian!
  - updated translations
    - pl, uk
  - roll up assorted fixes for defects

* Fri Nov 12 2010 Nalin Dahyabhai <nalin@redhat.com> 0.32-2
- depend on the e2fsprogs libuuid on Fedora and RHEL releases where it's
  not part of util-linux-ng

* Wed Oct 13 2010 Nalin Dahyabhai <nalin@redhat.com> 0.32-1
- oops, rfc5280 says we shouldn't be populating unique identifiers, so
  make it a configuration option and default the behavior to off

* Tue Oct 12 2010 Nalin Dahyabhai <nalin@redhat.com> 0.31-1
- start populating the optional unique identifier fields in self-signed
  certificates

* Thu Sep 30 2010 Nalin Dahyabhai <nalin@redhat.com> 0.30-4
- explicitly require "dbus" to try to ensure we have a running system bus
  when we get started (#639126)

* Wed Sep 29 2010 jkeating - 0.30-3
- Rebuilt for gcc bug 634757

* Thu Sep 23 2010 Nalin Dahyabhai <nalin@redhat.com> 0.30-2
- try to SIGHUP the messagebus daemon at first install so that it'll
  let us claim our service name if it isn't restarted before we are
  first started (#636876)

* Wed Aug 25 2010 Nalin Dahyabhai <nalin@redhat.com> 0.30-1
- update to 0.30
  - fix errors computing the time at the end of an interval that were
    caught by self-tests

* Mon Aug 23 2010 Nalin Dahyabhai <nalin@redhat.com> 0.29-1
- update to 0.29
  - fix 64-bit cleanliness issue using libdbus
  - actually include the full set of tests in tarballs

* Tue Aug 17 2010 Nalin Dahyabhai <nalin@redhat.com> 0.28-1
- update to 0.28
  - fix self-signing certificate notBefore and notAfter values on 32-bit
    machines

* Tue Aug 17 2010 Nalin Dahyabhai <nalin@redhat.com> 0.27-1
- update to 0.27
  - portability and test fixes

* Fri Aug 13 2010 Nalin Dahyabhai <nalin@redhat.com> 0.26-1
- update to 0.26
  - when canceling a submission request that's being handled by a helper,
    reap the child process's status after killing it (#624120)

* Fri Aug 13 2010 Nalin Dahyabhai <nalin@redhat.com> 0.25-1
- update to 0.25
  - new translations
    - in by Okta Purnama Rahadian!
  - fix detection of cases where we can't access a private key in an NSS
    database because we don't have the PIN
  - teach '*getcert start-tracking' about the -p and -P options which the
    '*getcert request' commands already understand (#621670), and also
    the -U, -K, -E, and -D flags
  - double-check that the nicknames of keys we get back from
    PK11_ListPrivKeysInSlot() match the desired nickname before accepting
    them as matches, so that our tests won't all blow up on EL5
  - fix dynamic addition and removal of CAs implemented through helpers

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
