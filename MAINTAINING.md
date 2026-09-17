# Maintaining

## Layout

The repository root is a dist-git style package: `incus.spec`, its sources (systemd units,
sysusers/tmpfiles/sysctl snippets, `incus-shutdown`), patches, the upstream signing key and
`incus.rpmlintrc`. The spec must stay at the root: rpmautospec silently computes a wrong Release
when it lives in a subdirectory.

| Automation | What it does |
| --- | --- |
| `.github/workflows/ci.yml` | PRs: pre-commit, SRPM, mock build + rpmlint + install check on x86_64 and aarch64. Pushes to `main` that touch packaging files: SRPM, mock build + rpmlint + install check, then submit the SRPM to COPR. |
| `.github/workflows/weekly.yml` | Weekly LTS watch: opens/updates one issue labelled `lts-watch` when something needs action (see below). |
| `renovate.json` | PRs for new 7.0.x releases, GitHub Actions and container digests, and pre-commit hooks. |
| `.pre-commit-config.yaml` | Lint hooks; run locally with `pre-commit install`. |

## One-time setup

1. **COPR**: log in at <https://copr.fedorainfracloud.org>, save the config shown at
   <https://copr.fedorainfracloud.org/api/> as `~/.config/copr`, then create the project
   (copr-cli: `dnf install copr-cli` on Fedora, `dnf install epel-release && dnf --enablerepo=crb install copr-cli` on EL10):

   ```sh
   copr-cli create incus-lts \
     --chroot rhel+epel-10-x86_64 --chroot rhel+epel-10-aarch64 \
     --description "Incus LTS for Rocky Linux 10 (https://github.com/WitteShadovv/incus-rocky)" \
     --instructions "See https://github.com/WitteShadovv/incus-rocky#install"
   ```

   Use `rhel+epel-10` chroots, not `epel-10`: the latter builds against CentOS Stream and can pick
   up dependencies newer than the current Rocky Linux minor release.
2. **GitHub environment** `copr` (Settings → Environments), deployment branches limited to `main`,
   with secret `COPR_CONFIG` = the same config file (including its `# expiration date:` line).
3. **Repository settings**: allow squash merging only, with its default commit message left at
   **Default message** (rpmautospec turns every commit on `main` into a Release bump and changelog
   entry; this keeps the `[skip changelog]` body of Renovate's single-commit PRs); protect `main`
   requiring the `pre-commit`, `SRPM`, `RPM (x86_64)` and `RPM (aarch64)` checks; enable private
   vulnerability reporting; keep secret scanning push protection on (the default for public repositories).
4. **Renovate**: install the [Renovate GitHub app](https://github.com/apps/renovate) for this repository.

## Releases and changelog

`Release: %autorelease` and `%autochangelog` (rpmautospec) derive the release number and changelog
from git history: every commit since the last `Version:` change bumps Release, and commit subjects
become changelog entries. Consequences:

- Write squash commit subjects as changelog lines, e.g. `Update Incus LTS to 7.0.2`. GitHub appends
  `(#N)` to the subject, which also ends up in the RPM changelog; delete it in the merge dialog if you do not want it.
- `[skip changelog]` on its own line anywhere in the squash commit message hides the whole PR from the
  changelog. Use it only for PRs that do not change the package (docs, CI), never on a commit pushed
  onto a PR that does.
- Merging to `main` publishes automatically only when packaging files change (`incus*` except
  `incus.rpmlintrc`, `*.patch`, `*.asc`); other merges still bump Release. To retry a failed COPR
  submission, use **Re-run failed jobs** on that run (if the job timed out or only one chroot failed,
  check the build on COPR first). To publish after merges that did not trigger CI (for example a CI
  fix), use **Run workflow** on `main`; it builds main's current Release.
- To ship a rebuild with unchanged sources (for example after a Rocky Linux `golang` update, which the
  weekly watch reports because every Go binary embeds the standard library), merge a PR titled
  `Rebuild with golang X.Y.Z-R` with the version-release the watch reports, raising
  `BuildRequires: golang >=` to it (EL also ships release-only golang fixes). Changing `incus.spec`
  triggers the publish and makes sure the build uses the fixed Go.
- A published build cannot be withdrawn by reverting it: `dnf upgrade` never installs a lower
  version-release, and COPR keeps only the highest build of each package (others are pruned after
  14 days). Downgrading hosts is not safe either, because point releases apply one-way database
  patches. Fix forward (patch or rebuild); to stop new installs of a broken build meanwhile, run
  `copr-cli delete-build <build-id>`.

## Updating to a new point release

Renovate opens "Update Incus LTS to 7.0.N" two days after the upstream release. CI fails on a missed
step 1 or 4, and on step 3 only if Rocky Linux's golang is older than `go.mod`; steps 2, 5 and 6 are
not checked:

1. **Patches**: drop every patch the release already contains. All current `Patch0001`-`Patch0027`
   come from `stable-7.0`; check each with `git merge-base --is-ancestor <commit> v7.0.N` in an
   `lxc/incus` clone. `%autosetup` applies patches with fuzz 0, so a leftover patch fails loudly.
2. **Bundled libraries**: update `bundled_raft_version` / `bundled_cowsql_version` and the comments
   above them: version from `AC_INIT` in `vendor/<lib>/configure.ac`, commit from `vendor/<lib>/.gitref`,
   date from `git log -1 --format=%cd --date=format:%Y%m%d <commit>` in a `cowsql/<lib>` clone.
3. **Go**: keep `BuildRequires: golang >=` at least at the `go` directive in `go.mod`, and make
   sure Rocky Linux ships that version (`dnf --repo appstream list --showduplicates golang`).
4. **Signature**: the tarball must still be signed by `602F567663E593BCBD14F338C638974D64792D67`;
   `%gpgverify` fails otherwise. Treat a failure as a possible compromise, not as a key to add: accept a
   new key only if the old key certified it or upstream announces its fingerprint outside
   linuxcontainers.org/downloads. Then export it with
   `gpg --export --export-options export-minimal --armor <fingerprint> > gpgkey-<fingerprint>.asc` and update `Source2:`,
   the comment above it in `incus.spec` and the fingerprint in this step.
5. **License**: from the repo root (EPEL: `go-vendor-tools askalono-cli rpm-build`), run
   `lic=$(rpmspec --define "_sourcedir $PWD" -q --srpm --qf '%{LICENSE}' incus.spec) && go_vendor_license --config go-vendor-tools.toml -C incus-7.0.N.tar.xz --use-archive report --verify "$lic"`.
   A non-zero exit means `License:` or `go-vendor-tools.toml` needs updating. The check does not see new
   in-tree license notices (compare
   `grep -rIilE 'SPDX-License-Identifier|General Public License|Licensed under|Permission is hereby granted|Redistribution and use' --exclude-dir=vendor --exclude-dir=doc`
   in the extracted tarball with the in-tree entries of `go-vendor-tools.toml`) nor the subpackage tags
   (derive those from `go version -m` of each subpackage's binaries).
6. **Advisories**: in [SECURITY.md](SECURITY.md), update the tarball version in the ledger intro, the
   status column and the patch note below the table for fixes now shipped in the release. Review
   `git log --oneline <reviewed commit>..origin/stable-7.0` for security fixes without an advisory,
   backport the ones the release lacks, and update the reviewed commit in the ledger intro.

## Weekly LTS watch

`weekly.yml` runs every Monday (and on demand). It keeps a single issue labelled `lts-watch` open
while any of these need action, comments when new items appear, and closes it once everything is
resolved:

| Item | Resolve by |
| --- | --- |
| Newer 7.0.x upstream than `Version:` | merging the Renovate PR (see above) |
| New LTS series (e.g. 8.0.0) | migrating (below) |
| Upstream advisory not listed in SECURITY.md | reviewing it against the shipped version + patches, backporting if needed, adding a row |
| COPR has no successful build of the spec version, or the last build failed | fixing the build or re-running CI on `main` |
| Rocky Linux AppStream has a newer `golang` than the published COPR build used | merging a `Rebuild with golang X.Y.Z-R` PR (see [Releases and changelog](#releases-and-changelog)) |
| `COPR_CONFIG` missing or the API token expires within 21 days | regenerating the token at <https://copr.fedorainfracloud.org/api/> and updating the secret (tokens last 180 days) |

A check that cannot run (API outage) keeps last week's items, never closes the issue and fails the
run, so GitHub emails you; a re-run checks out the branch head, so it sees fixes merged since. Manual
runs from a branch other than `main` skip the COPR token check (environment `copr` only admits
`main`), only write the report to the run summary and leave the issue alone. The issue body is
rewritten on every run and must keep starting with its hidden `<!-- lts-watch-keys: -->` marker; add
notes as comments.

GitHub disables scheduled workflows in public repositories after 60 days without commits (it emails
a warning first); merging Renovate's CI tooling PR (opened on Mondays when a tool has an update) usually prevents that. If Actions shows the
workflow as disabled, enable it and run it once manually.

## Moving to the next LTS series

1. Set `Version:` to `X.0.N`, drop all patches, re-check build requirements, runtime dependencies,
   systemd units and `INCUS_*` environment against the new release notes.
2. Grep for the old and next series, JSON-escaped forms included
   (`git grep -nE '\b[78](\\\\)?\.' -- ':!*.patch'`, digits shifted for later series), and update
   `renovate.json` (`allowedVersions` and its description), README.md (series, support end date, the
   "7.1 or newer" note, and the next series and `excludepkgs` example in the upgrade section),
   SECURITY.md (supported series, baseline tarball, `stable-X.0`; keep old rows), this file and the
   `weekly.yml` header comment.
3. Announce it in the README before merging: `dnf upgrade` will move users to the new series.

## Building locally

Same steps as CI, in a privileged Rocky Linux 10 container:

```sh
podman run --rm -it --privileged -v "$PWD:/src:Z" -w /src quay.io/rockylinux/rockylinux:10 bash
dnf -y install epel-release
dnf -y install git-core rpm-build rpmdevtools rpmautospec mock rpmlint glibc-langpack-en
git config --global --add safe.directory /src
spectool --get-files incus.spec
rpmautospec process-distgit incus.spec /tmp/incus.spec
rm -rf srpm results
rpmbuild -bs /tmp/incus.spec --define "_sourcedir /src" --define "_srcrpmdir /src/srpm"
mock -r rocky+epel-10-$(uname -m) --isolation=simple --no-bootstrap-image \
  --resultdir /src/results --rebuild srpm/*.src.rpm
rpmlint --rpmlintrc incus.rpmlintrc results/*.rpm
```

Uncommitted changes are built too, as Release+1 with an `Uncommitted changes` changelog entry;
commit first to get the Release `main` will publish.
