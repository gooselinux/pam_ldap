# We import a couple of source files from nss_ldap.
%global nss_ldap_version 265
# A suffix to use rather than ".bak" or ".orig" or whatever else a sensible
# human being might use.
%global tmpsuffix a134356b-d496-4171-a831-2bba8e89c85d

Summary: PAM module for LDAP
Name: pam_ldap
Version: 185
Release: 5%{?dist}
URL: http://www.padl.com/OSS/pam_ldap.html
License: LGPLv2+
Group: System Environment/Base

Source0: ftp://ftp.padl.com/pam_ldap-%{version}.tar.gz
Source1: ftp://ftp.padl.com/nss_ldap-%{nss_ldap_version}.tar.gz
Source5: README.TLS
Source7: dlopen.sh
Patch0: pam_ldap-185-dnsconfig.patch
Patch3: pam_ldap-180-install-perms.patch
Patch7: pam_ldap-182-manpointer.patch
Patch13: pam_ldap-176-exop-modify.patch
Patch20: pam_ldap-184-nsrole.patch
Patch23: pam_ldap-183-releaseconfig.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: autoconf, automake, libtool
BuildRequires: pam-devel
BuildRequires: openldap-devel >= 2.0.27
Conflicts: nss_ldap < 265
Requires(pre): coreutils
Requires(post): coreutils,/sbin/ldconfig
# The pam package supplies /%{_lib}/security.
Requires: pam

%description
pam_ldap is a module for Linux-PAM that supports password changes, server-
enforced password policies, access authorization, and crypted hashes.

%prep
%setup -q -a 1
cp %{SOURCE5} .
cp nss_ldap-%{nss_ldap_version}/resolve.c .
cp nss_ldap-%{nss_ldap_version}/resolve.h .
cp nss_ldap-%{nss_ldap_version}/snprintf.c .
cp nss_ldap-%{nss_ldap_version}/snprintf.h .
%patch0 -p1 -b .dnsconfig
%patch3 -p1 -b .install-perms
%patch7 -p1 -b .manpointer
%patch13 -p1 -b .exop-modify
%patch20 -p1 -b .nsrole
%patch23 -p1 -b .releaseconfig
sed -i -e 's,^ldap.conf$,%{name}.conf,g' *.5
sed -i -e 's,^/etc/ldap\.,/etc/%{name}.,g' *.5
sed -i -e 's,in ldap.conf,in %{name}.conf,g' *.5
sed -i -e 's,of ldap.conf,of %{name}.conf,g' *.5
sed -i -e 's,ldap.secret,%{name}.secret,g' *.5
sed -i -e 's,(ldap.conf),(%{name}.conf),g' *.5
autoreconf -f -i
cp %{_datadir}/libtool/config/config.{sub,guess} .

%build
# The version-embedding program's built in the build directory, so add it to
# the path.
%configure --libdir=/%{_lib} \
	--with-ldap-conf-file=%{_sysconfdir}/%{name}.conf \
	--with-ldap-secret-file=%{_sysconfdir}/%{name}.secret
env PATH=`pwd`:"$PATH" make %{?_smp_mflags}

# Check that the module is actually loadable.
sh %{SOURCE7} -lpam ./pam_ldap.so

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/{etc,%{_lib}/security,%{_libdir}}

# Install the default configuration file, but change the search bases to
# something generic to avoid overloading padl.com servers and to match
# good practice when using DNS domains in example configurations.
sed 's|dc=padl|dc=example|g' ldap.conf > $RPM_BUILD_ROOT/etc/%{name}.conf
chmod 644 $RPM_BUILD_ROOT/etc/%{name}.conf

# Install the module.  Trick the makefile into not trying to install ldap.conf.
touch $RPM_BUILD_ROOT/etc/ldap.conf
make install DESTDIR=$RPM_BUILD_ROOT
rm $RPM_BUILD_ROOT/etc/ldap.conf

# Create an ldap.secret file.
touch $RPM_BUILD_ROOT/etc/%{name}.secret

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%pre
# If we didn't already have a config file for this package, but we did have one
# for the old nss_ldap package, copy the configuration to a temporary location.
if ! test -s %{_sysconfdir}/%{name}.conf ; then
	if test -s %{_sysconfdir}/ldap.conf ; then
		cp -p %{_sysconfdir}/ldap.conf %{_sysconfdir}/%{name}.conf.%{tmpsuffix}
	fi
fi
if ! test -s %{_sysconfdir}/%{name}.secret ; then
	if test -s %{_sysconfdir}/ldap.secret ; then
		cp -p %{_sysconfdir}/ldap.secret %{_sysconfdir}/%{name}.secret.%{tmpsuffix}
	fi
fi

%post
# If we created a temporary configuration in %%pre, replace the one our package
# put down with the old one.
if test -s %{_sysconfdir}/%{name}.conf.%{tmpsuffix} ; then
	mv %{_sysconfdir}/%{name}.conf.%{tmpsuffix} %{_sysconfdir}/%{name}.conf
fi
if test -s %{_sysconfdir}/%{name}.secret.%{tmpsuffix} ; then
	mv %{_sysconfdir}/%{name}.secret.%{tmpsuffix} %{_sysconfdir}/%{name}.secret
fi

%files
%defattr(-,root,root,-)
%doc README.TLS AUTHORS ChangeLog COPYING COPYING.LIB NEWS README
%doc pam.d
%doc ldapns.schema
%doc ns-pwd-policy.schema
%attr(0755,root,root) /%{_lib}/security/*.so*
%attr(0644,root,root) %{_mandir}/man5/*.5*
%attr(0644,root,root) %config(noreplace) /etc/%{name}.conf
%attr(0600,root,root) %ghost %config(noreplace) /etc/%{name}.secret

%changelog
* Thu Mar 23 2010 Nalin Dahyabhai <nalin@redhat.com> 185-5
- require the pam package explicitly, so that /%%{_lib}/security won't be
  an orphaned directory (part of #553857)

* Thu Feb 25 2010 Nalin Dahyabhai <nalin@redhat.com> 185-4
- stop increasing the bind and search timelimits beyond their defaults

* Fri Feb 19 2010 Nalin Dahyabhai <nalin@redhat.com> 185-3
- make mentions of pam_ldap.conf and %%{name}.conf more consistent (rcritten)
- drop no-longer-used .versions file

* Mon Jan 18 2010 Nalin Dahyabhai <nalin@redhat.com> 185-2
- fix source URLs

* Fri Jan  8 2010 Nalin Dahyabhai <nalin@redhat.com> 185-1
- split out pam_ldap as a separate source package, update URL, change
  %%{version} to reflect pam_ldap's versioning rather than nss_ldap's
- set config file to /etc/pam_ldap.conf, rootbindpw file /etc/pam_ldap.secret
- drop %%post bits that care about upgrades from RHL 7.2
- drop %%post/%%postun calls to ldconfig
- drop buildrequires on openssl-devel, krb5-devel, cyrus-sasl-devel
- update to version 185
  - drop now-obsolete patches to the rebind callback
- add %%pre logic for the upgrading-from-a-non-split-nss_ldap case

* Wed Nov  4 2009 Nalin Dahyabhai <nalin@redhat.com> 264-8
- add "rtkit" and "pulse" to the list of users whom we default to ignoring
  for looking up supplemental groups (Gordon Messmer, part of #186527)

* Tue Jul 28 2009 Nalin Dahyabhai <nalin@redhat.com> 264-7
- set close-on-exec on the dummy socket created in the child atfork() (#512856)

* Sat Jul 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 264-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Jul 22 2009 Nalin Dahyabhai <nalin@redhat.com> 264-5
- fix some minor leaks in pam_ldap, part of upstream #326,#333

* Tue Jul  7 2009 Nalin Dahyabhai <nalin@redhat.com> - 264-4
- add proposed patch for upstream #322: crashing in oneshot mode

* Mon Jul  6 2009 Nalin Dahyabhai <nalin@redhat.com>
- add but don't apply proposed patch for upstream #399: depending on the
  server to enforce the expected case-sensitivity opens up corner cases

* Fri Jun 19 2009 Kedar Sovani <kedars@marvell.com>  - 264-3
- BuildRequires: openssl-static

* Fri Jun 19 2009 Nalin Dahyabhai <nalin@redhat.com>
- revert most of the previous round of changes: splitting pam_ldap off
  won't be helpful in the long term if it, too, is eventually going to conflict
  with the nss-ldapd package

* Mon Apr  6 2009 Nalin Dahyabhai <nalin@redhat.com> - 264/184-100
- split pam_ldap off into a separate binary package
- require /%%{_lib}/security/pam_ldap.so to pull in pam_ldap on upgrades
- require our configuration file to come from somewhere
- remove some cruft
- move the %%postun that fixes up pam configs to the pam_ldap package

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 264-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Jan 27 2009 Nalin Dahyabhai <nalin@redhat.com> - 264-1
- update to 264, pulling in Luke's patch for #248, among others
- add optional checking of nsRole to pam_ldap (#202135, upstream #382)

* Mon Dec 22 2008 Nalin Dahyabhai <nalin@redhat.com> - 263-2
- correct some build errors
- add but do not apply proposed pam_ldap patch to add nsrole support

* Wed Oct 29 2008 Nalin Dahyabhai <nalin@redhat.com> - 263-1
- update to 263, pulling in Luke's patch for #374 (#445972) which doesn't
  leak the result message, and the fix for #376 (#466794)

* Wed Oct 29 2008 Nalin Dahyabhai <nalin@redhat.com> - 261-5
- pam_ldap: don't crash when we have to follow a referral while looking up
  information about the authenticating user and we're using SASL, which
  affected 259-1 and later (patch from Paul P Komkoff Jr, #469061)

* Fri Oct 17 2008 Nalin Dahyabhai <nalin@redhat.com> - 261-4
- add missing local-to-network conversion on port numbers when looking up
  services, which affected 259-1 and later (#450634)

* Mon Sep 15 2008 Nalin Dahyabhai <nalin@redhat.com>
- return 0 (fail) instead of 1 (success) when setnetgrent() is called for
  a netgroup which doesn't actually exist or which has no members (#445972,
  upstream #374)

* Thu Sep 11 2008 Nalin Dahyabhai <nalin@redhat.com> - 261-3
- promote the previous change from a scratch build to the real thing

* Tue Aug 26 2008 Nalin Dahyabhai <nalin@redhat.com> - 261-2
- add libssl and libcrypto to the list of libraries against which we link
  statically to avoid running into symbol collisions at run-time (#446860)

* Wed Jul 16 2008 Nalin Dahyabhai <nalin@redhat.com> - 261-1
- update to version 261
- remove fuzz from patches

* Wed Apr 16 2008 Nalin Dahyabhai <nalin@redhat.com> - 259-3
- try to work around not having had a populated resolver configuration earlier,
  but needing to use its data when we're asked to look up something (#442272)

* Tue Apr 15 2008 Nalin Dahyabhai <nalin@redhat.com> - 259-2
- apply updated logic for finding libresolv to pam_ldap's build setup
- add gdm,polkituser to default nss_initgroups_ignoreusers list

* Tue Feb 26 2008 Nalin Dahyabhai <nalin@redhat.com> - 259-1
- update to nss_ldap 259
- nss_ldap: update to revised proposed patch for #248
- pam_ldap: replace two patches to handle password changing against replicas
  with Ralf Haferkamp's revision, which also sends the policy control with the
  initial password change request
- pam_ldap: enable patch to stop also trying to change password using
  ldap_modify after trying to change it with an exop when the configuration
  is "pam_password exop_send_old"

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 257-7
- Autorebuild for GCC 4.3

* Wed Dec  5 2007 Nalin Dahyabhai <nalin@redhat.com> - 257-6
- rebuild

* Wed Nov 21 2007 Nalin Dahyabhai <nalin@redhat.com> - 257-5
- nss_ldap: go back to linking with static libldap and liblber so that we
  don't get unresolved references which may be resolved by a different libldap
  used by the calling application

* Thu Sep 20 2007 Nalin Dahyabhai <nalin@redhat.com>
- revise not-applied patch for attempting to stop infinite recursion in
  poorly-configured case

* Fri Aug 24 2007 Nalin Dahyabhai <nalin@redhat.com> - 257-3
- tack on a disttag

* Fri Aug 24 2007 Nalin Dahyabhai <nalin@redhat.com> - 257-2
- construct LDAP URIs correctly during DNS autoconfiguration (upstream #338)

* Tue Aug 21 2007 Nalin Dahyabhai <nalin@redhat.com> - 257-1
- update to nss_ldap 257
- look harder when we're looking for symbols provided by the resolver library
  (upstream #337)
- clarify license (both under LGPLv2 or later)

* Thu Jul 19 2007 Nalin Dahyabhai <nalin@redhat.com> - 256-1
- update to nss_ldap 256, pam_ldap 184

* Wed Mar 21 2007 Nalin Dahyabhai <nalin@redhat.com> - 254-2
- resize the supplemental GID array when it gets too large and an array size
  limit isn't set (Gavin Romig-Koch, #232713)

* Mon Feb 26 2007 Nalin Dahyabhai <nalin@redhat.com> - 254-1
- update to nss_ldap 254
- use the upstream version scripts
- stop trying to isolate us from the apps by building with static libraries,
  though that means we're tied to /usr now
- move the nsswitch module to %%{_libdir}; its deps aren't available without
  a mounted /usr anyway
- make rpmlint happier

* Mon Nov 20 2006 Nalin Dahyabhai <nalin@redhat.com> - 253-4
- rebuild

* Mon Nov 20 2006 Nalin Dahyabhai <nalin@redhat.com> - 253-3
- rebuild

* Mon Nov 20 2006 Nalin Dahyabhai <nalin@redhat.com> - 253-2
- update to pam_ldap 183, resolving CVE-2006-5170 (#216421)

* Fri Sep 22 2006 Nalin Dahyabhai <nalin@redhat.com> - 253-1
- update to 253
  - closes a crasher when glibc's initgroups backend passes in a zero-length,
    NULL buffer to start
  - includes lookup_nssldap updates for autofs

* Tue Sep 12 2006 Nalin Dahyabhai <nalin@redhat.com> - 251-2
- configure with --enable-configurable-krb5-ccname-gssapi instead of
  --enable-configurable-krb5-ccname, the latter of which doesn't actually
  do anything (Howard Wilkinson)

* Thu Aug  3 2006 Nalin Dahyabhai <nalin@redhat.com> - 251-1
- update to 251

* Tue Jul 25 2006 Nalin Dahyabhai <nalin@redhat.com> - 250-6
- note the location of the man pages in /etc/ldap.conf (part of #146815)

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 250-5.1
- rebuild

* Tue May 16 2006 Nalin Dahyabhai <nalin@redhat.com> - 250-5
- adjust nss_ldap's makefile rule to more correctly deduce the right soversion
  for nsswitch modules (#191927)

* Mon May  8 2006 Nalin Dahyabhai <nalin@redhat.com> - 250-4
- update the list of local users to include named,avahi,haldaemon (from #186527)

* Tue May  2 2006 Nalin Dahyabhai <nalin@redhat.com> - 250-3
- update to pam_ldap 182

* Mon May  1 2006 Nalin Dahyabhai <nalin@redhat.com> - 250-2
- update to pam_ldap 181
- fix syntax error in pam_ldap.c (upstream #269)

* Thu Apr 27 2006 Nalin Dahyabhai <nalin@redhat.com> - 250-1
- update to 250
- configure default time limits for binding/searching/idling

* Fri Feb 24 2006 Nalin Dahyabhai <nalin@redhat.com> - 249-1
- update to 249, which incorporates the fix for #182464

* Thu Feb 23 2006 Nalin Dahyabhai <nalin@redhat.com> - 248-3
- fix deadlock in initgroups() (#182464, upstream #255)

* Mon Feb 13 2006 Jesse Keating <jkeating@redhat.com> - 248-2.2
- rebump for build order issues during double-long bump

* Fri Feb 10 2006 Jesse Keating <jkeating@redhat.com> - 248-2.1
- bump again for double-long bug on ppc(64)

* Thu Feb  9 2006 Nalin Dahyabhai <nalin@redhat.com> - 248-2
- set "nss_initgroups_ignoreusers root,ldap" in the default configuration
  file, so that nss_ldap will assume that there are no supplemental groups
  for this user to be found in the directory server (#180657)

* Tue Feb 07 2006 Jesse Keating <jkeating@redhat.com> - 248-1.1
- rebuilt for new gcc4.1 snapshot and glibc changes

* Wed Jan 25 2006 Nalin Dahyabhai <nalin@redhat.com> 248-1
- update to nss_ldap 248

* Tue Jan 24 2006 Nalin Dahyabhai <nalin@redhat.com> 246-1
- update to nss_ldap 246

* Wed Jan 11 2006 Nalin Dahyabhai <nalin@redhat.com> 245-1
- update to nss_ldap 245
- add patch from upcoming 246 release to change the placeholder used when
  userPassword is unreadable from "x" to "*" (upstream #240)

* Fri Dec 09 2005 Jesse Keating <jkeating@redhat.com>
- rebuilt

* Mon Nov 21 2005 Nalin Dahyabhai <nalin@redhat.com> 244-2
- rebuild with new libldap and friends (#173794)

* Thu Oct 27 2005 Nalin Dahyabhai <nalin@redhat.com> 244-1
- update to nss_ldap 244

* Tue Oct  4 2005 Nalin Dahyabhai <nalin@redhat.com> 243-1
- update to nss_ldap 243

* Wed Sep 28 2005 Nalin Dahyabhai <nalin@redhat.com> 242-2
- own the symlink for the module's soname (#169288)

* Tue Sep 27 2005 Nalin Dahyabhai <nalin@redhat.com> 242-1
- update to nss_ldap 242

* Mon Sep 12 2005 Nalin Dahyabhai <nalin@redhat.com> 241-1
- update to nss_ldap 241

* Thu Sep  7 2005 Nalin Dahyabhai <nalin@redhat.com> 240-2
- install the pam_ldap man page (part of #167764)

* Wed Aug 31 2005 Nalin Dahyabhai <nalin@redhat.com> 240-1
- update to nss_ldap 240

* Wed Aug 17 2005 Nalin Dahyabhai <nalin@redhat.com> 239-1
- update to nss_ldap 239
- provide a libnss_ldap.so link for directly linking with nss_ldap, as glibc
  does for the modules it provides

* Wed Aug 17 2005 Nalin Dahyabhai <nalin@redhat.com> 234-6
- rebuild

* Wed Aug 17 2005 Nalin Dahyabhai <nalin@redhat.com> 234-5
- update to pam_ldap 180 to get fix for vulnerability from parsing password
  policy controls which don't contain error numbers (#166164, CAN-2005-2497)

* Fri May 20 2005 Nalin Dahyabhai <nalin@redhat.com> 234-4
- override glibc version detection so that mismatches between the versions of
  32- and 64-bit glibc don't result in our %%install installing the module
  with a different name than the 'make install' target uses
  
* Fri May 20 2005 Nalin Dahyabhai <nalin@redhat.com> 234-3
- fix type mismatch bug in patch for using non-blocking start_tls in
  preference to the blocking version when it's available (#156582)

* Wed Mar 16 2005 Nalin Dahyabhai <nalin@redhat.com> 234-2
- rebuild

* Mon Feb 28 2005 Nalin Dahyabhai <nalin@redhat.com> 234-1
- update to nss_ldap 234
- configure with --enable-configurable-krb5-ccname

* Wed Feb  2 2005 Nalin Dahyabhai <nalin@redhat.com> 232-2
- prefer using libraries in %%{_libdir}/nss_ldap-openldap if we find any
- use ldap_start_tls in preference to ldap_start_tls_s, if found, so that
  we can time out if the server has gone catatonic

* Mon Jan 24 2005 Nalin Dahyabhai <nalin@redhat.com> 232-1
- update to version 232

* Fri Dec 31 2004 Nalin Dahyabhai <nalin@redhat.com> 227-1
- update to version 227
- force nss_ldap to mimic pam_ldap's behavior when the tls_checkpeer setting is
  unconfigured in ldap.conf

* Fri Dec 31 2004 Nalin Dahyabhai <nalin@redhat.com> 226-3
- fix misleading doc comment in /etc/ldap.conf -- the checkpeer setting follows
  libldap's default, which is dependent on the version of OpenLDAP which which
  this package is linked (part of #143622)

* Thu Oct 28 2004 Nalin Dahyabhai <nalin@redhat.com> 226-2
- rebuild

* Thu Oct 28 2004 Nalin Dahyabhai <nalin@redhat.com> 226-1
- update to nss_ldap 226, pam_ldap 176
- rework pam_ldap dns autoconfig patch
- require automake instead of automake15, because autoreconf uses the current
  version (#129877)

* Tue Aug 31 2004 Nalin Dahyabhai <nalin@redhat.com> 220-3
- rebuild

* Tue Jun 15 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Mon Jun  7 2004 Nalin Dahyabhai <nalin@redhat.com> 220-1
- update to 220, pam_ldap 169

* Thu Apr 15 2004 Nalin Dahyabhai <nalin@redhat.com>
- fail at build-time if the modules produced can't be loaded
- fix missing module in pam_ldap build

* Thu Mar 25 2004 Nalin Dahyabhai <nalin@redhat.com> 217-1
- include patch to set errno to ENOENT when returning NSS_STATUS_NOTFOUND to
  glibc

* Tue Mar 23 2004 Nalin Dahyabhai <nalin@redhat.com>
- update to 217

* Wed Mar 10 2004 Nalin Dahyabhai <nalin@redhat.com> 212-1
- update to 212, pam_ldap 167
- link nss_ldap with libgssapi_krb5, the static libsasl2 includes the gssapi
  mech, at least for now, and we pick up its unresolved symbols at link-time
- fix out-of-bounds error at initialization-time (part of #101269)
- include pam_ldap's authorization schema files for slapd as a doc file

* Tue Mar 02 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com>
- rebuilt

* Tue Nov 25 2003 Nalin Dahyabhai <nalin@redhat.com> 207-6
- rebuild

* Thu Nov 20 2003 Nalin Dahyabhai <nalin@redhat.com> 207-5
- fix objectclass and attribute mapping, which failed due to uninitialized
  fields in mapping index structures, fixed upstream in 210 (#110547)

* Mon Nov 10 2003 Nalin Dahyabhai <nalin@redhat.com> 207-4
- link with the proper libsasl (1 or 2) for the version of OpenLDAP we
  are linking with (#106801)

* Thu Aug 14 2003 Nalin Dahyabhai <nalin@redhat.com> 207-3
- link dynamically with libcom_err if it isn't in /usr/kerberos/%%{_lib} (which
  we assume means that it's in /%%{_lib})

* Wed Aug 13 2003 Nalin Dahyabhai <nalin@redhat.com> 207-2
- relax openldap-devel buildreq to 2.0.27

* Thu Jun  5 2003 Nalin Dahyabhai <nalin@redhat.com> 207-1
- update to build with newer OpenLDAP
- add README.TLS to remind people that in order for TLS support to be usable,
  the server's certificate has to pass validation checks made by the client

* Sun Mar 09 2003 Florian La Roche <Florian.LaRoche@redhat.de>
- move pam into /lib64/security directory

* Wed Jan 22 2003 Tim Powers <timp@redhat.com>
- rebuilt

* Wed Jan 15 2003 Nalin Dahyabhai <nalin@redhat.com> 202-4
- rework static link order to account for libssl requiring libkrb5
- force assembly locking on %%ix86 systems
- link with libz, which libssl also requires

* Thu Dec 12 2002 Elliot Lee <sopwith@redhat.com> 202-3
- Fix wildcard for symlink in %%install

* Thu Nov 14 2002 Nalin Dahyabhai <nalin@redhat.com> 202-2
- apply DB patches from sleepycat.com
- correctly point nss_ldap at the bundled DB library
- create /%%{_lib} instead of /lib to install into

* Wed Oct  2 2002 Nalin Dahyabhai <nalin@redhat.com> 202-1
- update to nss_ldap 202, pam_ldap 153
- update DB from 4.0.14 to 4.1.24.NC
- try to address multilib path changes

* Tue Aug 27 2002 Nalin Dahyabhai <nalin@redhat.com> 198-3
- rebuild

* Fri Aug  9 2002 Nalin Dahyabhai <nalin@redhat.com> 198-2
- handle larger-than-expected DNS responses correctly

* Wed Aug  7 2002 Nalin Dahyabhai <nalin@redhat.com> 198-1
- update to nss_ldap 198, closing a possible buffer overflow in DNS autoconfig

* Fri Jul 19 2002 Nalin Dahyabhai <nalin@redhat.com> 197-1
- update to nss_ldap 197, pam_ldap 150

* Fri Jun 21 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Mon Jun 10 2002 Nalin Dahyabhai <nalin@redhat.com> 194-1
- update to nss_ldap 194, pam_ldap 148

* Sun May 26 2002 Tim Powers <timp@redhat.com>
- automated rebuild

* Mon May 20 2002 Nalin Dahyabhai <nalin@redhat.com> 189-3
- rebuild in new environment

* Thu May 16 2002 Nalin Dahyabhai <nalin@redhat.com> 189-2
- build for RHL 7.2/7.3

* Thu May 16 2002 Nalin Dahyabhai <nalin@redhat.com> 189-1.7
- build for RHL 7/7.1

* Thu May 16 2002 Nalin Dahyabhai <nalin@redhat.com> 189-1.6
- fix up logic generated by authconfig from RHL 7.2 in %%post
- build for RHL 6.x

* Wed May 15 2002 Nalin Dahyabhai <nalin@redhat.com>
- the triggerun should be a trigger postun

* Tue May  7 2002 Nalin Dahyabhai <nalin@redhat.com> 189-1
- rebuild for RHL 7.2/7.3

* Tue May  7 2002 Nalin Dahyabhai <nalin@redhat.com> 189-0.7
- rebuild for RHL 7/7.1

* Tue May  7 2002 Nalin Dahyabhai <nalin@redhat.com> 189-0.6
- update to nss_ldap 189, pam_ldap 145

* Tue May  7 2002 Nalin Dahyabhai <nalin@redhat.com> 188-1
- rebuild for RHL 7.2/7.3

* Tue May  7 2002 Nalin Dahyabhai <nalin@redhat.com> 188-0.7
- rebuild for RHL 7/7.1

* Tue May  7 2002 Nalin Dahyabhai <nalin@redhat.com> 188-0.6
- rebuild for RHL 6.2
- change dependency on pam-devel to /usr/include/security/pam_modules.h
- drop build deps on cyrus-sasl-devel and openldap >= 2.x
- modify pam_ldap versions file so that binutils from RHL 6.2 can parse it
- update to nss_ldap 188
- update to pam_ldap 144

* Fri Apr  5 2002 Nalin Dahyabhai <nalin@redhat.com> 185-1
- update to nss_ldap 185
- update to pam_ldap 140

* Thu Feb 28 2002 Nalin Dahyabhai <nalin@redhat.com> 184-1
- update to pam_ldap 138
- enable rfc2307bis schema support
- version the pam_ldap module
- add the proper soname to the nss_ldap module and remove the symlink
- add a trigger to run ldconfig again when an upgrade removes the symlink,
  which used to be in this package (doh!)
- fix the symlink from %%{_libdir} to the module (for linking directly to it)

* Thu Feb 14 2002 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 184, pam_ldap 137

* Wed Jan 23 2002 Nalin Dahyabhai <nalin@redhat.com> 181-1
- update to nss_ldap 181, pam_ldap 136

* Thu Dec 20 2001 Nalin Dahyabhai <nalin@redhat.com> 175-1
- update to nss_ldap 175, pam_ldap 135

* Tue Nov 27 2001 Nalin Dahyabhai <nalin@redhat.com> 174-1
- update to nss_ldap 174

* Fri Nov 16 2001 Nalin Dahyabhai <nalin@redhat.com> 173-3
- update to pam_ldap 134

* Wed Oct 31 2001 Nalin Dahyabhai <nalin@redhat.com> 173-2
- build nss_ldap with --enable-schema-mapping

* Mon Oct 29 2001 Nalin Dahyabhai <nalin@redhat.com> 173-1
- update to nss_ldap 173, which includes doc updates
- update to pam_ldap 133, which simplifies the dnsconfig patch quite a bit

* Thu Sep  6 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to pam_ldap 125, making checking of host attributes configurable

* Fri Aug 31 2001 Nalin Dahyabhai <nalin@redhat.com>
- link statically with libldap again, because libldap is linked with other
  shared libraries now (keeping us from having files in /usr open when we
  go to shut the system down)

* Thu Aug 30 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 172, fixing schema mapping code
- update to pam_ldap 124, incorporating TLS default option and doc fixes

* Mon Aug  6 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 167, adding support for rebinds

* Tue Jul 24 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 164, fixing the timeout problem correctly
- update to pam_ldap 122, fixing escaping of user name in filters

* Thu Jul 12 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 163, fixing the timeout problem
- update to pam_ldap 120
- add gdbm-devel as a buildprereq, because we list it in $LIBS (#48999)
- add db3-devel as a buildprereq (#48999)
- add pam-devel as a buildprereq (#48999)

* Tue Jul 10 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 161
- attempt to fix hangs when no timeout is specified, or the timeout is 0

* Mon Jul  9 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 160, pam_ldap 119

* Thu Jun 28 2001 Nalin Dahyabhai <nalin@redhat.com>
- patch cleanups

* Tue Jun 26 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 159, pam_ldap 118

* Tue Jun 19 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 153, pam_ldap 117

* Tue May 29 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 152, pam_ldap 111

* Mon May 21 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to pam_ldap 108

* Wed Apr 25 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to pam_ldap 107

* Thu Apr 19 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 150 (incorporates the fail patch)
- update to pam_ldap 106

* Wed Mar  7 2001 Nalin Dahyabhai <nalin@redhat.com>
- make nss_ldap fail when attempting to startup TLS fails, because that's what
  we do when LDAPS doesn't work (and what pam_ldap does already)
- add DNS autoconfiguration to pam_ldap

* Tue Mar  6 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 149, minor fixes for compile glitches
- update to pam_ldap 105, minor fixes (as above) and handles shadow expiration

* Fri Mar  2 2001 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in new environment

* Wed Feb 28 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 146 to get a faster initgroups() back-end

* Mon Feb 12 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 143 to get the official fix for the heap corruption

* Fri Feb  9 2001 Nalin Dahyabhai <nalin@redhat.com>
- fix heap corruption when falling back to DNS SRV records for configuration

* Mon Feb  5 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 142, fixes a memory leak

* Mon Jan 29 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 140, fixes a configure bug and an alignment problem

* Fri Jan 19 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 139

* Mon Jan 15 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 138, which folds in our patch for initgroups
- change the default search base in ldap.conf to dc=example,dc=com

* Wed Jan 10 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 137 and pam_ldap 99
- try to not cause a segfault in _nss_ldap_initgroups

* Wed Jan  3 2001 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 124 and pam_ldap 82

* Thu Dec 28 2000 Nalin Dahyabhai <nalin@redhat.com>
- add a requires: for nscd

* Thu Dec 14 2000 Nalin Dahyabhai <nalin@redhat.com>
- version the NSS module so that it works properly with programs which have
  been linked statically to a different version of an LDAP library, like
  Netscape Communicator

* Wed Dec  6 2000 Nalin Dahyabhai <nalin@redhat.com>
- BuildPrereq gdbm-devel
- pass RPM_OPT_FLAGS as CFLAGS to %%configure
- if protocol version is 2, explicitly set protocol version to 3 before trying
  to start TLS
- add STARTTLS support to nss_ldap
- work around a build-time problem on ia64

* Tue Dec  5 2000 Nalin Dahyabhai <nalin@redhat.com>
- BuildPrereq cyrus-sasl-devel instead of cyrus-sasl

* Mon Nov 20 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 123 and pam_ldap 82

* Fri Oct 27 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 122
- link statically with libsasl, require the first devel package that supplied it

* Thu Oct 19 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 120 and pam_ldap 77

* Wed Oct  4 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 116 and pam_ldap 74

* Fri Sep  7 2000 Nalin Dahyabhai <nalin@redhat.com>
- rebuild in new environment

* Thu Jul 27 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to pam_ldap 67 to fix a bug in template user code
- convert symlink in /usr/lib to a relative one (#16132)

* Thu Jul 27 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 113 and pam_ldap 66

* Wed Jul 12 2000 Prospector <bugzilla@redhat.com>
- automatic rebuild

* Tue Jun 27 2000 Matt Wilson <msw@redhat.com>
- changed all the -,- in attr statements to root,root

* Tue Jun 27 2000 Nalin Dahyabhai <nalin@redhat.com>
- update pam_ldap to 63

* Wed May 31 2000 Nalin Dahyabhai <nalin@redhat.com>
- update pam_ldap to 56

* Tue May 30 2000 Nalin Dahyabhai <nalin@redhat.com>
- update pam_ldap to 55
- back out no-threads patch for pam_ldap, not needed any more

* Thu May 25 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to 110
- revert prototype patch, looks like a problem with the new glibc after all

* Fri May 19 2000 Nalin Dahyabhai <nalin@redhat.com>
- get libpthread out of the NSS module
- fix prototype problems in getpwXXX()

* Mon May 15 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 109

* Sat Apr 29 2000 Nalin Dahyabhai <nalin@redhat.com>
- update pam_ldap 51

* Tue Apr 25 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 108 and pam_ldap 49

* Thu Apr 20 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to pam_ldap 48

* Thu Mar 30 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 107
- note: check http://www.advogato.org/person/lukeh/ for Luke's changelog

* Tue Mar 21 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 106

* Wed Feb  9 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 105

* Mon Feb  7 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 104 and pam_ldap 46
- disable link against libpthread in pam_ldap

* Tue Feb  1 2000 Nalin Dahyabhai <nalin@redhat.com>
- remove migration tools, because this package requires openldap now, which
  also includes them

* Fri Jan 28 2000 Nalin Dahyabhai <nalin@redhat.com>
- update to nss_ldap 103

* Mon Jan 24 2000 Preston Brown <pbrown@redhat.com>
- fix typo in linuxconf-pair pam cfg file (#7800)

* Tue Jan 11 2000 Preston Brown <pbrown@redhat.com>
- v99, made it require pam_ldap
- added perl migration tools
- integrate pam_ldap stuff

* Fri Oct 22 1999 Bill Nottingham <notting@redhat.com>
- statically link ldap libraries (they're in /usr/lib)

* Tue Aug 10 1999 Cristian Gafton <gafton@redhat.com>
- use the ldap.conf file as an external source
- don't forcibly build the support for version 3
- imported the default spec file from the tarball and fixed it up for RH 6.1
