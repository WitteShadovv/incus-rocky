# Security policy

## Reporting a vulnerability

- **Packaging issues** (spec file, patches as applied here, systemd units, users, file permissions,
  COPR builds): use [private vulnerability reporting](https://github.com/WitteShadovv/incus-rocky/security/advisories/new)
  on this repository. Please do not open a public issue.
- **Bugs in Incus itself**: report them upstream at <https://github.com/lxc/incus/security>. Fixes
  published there are tracked in the ledger below.

Only the latest 7.0.x build published in COPR receives fixes.

## Upstream advisory ledger

Upstream advisories only name feature releases (for example `< v7.3.0`), so they do not say whether
an LTS point release contains the fix. Each advisory is therefore checked against what this
repository ships: the `v7.0.1` release tarball plus the patches in `incus.spec`. The ledger covers
Incus advisories only; vulnerabilities in vendored Go modules are fixed through 7.0.x point releases.
The Go standard library is compiled into every binary, so its fixes ship as rebuilds against the
updated EL10 `golang`; the weekly `lts-watch` issue flags one when Rocky Linux ships a newer `golang`
than the published build used.

Status is **Fixed in 7.0.N** (the fix is an ancestor of the release tag), **Fixed by PatchNNNN**
(backported from `stable-7.0`), **NOT FIXED** or **Not applicable** (with the reason). Advisories not
fixed in 7.0.0 and missing from this table are listed in the weekly `lts-watch` issue (see
MAINTAINING.md). Commit ids are on the upstream `stable-7.0` branch. Last full review: 2026-09-17,
through `stable-7.0` commit `8ffb8bf04335`.

| Advisory | Severity | Summary | Status for incus-rocky |
| --- | --- | --- | --- |
| [GHSA-9pqw-c7m4-xvg7](https://github.com/lxc/incus/security/advisories/GHSA-9pqw-c7m4-xvg7) (CVE-2026-81500) | Medium | `incus` client path traversal when exporting an image from a malicious server | Fixed by Patch0021 (`8723e9804172`) |
| [GHSA-c6wx-8679-hpr9](https://github.com/lxc/incus/security/advisories/GHSA-c6wx-8679-hpr9) (CVE-2026-81501) | Medium | Restricted client can import a private image from another project | Fixed by Patch0022 (`2521bf480af2`) |
| [GHSA-53cg-qvg7-m8vg](https://github.com/lxc/incus/security/advisories/GHSA-53cg-qvg7-m8vg) (CVE-2026-62313) | Medium | Isolation restriction bypass by omitting `security.idmap.isolated` | Fixed by Patch0020 (`0de0aac019ef`, rebased) |
| [GHSA-q7xw-r4w2-2wcm](https://github.com/lxc/incus/security/advisories/GHSA-q7xw-r4w2-2wcm) (CVE-2026-62867) | Critical | Argument injection through `block.create_options` | Fixed by Patch0004 (`dbc1e36173f8`) |
| [GHSA-qw5c-v953-38gw](https://github.com/lxc/incus/security/advisories/GHSA-qw5c-v953-38gw) (CVE-2026-62940) | Critical | Restriction bypass via migration config override | Fixed by Patch0013 (`57c415871256`) |
| [GHSA-mq9x-prm8-3vpw](https://github.com/lxc/incus/security/advisories/GHSA-mq9x-prm8-3vpw) (CVE-2026-62941) | Critical | Restriction bypass via cross-project instance copy | Fixed by Patch0012 (`9bc9f9ba5ab6`) |
| [GHSA-m3j6-p3v3-qmjv](https://github.com/lxc/incus/security/advisories/GHSA-m3j6-p3v3-qmjv) (CVE-2026-81498) | High | Newline injection through `nvidia.driver.capabilities` | Fixed by Patch0005 (`4f847ad5ab34`) |
| [GHSA-6rqx-22hc-qm36](https://github.com/lxc/incus/security/advisories/GHSA-6rqx-22hc-qm36) (CVE-2026-63125) | Critical | Host file write via `backup.yaml` symlink in image | Fixed by Patch0006 (`7135f0183d9d`); Patch0001 (refined by Patch0003) strips such symlinks |
| [GHSA-fmjx-5j3g-997p](https://github.com/lxc/incus/security/advisories/GHSA-fmjx-5j3g-997p) (CVE-2026-63343) | Critical | Host file read/write via `metadata.yaml` symlink in image | Fixed by Patch0007 (`1bb869273c69`); Patch0001 (refined by Patch0003) strips such symlinks |
| [GHSA-p2v3-6wvc-cv3p](https://github.com/lxc/incus/security/advisories/GHSA-p2v3-6wvc-cv3p) (CVE-2026-81493) | Critical | Host file write via image fingerprint path traversal | Fixed by Patch0009 (`3d7246efe5ec`) |
| [GHSA-4qxq-p5hm-3q3p](https://github.com/lxc/incus/security/advisories/GHSA-4qxq-p5hm-3q3p) (CVE-2026-81497) | High | Host file read/write via VM template path traversal | Fixed by Patch0008 (`181ae5c746c7`); Patch0018 adds `os.Root` for output |
| [GHSA-7fj9-65v4-rp7h](https://github.com/lxc/incus/security/advisories/GHSA-7fj9-65v4-rp7h) (CVE-2026-81494) | Critical | Host file write via image symlinks and `oci.dns.*` newlines | Fixed by Patch0006 (`backup.yaml`) and Patch0019 (`0b0847de5154`, rebased: `resolv.conf`, `oci.dns.*`) |
| [GHSA-26gp-p5fw-3r2h](https://github.com/lxc/incus/security/advisories/GHSA-26gp-p5fw-3r2h) (CVE-2026-81496) | Critical | Host file write via path traversal in instance backup import | Fixed by Patch0011 (`0d21c84dbff0`) |
| [GHSA-67qw-68v3-36h6](https://github.com/lxc/incus/security/advisories/GHSA-67qw-68v3-36h6) (CVE-2026-81495) | Critical | Host file write via path traversal in custom volume import | Fixed by Patch0010 (`c7cf33d46a83`) |
| [GHSA-6v6x-387m-rj4w](https://github.com/lxc/incus/security/advisories/GHSA-6v6x-387m-rj4w) (CVE-2026-81499) | Medium | Restriction bypass on network address sets | Fixed by Patch0014 (`f86f08bfcd36`); Patch0017 fails closed for other object types |
| [GHSA-48q5-w887-33wv](https://github.com/lxc/incus/security/advisories/GHSA-48q5-w887-33wv) (CVE-2026-48751) | Critical | Restriction bypass via snapshot restore, command execution | Fixed in 7.0.1 (`12df568641cf`) |
| [GHSA-73hr-m85f-64v9](https://github.com/lxc/incus/security/advisories/GHSA-73hr-m85f-64v9) (CVE-2026-48750) | Critical | Host file write via `exec-output` symlink in image | Fixed in 7.0.1 (`b2c7f02aca01`); Patch0016 confines exec output access |
| [GHSA-vxp5-584q-c479](https://github.com/lxc/incus/security/advisories/GHSA-vxp5-584q-c479) (CVE-2026-48752) | Critical | Host file read/write via `templates/` symlink in image | Fixed in 7.0.1 (`d9d80e87c7ac`); VM driver completed by Patch0008 (GHSA-4qxq-p5hm-3q3p) |
| [GHSA-2q3f-q5pq-g8wv](https://github.com/lxc/incus/security/advisories/GHSA-2q3f-q5pq-g8wv) (CVE-2026-48749) | Critical | Host file read/write via `rootfs/` symlink in image | Fixed in 7.0.1 (`33c91cf10f90`) |
| [GHSA-v6mj-8pf4-hhw4](https://github.com/lxc/incus/security/advisories/GHSA-v6mj-8pf4-hhw4) (CVE-2026-48755) | Critical | Argument injection in backup compression algorithm | Fixed in 7.0.1 (`a34b4d531b2c`) |
| [GHSA-f6m5-xw2g-xc4x](https://github.com/lxc/incus/security/advisories/GHSA-f6m5-xw2g-xc4x) (CVE-2026-48769) | Critical | Host file write via trusted image hash (direct download) | Fixed in 7.0.1 (`609acee9fdce`); other protocols fixed by Patch0009 (GHSA-p2v3-6wvc-cv3p) |
| [GHSA-c9f5-j9c3-mhrg](https://github.com/lxc/incus/security/advisories/GHSA-c9f5-j9c3-mhrg) (CVE-2026-55622) | High | Restriction bypass in instance copy across projects | Fixed in 7.0.1 (`83e31cfef356`) |
| [GHSA-64f3-v33m-w89f](https://github.com/lxc/incus/security/advisories/GHSA-64f3-v33m-w89f) (CVE-2026-55621) | High | Restriction bypass in custom volume copy across projects | Fixed in 7.0.1 (`457687e5a0ae`) |
| [GHSA-ccjc-4qc3-jxqc](https://github.com/lxc/incus/security/advisories/GHSA-ccjc-4qc3-jxqc) (CVE-2026-48753) | Critical | Host file write via path traversal in S3 multipart upload | Fixed in 7.0.1 (`9e3748f9396f`) |
| [GHSA-8g7m-96c8-8wwc](https://github.com/lxc/incus/security/advisories/GHSA-8g7m-96c8-8wwc) (CVE-2026-47753) | Low | Daemon crash on instance backup import without volume | Fixed in 7.0.1 (`5a75b878a5b0`) |
| [GHSA-4xg6-52mh-fpw8](https://github.com/lxc/incus/security/advisories/GHSA-4xg6-52mh-fpw8) (CVE-2026-48754) | Low | Daemon crash in `createDependentVolumesFromBackup` | Fixed in 7.0.1 (`81f334ffe18f`) |
| [GHSA-xhqx-mgh3-3h7q](https://github.com/lxc/incus/security/advisories/GHSA-xhqx-mgh3-3h7q) (CVE-2026-48756) | Low | Daemon crash in `CreateCustomVolumeFromBackup` | Fixed in 7.0.1 (`8c2c02bd4b3e`) |

Patch0002 (rejects symlinks in S3 bucket backups) is a security hardening without an advisory of its
own; Patch0015 fixes inverted `nvidia.require.*` handling, a functional fix from the same batch.
Patch0024 adds the missing instance view check when publishing an image, Patch0025 stops a crafted OCI
image from crashing incusd, Patch0026 stops a failed backup from crashing incusd, and Patch0027 makes
custom storage volume permission checks use the right project (fixes on `stable-7.0` without an
advisory).
