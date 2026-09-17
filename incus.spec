# Incus LTS for Enterprise Linux 10 (Rocky Linux 10), COPR witteshadovv/incus-lts
# Based on Fedora's incus.spec (src.fedoraproject.org/rpms/incus, 6.23-4) and ganto/copr-lxc4.

%bcond check 1

# Bundled C libraries shipped inside the upstream release tarball (vendor/raft, vendor/cowsql).
# Values from vendor/*/.gitref and vendor/*/configure.ac AC_INIT; re-check on every version bump.
# raft:   .gitref 148951f79a1ed529d6f112661a3067494f1a0917 (cowsql/raft main, 2025-12-27), AC_INIT 0.22.1
# cowsql: .gitref 7c4d73151969ead4f81077ae243d81396ce67988 (cowsql/cowsql main, 2026-04-29), AC_INIT 1.15.9
%global bundled_raft_version    0.22.1^20251227git148951f
%global bundled_cowsql_version  1.15.9^20260429git7c4d731

Name:           incus
Version:        7.0.1
Release:        %autorelease
Summary:        Powerful system container and virtual machine manager
# Incus: Apache-2.0; in-tree C headers: LGPL-2.1-or-later, (L)GPL WITH Linux-syscall-note; bundled raft/cowsql
# (incusd only): LGPL-3.0-only WITH LGPL-3.0-linking-exception; vendored Go modules and in-tree exceptions per
# go-vendor-tools.toml (see MAINTAINING.md), texts in LICENSE.vendor. Subpackage tags list only what their binaries link.
# go-lxc is LGPL-2.1 with a static/dynamic linking exception (no exact SPDX exception id).
License:        Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND GPL-2.0-only WITH Linux-syscall-note AND ISC AND LGPL-2.1-only AND LGPL-2.1-or-later AND LGPL-2.1-or-later WITH Linux-syscall-note AND LGPL-3.0-only WITH LGPL-3.0-linking-exception AND MIT AND MPL-2.0 AND Unlicense AND (Apache-2.0 OR MIT)
URL:            https://linuxcontainers.org/incus
Source0:        https://linuxcontainers.org/downloads/%{name}/%{name}-%{version}.tar.xz
Source1:        https://linuxcontainers.org/downloads/%{name}/%{name}-%{version}.tar.xz.asc
# Stéphane Graber, exported with: gpg --export --export-options export-minimal --armor 602F567663E593BCBD14F338C638974D64792D67
Source2:        gpgkey-602F567663E593BCBD14F338C638974D64792D67.asc

Source101:      %{name}.socket
Source102:      %{name}.service
Source103:      %{name}-startup.service
Source104:      %{name}-user.socket
Source105:      %{name}-user.service
Source106:      %{name}-sysusers.conf
Source107:      %{name}-tmpfiles.conf
Source108:      %{name}-sysctl.conf
Source109:      %{name}-shutdown

# Security fixes from lxc/incus stable-7.0 (zabbly/incus lts-7.0 @5ede4f7 set, plus Patch0024-0027).
# Drop each patch once the new release contains it (MAINTAINING.md, step 1).
# https://github.com/lxc/incus/commit/136444d9b65d17a55519f1a86809f030d58c9c79
Patch0001:      0001-incusd-storage-Strip-unsafe-symlinks-in-externally-s.patch
# https://github.com/lxc/incus/commit/4dc6e1f7935ac13bcff98f6aa213e02815d0dcc8
Patch0002:      0002-incusd-storage-s3-Reject-symlinks-in-bucket-backups.patch
# https://github.com/lxc/incus/commit/001bd0657f9ea6d73368118a01c5248080f2bbef
Patch0003:      0003-incusd-storage-Allow-expected-symlinks-in-instance-m.patch
# https://github.com/lxc/incus/commit/dbc1e36173f8cac74ef276a88ba1e0bc9964002c
Patch0004:      0004-incusd-project-Restrict-volume-creation-options-in-r.patch
# https://github.com/lxc/incus/commit/4f847ad5ab34716efb723e3f46e3d72e472035de
Patch0005:      0005-internal-instance-Prevent-line-breaks-in-NVIDIA-conf.patch
# https://github.com/lxc/incus/commit/7135f0183d9dc0661d2e3eb36779bc2273545266
Patch0006:      0006-incusd-storage-Confine-backup-yaml-write-to-instance.patch
# https://github.com/lxc/incus/commit/1bb869273c69cd5d17558a021028c5dee45d82d4
Patch0007:      0007-incusd-instance-Confine-metadata-yaml-access-to-inst.patch
# https://github.com/lxc/incus/commit/181ae5c746c718767e8ca6f3edbe3df4a6fc9fbe
Patch0008:      0008-incusd-instance-qemu-Confine-template-access-to-inst.patch
# https://github.com/lxc/incus/commit/3d7246efe5ec4dba476f95ec163eb4a165717863
Patch0009:      0009-incusd-images-Validate-image-fingerprint-for-all-pro.patch
# https://github.com/lxc/incus/commit/c7cf33d46a83fd39b59843f0bd406a2c88d2e899
Patch0010:      0010-incusd-storage-Validate-volume-name-on-ISO-and-backu.patch
# https://github.com/lxc/incus/commit/0d21c84dbff03e1a676a94ecbfaafca8b48695ba
Patch0011:      0011-incusd-instances-Validate-instance-name-on-backup-im.patch
# https://github.com/lxc/incus/commit/9bc9f9ba5ab61fd5e6c9fa0f5e2440d4ce8495e5
Patch0012:      0012-incusd-instances-Re-check-restrictions-after-copy-co.patch
# https://github.com/lxc/incus/commit/57c415871256445efa758086e6ef8111464b1c26
Patch0013:      0013-incusd-instance-Enforce-project-restrictions-on-migr.patch
# https://github.com/lxc/incus/commit/f86f08bfcd36aae7e8f29e83e71e6767ddb3e077
Patch0014:      0014-incusd-Expand-network-address-set-project-for-author.patch
# https://github.com/lxc/incus/commit/038fd13e82c107ed40cad7697eabe45f3395a0cf
Patch0015:      0015-incusd-instance-Fix-NVIDIA-require-cuda-and-require.patch
# https://github.com/lxc/incus/commit/1e09276c318107c21091b9811643ef13e8692824
Patch0016:      0016-incusd-instance-Confine-exec-output-access-to-its-di.patch
# https://github.com/lxc/incus/commit/8cdc50343707525e01178b04f11350340b67eaa1
Patch0017:      0017-incusd-Fail-closed-on-unknown-authorization-project.patch
# https://github.com/lxc/incus/commit/a89084e2de1548513d349c5305f509ed80d43240
Patch0018:      0018-incusd-instance-qemu-Use-os-Root-for-template-output.patch
# stable-7.0 0b0847de515424e64fc898f7f5deddb4770ceb14 (zabbly/incus patches/incus-0001-*.patch)
Patch0019:      0019-incusd-instance-Confine-OCI-network-writes-to-instan.patch
# stable-7.0 0de0aac019efe95ba0e6e7e1e6fc3204bf5da5c7 (zabbly/incus patches/incus-0002-*.patch)
Patch0020:      0020-incusd-project-Enforce-isolated-restriction-when-idm.patch
# https://github.com/lxc/incus/commit/8723e980417255462f5123b2aff30973673b2076
Patch0021:      0021-client-images-Prevent-path-traversal-in-downloaded-i.patch
# https://github.com/lxc/incus/commit/2521bf480af23765ea25754fd9a0a2ca146945c6
Patch0022:      0022-incusd-images-Check-access-before-reusing-cross-proj.patch
# EL qemu-kvm (/usr/libexec/qemu-kvm) VM start fix, lxc/incus#3936
# https://github.com/lxc/incus/commit/41abfc72138420da1600920b18c592b398260800
Patch0023:      0023-incusd-instance-qemu-Accept-qemu-kvm-binary-name-in.patch
# https://github.com/lxc/incus/commit/8ce2d877c9181da1c6288d411eb75575f4cc3ed2
Patch0024:      0024-incusd-images-Check-source-instance-access-on-publis.patch
# https://github.com/lxc/incus/commit/a5cf022bcec7a49e1cdfe8e2e159561058434814
Patch0025:      0025-incusd-Validate-OCI-config-json-before-use.patch
# https://github.com/lxc/incus/commit/1ef9eec16e4fe950bedee88ecc0e6100b8cf945f
Patch0026:      0026-incusd-Don-t-close-a-nil-pipe-reader-on-backup-failu.patch
# https://github.com/lxc/incus/commit/1bddf9074df3fcdc76e65098be1688ecc50ae2ce (rebased: context from uncarried f31136c24)
Patch0027:      0027-incusd-Fix-storage-volume-project-expansion.patch

ExclusiveArch:  x86_64 aarch64

BuildRequires:  golang >= 1.25.11
BuildRequires:  go-rpm-macros
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  pkgconf-pkg-config
BuildRequires:  gnupg2
BuildRequires:  gettext
BuildRequires:  help2man
BuildRequires:  systemd-rpm-macros
BuildRequires:  pkgconfig(libuv)
BuildRequires:  pkgconfig(liblz4)
BuildRequires:  pkgconfig(sqlite3)
BuildRequires:  pkgconfig(lxc)
BuildRequires:  pkgconfig(libacl)
BuildRequires:  pkgconfig(libcap)
BuildRequires:  pkgconfig(libudev)

Provides:       bundled(raft) = %{bundled_raft_version}
Provides:       bundled(cowsql) = %{bundled_cowsql_version}

Requires:       %{name}-client%{?_isa} = %{version}-%{release}
Requires:       (container-selinux >= 4:2.245.0 if selinux-policy)
Requires:       attr
Requires:       dnsmasq
Requires:       iproute
Requires:       lxcfs
# EPEL lxcfs.service runs ExecStopPost=/bin/fusermount (package fuse) without requiring it: without it a
# crashed lxcfs leaves a stale mount and incus.service (Requires=lxcfs.service) cannot start.
Requires:       fuse
Requires:       nftables
Requires:       rsync
Requires:       shadow-utils
Requires:       squashfs-tools
Requires:       tar
Requires:       xz
Requires(pre):  systemd
Requires(post): shadow-utils
%{?systemd_requires}

Recommends:     %{name}-agent = %{version}-%{release}
Recommends:     hwdata
Recommends:     skopeo
Recommends:     xdelta
# Virtual machines (weak dependencies, EL10 package names)
Recommends:     qemu-kvm-core
Recommends:     qemu-img
Recommends:     qemu-kvm-device-display-virtio-gpu-pci
Recommends:     virtiofsd
Recommends:     swtpm
Recommends:     swtpm-tools
Recommends:     xorriso
%ifarch x86_64
Recommends:     edk2-ovmf
Recommends:     qemu-kvm-device-display-virtio-vga
%endif
%ifarch aarch64
Recommends:     edk2-aarch64
%endif
Suggests:       %{name}-tools
Suggests:       gdisk
Suggests:       lvm2
Suggests:       qemu-kvm-device-usb-host
Suggests:       squashfs-tools-ng

%description
Incus is a modern, secure and powerful system container and virtual machine
manager. It offers a REST API to manage instances locally or remotely, using
an image based work-flow and with support for live migration.

This package contains the Incus daemon.

%package client
Summary:        Incus command line client
License:        Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND LGPL-2.1-or-later AND MIT AND MPL-2.0 AND Unlicense

%description client
Incus is a modern, secure and powerful system container and virtual machine
manager.

This package contains the command line client.

%package tools
Summary:        Extra tools for Incus
License:        Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND LGPL-2.1-only AND LGPL-2.1-or-later AND LGPL-2.1-or-later WITH Linux-syscall-note AND MIT AND MPL-2.0 AND Unlicense
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description tools
This package contains extra tools provided with Incus:
 - fuidshift: map/unmap filesystem uids/gids
 - incus-benchmark: Incus benchmark utility
 - incus-migrate: physical/virtual machine to Incus migration tool
 - incus-simplestreams: manage a simplestreams image server tree
 - lxc-to-incus: migrate LXC containers to Incus
 - lxd-to-incus: migrate an existing LXD environment to Incus

%package agent
Summary:        Incus virtual machine guest agent
License:        Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND MIT AND MPL-2.0 AND Unlicense

%description agent
Statically linked guest agent for Incus virtual machines. Install it on the
Incus host: the daemon copies it into each virtual machine's config drive,
from which guests load it. It is not meant to be installed inside guests.

%prep
%{gpgverify} --keyring='%{SOURCE2}' --signature='%{SOURCE1}' --data='%{SOURCE0}'
%autosetup -p1
cp -p vendor/raft/LICENSE LICENSE.raft
cp -p vendor/cowsql/LICENSE LICENSE.cowsql
# License/notice texts of all vendored Go modules (each binary links a subset)
find vendor -regextype posix-extended -type f -iregex '.*/(licen[cs]e|copying|copyright|notice|patents|unlicense)[^/]*' \
  ! -path 'vendor/raft/*' ! -path 'vendor/cowsql/*' | LC_ALL=C sort | while read -r f; do
  printf '===== %s =====\n' "$f"; cat "$f"; printf '\n'
done > LICENSE.vendor

%build
BUNDLED="$PWD/_bundled"

# 1. Bundled raft + cowsql as static PIC archives (distro CFLAGS via %%configure).
#    Subshells keep %%configure's exported CFLAGS/LDFLAGS out of the Go build.
(
  cd vendor/raft
  autoreconf -fi
  %configure --prefix="$BUNDLED" --libdir="$BUNDLED/lib" --includedir="$BUNDLED/include" \
    --enable-static --disable-shared --with-pic \
    --disable-benchmark --disable-example --disable-fixture
  %make_build
  make install
)
(
  cd vendor/cowsql
  autoreconf -fi
  export PKG_CONFIG_PATH="$BUNDLED/lib/pkgconfig"
  %configure --prefix="$BUNDLED" --libdir="$BUNDLED/lib" --includedir="$BUNDLED/include" \
    --enable-static --disable-shared --with-pic
  %make_build
  make install
)

# 2. Go environment: module mode (GOPATH mode breaks net/http.ServeMux routing), offline vendor.
unset LDFLAGS
export GO111MODULE=on GOFLAGS=-mod=vendor GOPROXY=off GOTOOLCHAIN=local
# Distro hardening flags minus -Wall (with incus' "#cgo CFLAGS: -Werror" it fails on -Wuse-after-free),
# -Werror=format-security and the LTO flags (the Go link step does no LTO).
export CGO_CFLAGS="$(echo '%{build_cflags}' | sed -E 's/(-flto=auto|-ffat-lto-objects|-Wall|-Werror=format-security)( |$)/ /g') -I$BUNDLED/include"
export CGO_LDFLAGS="-Wl,--as-needed -L$BUNDLED/lib -l:libcowsql.a -l:libraft.a -luv -llz4 -lsqlite3"
export CGO_LDFLAGS_ALLOW="(-Wl,-wrap,pthread_create)|(-Wl,-z,now)"

mkdir -p _build/bin _build/man _build/completions
# NB: %%gobuild is a parametric macro: all arguments must be on ONE line (no "\" continuations).
cgo_cmds="./cmd/incusd ./cmd/incus-user ./cmd/incus ./cmd/fuidshift ./cmd/incus-benchmark ./cmd/incus-simplestreams ./cmd/lxc-to-incus ./cmd/lxd-to-incus"
export GO_BUILDTAGS="libsqlite3"
%gobuild -o _build/bin/ $cgo_cmds

# 3. Static, CGO-free, baseline x86-64 builds like upstream's release binaries: incus-agent is copied
#    into guests, incus-migrate is meant to be copied to the machine being migrated.
for cmd in incus-agent incus-migrate; do
  tags="netgo"; [ "$cmd" = incus-agent ] && tags="agent netgo"
  CGO_ENABLED=0 GOAMD64=v1 go build -compiler gc -a -v -tags="rpm_crashtraceback $tags" \
    -ldflags "-B 0x$(echo "%{name}-%{version}-%{release}-$cmd-${SOURCE_DATE_EPOCH:-}" | sha1sum | cut -d ' ' -f1) -compressdwarf=false" \
    -o _build/bin/$cmd ./cmd/$cmd
done

# 4. Shell completions, man pages, translations
for sh in bash fish zsh; do
  _build/bin/incus completion $sh > _build/completions/incus.$sh
done
_build/bin/incus manpage _build/man/
_build/bin/incusd manpage _build/man/
help2man _build/bin/fuidshift -n "uid/gid shifter" --no-info --no-discard-stderr > _build/man/fuidshift.1
help2man _build/bin/incus-benchmark -n "Incus benchmark tool" --no-info --no-discard-stderr > _build/man/incus-benchmark.1
help2man _build/bin/incus-migrate -n "Physical to instance migration tool" --no-info --no-discard-stderr > _build/man/incus-migrate.1
help2man _build/bin/incus-simplestreams -n "Simplestreams image server tool" --no-info --no-discard-stderr > _build/man/incus-simplestreams.1
help2man _build/bin/lxc-to-incus -n "Convert LXC containers to Incus" --no-info --no-discard-stderr > _build/man/lxc-to-incus.1
help2man _build/bin/lxd-to-incus -n "LXD to Incus migration tool" --no-info --no-discard-stderr > _build/man/lxd-to-incus.1
help2man _build/bin/incus-agent -n "Incus virtual machine guest agent" --no-info --no-discard-stderr > _build/man/incus-agent.1

# glibc has no zh_Hans/zh_Hant locales; ship these catalogs as zh_CN/zh_TW
mv po/zh_Hans.po po/zh_CN.po
mv po/zh_Hant.po po/zh_TW.po
make %{?_smp_mflags} build-mo

%install
install -d %{buildroot}%{_bindir} %{buildroot}%{_libexecdir}/%{name}
for b in incus fuidshift incus-benchmark incus-migrate incus-simplestreams lxc-to-incus lxd-to-incus incus-agent; do
  install -m0755 -p _build/bin/$b %{buildroot}%{_bindir}/$b
done
install -m0755 -p _build/bin/incusd _build/bin/incus-user %{buildroot}%{_libexecdir}/%{name}/
install -m0755 -p %{SOURCE109} %{buildroot}%{_libexecdir}/%{name}/shutdown

install -d %{buildroot}%{_unitdir}
install -m0644 -p %{SOURCE101} %{SOURCE102} %{SOURCE103} %{SOURCE104} %{SOURCE105} %{buildroot}%{_unitdir}/
%ifnarch x86_64
# EL10 aarch64 firmware lives in /usr/share/AAVMF (Incus built-in default); a missing
# INCUS_EDK2_PATH is a hard error, so only set it where /usr/share/edk2/ovmf exists.
sed -i '/^Environment=INCUS_EDK2_PATH=/d' %{buildroot}%{_unitdir}/%{name}.service
%endif
install -D -m0644 -p %{SOURCE106} %{buildroot}%{_sysusersdir}/%{name}.conf
install -D -m0644 -p %{SOURCE107} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -D -m0644 -p %{SOURCE108} %{buildroot}%{_sysctldir}/50-incus.conf

install -d %{buildroot}%{_mandir}/man1
cp -p _build/man/*.1 %{buildroot}%{_mandir}/man1/

install -D -m0644 -p _build/completions/incus.bash %{buildroot}%{bash_completions_dir}/incus
install -D -m0644 -p _build/completions/incus.fish %{buildroot}%{fish_completions_dir}/incus.fish
install -D -m0644 -p _build/completions/incus.zsh %{buildroot}%{zsh_completions_dir}/_incus

install -d -m0700 %{buildroot}%{_localstatedir}/cache/%{name}
install -d -m0700 %{buildroot}%{_localstatedir}/log/%{name}
install -d -m0711 %{buildroot}%{_localstatedir}/lib/%{name}

for mofile in po/*.mo; do
  install -D -m0644 -p "$mofile" %{buildroot}%{_datadir}/locale/$(basename "${mofile%%.mo}")/LC_MESSAGES/%{name}.mo
done
%find_lang %{name}

%if %{with check}
%check
BUNDLED="$PWD/_bundled"
unset LDFLAGS
export GO111MODULE=on GOFLAGS=-mod=vendor GOPROXY=off GOTOOLCHAIN=local
export CGO_CFLAGS="-O2 -g -I$BUNDLED/include"
export CGO_LDFLAGS="-Wl,--as-needed -L$BUNDLED/lib -l:libcowsql.a -l:libraft.a -luv -llz4 -lsqlite3"
export CGO_LDFLAGS_ALLOW="(-Wl,-wrap,pthread_create)|(-Wl,-z,now)"
# Guard: incusd must not be built with the pre-Go-1.22 ServeMux behaviour (GOPATH mode)
if go version -m _build/bin/incusd | grep -q 'httpmuxgo121=1'; then echo "incusd built in GOPATH mode" >&2; exit 1; fi
# Guard: raft/cowsql are linked statically, agent is fully static
if readelf -d _build/bin/incusd | grep -qE 'NEEDED.*lib(cowsql|raft)'; then echo "raft/cowsql linked dynamically" >&2; exit 1; fi
if readelf -l _build/bin/incus-agent | grep -q INTERP; then echo "incus-agent is not static" >&2; exit 1; fi
# lxc-to-incus tests fail (ganto/copr-lxc4#23); test/ holds integration-suite helpers, not unit tests.
go list -tags libsqlite3 ./... | grep -Ev '/test(/|$)|/cmd/lxc-to-incus$' > _build/packages.test
xargs -a _build/packages.test go test -p %{_smp_build_ncpus} -tags libsqlite3 -timeout 30m
%endif

%pre
%sysusers_create_package %{name} %{SOURCE106}
%tmpfiles_create_package %{name} %{SOURCE107}

%post
if [ $1 -eq 1 ]; then
  # Unprivileged containers need a root subordinate id range. Start above login.defs
  # SUB_UID_MAX (600100000) so useradd's automatic ranges never overlap.
  grep -qE '^(root|0):' %{_sysconfdir}/subuid 2>/dev/null || usermod --add-subuids 1000000000-1999999999 root || :
  grep -qE '^(root|0):' %{_sysconfdir}/subgid 2>/dev/null || usermod --add-subgids 1000000000-1999999999 root || :
fi
%systemd_post %{name}.socket %{name}.service %{name}-startup.service %{name}-user.socket %{name}-user.service

%preun
%systemd_preun %{name}.socket %{name}.service %{name}-startup.service %{name}-user.socket %{name}-user.service

%postun
# Restart only the daemons: restarting incus.socket would also restart incus-startup.service
# (Requires=), whose ExecStop shuts down all instances. incusd restarts keep instances running.
%systemd_postun_with_restart %{name}.service %{name}-user.service

%files
%license LICENSE.raft LICENSE.cowsql vendor/modules.txt
%doc README.md
%dir %{_sysctldir}
%{_sysctldir}/50-incus.conf
%{_unitdir}/%{name}.socket
%{_unitdir}/%{name}.service
%{_unitdir}/%{name}-startup.service
%{_unitdir}/%{name}-user.socket
%{_unitdir}/%{name}-user.service
%dir %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/incusd
%{_libexecdir}/%{name}/incus-user
%{_libexecdir}/%{name}/shutdown
%{_sysusersdir}/%{name}.conf
%{_tmpfilesdir}/%{name}.conf
%{_mandir}/man1/incusd*.1*
%attr(700,root,root) %dir %{_localstatedir}/cache/%{name}
%attr(700,root,root) %dir %{_localstatedir}/log/%{name}
%attr(711,root,root) %dir %{_localstatedir}/lib/%{name}
%ghost %attr(711,root,root) %dir /run/%{name}

%files client -f %{name}.lang
%license COPYING LICENSE.vendor vendor/modules.txt
%{_bindir}/incus
%{bash_completions_dir}/incus
%{fish_completions_dir}/incus.fish
%{zsh_completions_dir}/_incus
%{_mandir}/man1/incus.1*
%{_mandir}/man1/incus.*.1*

%files tools
%license vendor/modules.txt
%{_bindir}/fuidshift
%{_bindir}/incus-benchmark
%{_bindir}/incus-migrate
%{_bindir}/incus-simplestreams
%{_bindir}/lxc-to-incus
%{_bindir}/lxd-to-incus
%{_mandir}/man1/fuidshift.1*
%{_mandir}/man1/incus-benchmark.1*
%{_mandir}/man1/incus-migrate.1*
%{_mandir}/man1/incus-simplestreams.1*
%{_mandir}/man1/lxc-to-incus.1*
%{_mandir}/man1/lxd-to-incus.1*

%files agent
%license COPYING LICENSE.vendor vendor/modules.txt
%{_bindir}/incus-agent
%{_mandir}/man1/incus-agent.1*

%changelog
%autochangelog
