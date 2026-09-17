# incus-rocky

[![CI](https://github.com/WitteShadovv/incus-rocky/actions/workflows/ci.yml/badge.svg)](https://github.com/WitteShadovv/incus-rocky/actions/workflows/ci.yml)
[![COPR](https://copr.fedorainfracloud.org/coprs/witteshadovv/incus-lts/package/incus/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/witteshadovv/incus-lts/)

[Incus](https://linuxcontainers.org/incus/) **LTS** RPMs for Rocky Linux 10 (x86_64, aarch64),
built in Fedora COPR [`witteshadovv/incus-lts`](https://copr.fedorainfracloud.org/coprs/witteshadovv/incus-lts/).

Only LTS releases are packaged (currently **7.0.x**, supported upstream until June 2031); feature
releases (7.1, 7.2, ...) are never shipped. This repository moves to the next LTS when it is released,
see [Upgrades between LTS series](#upgrades-between-lts-series).

## Install

```sh
sudo dnf install epel-release dnf-plugins-core
sudo dnf copr enable witteshadovv/incus-lts rhel+epel-10-$(uname -m)
sudo dnf install incus incus-tools
sudo systemctl enable --now incus.socket incus-user.socket incus-startup.service
sudo usermod -aG incus-admin "$USER"   # root-equivalent, applies at next login (or newgrp incus-admin)
sudo incus admin init
```

Members of group `incus` instead get restricted per-user projects through `incus-user`.

The chroot argument is required: a plain `dnf copr enable witteshadovv/incus-lts` guesses the
CentOS Stream based `epel-10` chroot, while this project builds against `rhel+epel-10`
(same minor release as Rocky Linux).

If another repository also provides `incus` (for example `ligenix/enterprise-qemu-spice` from the
Rocky Linux documentation, `neelc/incus` or `totocz/incus`; check with
`dnf repoquery --qf '%{repoid} %{evr}' incus`), disable it or add `excludepkgs=incus*` to its repo
file: dnf installs the highest version from any repository. Incus cannot be downgraded, so a host
that already ran 7.1 or newer cannot switch to this repository.

| Package | Contents |
| --- | --- |
| `incus` | daemon (`incusd`, `incus-user`), systemd units |
| `incus-client` | `incus` command line client, completions, man pages |
| `incus-agent` | static VM guest agent (installed with `incus` as a weak dependency) |
| `incus-tools` | `fuidshift`, `incus-benchmark`, `incus-migrate`, `incus-simplestreams`, `lxc-to-incus`, `lxd-to-incus` |

## Host notes

- **firewalld**: instances need DHCP, DNS and forwarding on the Incus bridge. The simplest way is the
  `trusted` zone, which also lets every instance reach every service on the host, so use it only when
  all instance users are trusted:
  `sudo firewall-cmd --zone=trusted --change-interface=incusbr0 --permanent && sudo firewall-cmd --reload`
- **Unprivileged containers** need subordinate IDs for root. On first install the package adds
  `root:1000000000:1000000000` to `/etc/subuid` and `/etc/subgid` if root has no entry yet
  (restart `incus` after changing these files).
- **sysctl**: the package raises the inotify and keyring limits host-wide (`/usr/lib/sysctl.d/50-incus.conf`);
  override them in `/etc/sysctl.d/`. Upstream's server settings page lists further production values.
- **SELinux** stays enforcing, but `container-selinux` only labels Incus' files: `incusd` and its
  instances run unconfined. Keep containers unprivileged; `security.privileged=true` is not root-safe.
- **Storage**: `dir` and `lvm` work with stock packages; ZFS and Ceph need third-party repositories;
  btrfs needs a non-stock kernel (the EL10 kernel ships no btrfs module).
- `br_netfilter` (needed for some proxy/forward setups) is in `kernel-modules-extra`.

## Virtual machines

VM support uses RHEL's `qemu-kvm`, which is built without SPICE and 9p:

- no `incus console --type=vga` and no USB redirection;
- the VM agent must be delivered as a CD-ROM, through a VM-only profile (containers reject it):

  ```sh
  incus profile create vm
  incus profile device add vm agent disk source=agent:config
  incus launch images:rockylinux/10 v1 --vm -p default -p vm
  ```

- no `io.bus=nvme` disks;
- aarch64: EL10's Secure Boot firmware relies on QEMU host-side UEFI variables, which Incus does not use,
  so run `incus profile set vm security.secureboot=false`;
  images.linuxcontainers.org has no arm64 VM image for `rockylinux/10`, so use e.g. `images:debian/13`.

## Upgrades between LTS series

This repository follows the **newest** LTS series. When the next LTS (8.0) is adopted, `dnf upgrade`
moves hosts from 7.0 to 8.0, and the Incus database upgrade cannot be undone. This repository stops
publishing 7.0.x at that point; to hold a host on 7.0 until you are ready, exclude the next series:

```sh
sudo dnf config-manager --save \
  --setopt='copr:copr.fedorainfracloud.org:witteshadovv:incus-lts.excludepkgs=incus*-8.*'
```

(`dnf copr enable` rewrites that repo file; re-apply the option if you run it again.)

## Project

- Bugs: packaging problems in [issues](https://github.com/WitteShadovv/incus-rocky/issues), Incus bugs
  upstream at <https://github.com/lxc/incus/issues>, vulnerabilities per [SECURITY.md](SECURITY.md).
- [MAINTAINING.md](MAINTAINING.md): how packages are built, updated and published.
- Packaging files are MIT licensed ([LICENSE](LICENSE)); Incus and the backported upstream patches
  (`*.patch`) are Apache-2.0.
