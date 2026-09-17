#!/usr/bin/env bash
# Weekly Incus LTS watch (.github/workflows/weekly.yml): compares the spec with upstream tags,
# security advisories, COPR and Rocky Linux golang, writes a report and keeps one issue (label $ISSUE_LABEL) in sync.
# Local run: DRY_RUN=1 .github/scripts/lts-watch.sh (needs bash, curl, git, jq, tar; gh optional). The golang check
# runs only with ROCKY_GOLANG=$(podman run --rm quay.io/rockylinux/rockylinux:10 dnf -q --repo appstream repoquery \
#   --latest-limit 1 --qf '%{version}-%{release}' golang)
set -euo pipefail

SPEC=${SPEC:-incus.spec}
LEDGER=${LEDGER:-SECURITY.md}
UPSTREAM=${UPSTREAM:-lxc/incus}
COPR_OWNER=${COPR_OWNER:-witteshadovv}
COPR_PROJECT=${COPR_PROJECT:-incus-lts}
COPR_PACKAGE=${COPR_PACKAGE:-incus}
PR_LABEL=${PR_LABEL:-incus-lts}
ISSUE_LABEL=${ISSUE_LABEL:-lts-watch}
TOKEN_WARN_DAYS=${TOKEN_WARN_DAYS:-21}
DRY_RUN=${DRY_RUN:-0}
COPR_TOKEN_DAYS_LEFT=${COPR_TOKEN_DAYS_LEFT:-}
ROCKY_GOLANG=${ROCKY_GOLANG:-}
run_url=${GITHUB_RUN_ID:+${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-}/actions/runs/$GITHUB_RUN_ID}
today=$(date -u +%F)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
keys=() lines=() warnings=() info=()

die() { echo "lts-watch: $*" >&2; exit 1; }
item() { keys+=("$1"); lines+=("$2"); }
warn() { warnings+=("- $1"); echo "::warning::$1" >&2; }
vlt() { [ "$1" != "$2" ] && printf '%s\n' "$1" "$2" | sort -V -C; }

auth=()
[ -z "${GH_TOKEN:-}" ] || auth=(-H "Authorization: Bearer $GH_TOKEN")
gh_get() {
  curl -fsSL --retry 3 --retry-all-errors --max-time 30 -D "$tmp/headers" -H 'Accept: application/vnd.github+json' \
    -H 'X-GitHub-Api-Version: 2022-11-28' "${auth[@]}" "$1"
}
fetch_advisories() {
  local url="https://api.github.com/repos/$UPSTREAM/security-advisories?state=published&per_page=100"
  while [ -n "$url" ]; do
    gh_get "$url" || return 1
    url=$(tr -d '\r' <"$tmp/headers" | sed -n 's/^link:.*<\([^>]*\)>; *rel="next".*/\1/Ip')
  done
}
# A check that could not run keeps its previously reported items: no false "all clear", no re-announcement.
carry() { # carry REASON KEY-PREFIX...
  local why=$1 k p
  shift
  for k in $old_keys; do
    for p in "$@"; do [[ $k != "$p":* ]] || item "$k" "- \`$k\`: not re-checked ($why)"; done
  done
}
gh_do() {
  if [ "$DRY_RUN" != 1 ]; then gh "$@"; return; fi
  printf '+ gh'; printf ' %q' "$@"; echo
  local a
  for a in "$@"; do case $a in "$tmp"/*) sed 's/^/  | /' "$a" ;; esac; done
}

version=$(awk '$1 == "Version:" { print $2; exit }' "$SPEC")
[[ $version =~ ^([0-9]+)\.([0-9]+)\.[0-9]+$ ]] || die "no X.Y.Z Version: in $SPEC"
major=${BASH_REMATCH[1]}
series=$major.${BASH_REMATCH[2]}
[ -r "$LEDGER" ] || die "advisory ledger $LEDGER not found"

tags=$(git ls-remote --tags --refs "https://github.com/$UPSTREAM.git" | sed -n 's#.*refs/tags/v##p' | sort -V) ||
  die "git ls-remote $UPSTREAM failed"
series_tags=$(grep -E "^${series//./\\.}\.[0-9]+$" <<<"$tags") || die "no v$series.N tags upstream"
latest=$(tail -n1 <<<"$series_tags")
next_lts=$(grep -E '^[0-9]+\.0\.0$' <<<"$tags" | awk -F. -v m="$major" '$1 > m' | tail -n1) || true

number="" old_keys=""
# REST, not `gh issue list --label` (search API): a just-created issue is found at once, so no duplicates.
# Only the watch's own issue (body starts with the marker), not a hand-labelled one that merely quotes it.
if issues=$(gh api "repos/{owner}/{repo}/issues?labels=$ISSUE_LABEL&state=open&per_page=100" \
  --jq '[.[] | select(.pull_request == null and (.body // "" | startswith("<!-- lts-watch-keys:"))) | {number, body}]' \
  2>"$tmp/gh.err"); then
  number=$(jq -r '.[0].number // empty' <<<"$issues")
  old_keys=$(jq -r '.[0].body // "" | capture("<!-- lts-watch-keys:(?<k>[^>]*)-->").k' <<<"$issues")
elif [ "$DRY_RUN" = 1 ]; then
  echo "lts-watch: listing issues failed, assuming no open issue: $(cat "$tmp/gh.err")" >&2
else
  die "listing issues failed: $(cat "$tmp/gh.err")"
fi

info+=("- Spec: $version ($(grep -c '^Patch[0-9]*:' "$SPEC" || true) patches)")
info+=("- Upstream: newest $series tag v$latest; newer LTS series: ${next_lts:+v}${next_lts:-none}")

# a) newer point release in our series
if vlt "$version" "$latest"; then
  missing=$(printf '%s\n' "$version" "$series_tags" | sort -uV | awk -v v="$version" 'f; $0 == v { f = 1 }' | paste -sd, -)
  if prs=$(gh pr list --label "$PR_LABEL" --state open --json number,title,url \
    --jq '.[] | "[#\(.number) \(.title)](\(.url))"' 2>"$tmp/gh.err"); then
    prs=${prs//$'\n'/, }
  else
    prs="unknown"
    [ "$DRY_RUN" = 1 ] || warn "gh pr list failed: $(cat "$tmp/gh.err")"
  fi
  line="- **Incus [$latest](https://github.com/$UPSTREAM/releases/tag/v$latest) released**: spec is $version,"
  line+=" missing ${missing//,/, }. Renovate PR (label \`$PR_LABEL\`): ${prs:-none open, Renovate should open one}."
  item "release:$latest" "$line Follow \"Updating to a new point release\" in MAINTAINING.md."
fi

# b) newer LTS series (single stream follows the newest LTS)
if [ -n "$next_lts" ]; then
  line="- **New LTS series [$next_lts](https://github.com/$UPSTREAM/releases/tag/v$next_lts)**: this repository"
  line+=" follows the newest LTS, so $series needs a manual migration."
  item "series:$next_lts" "$line Follow \"Moving to the next LTS series\" in MAINTAINING.md."
fi

# c) advisories not fixed before $major.0.0 and not yet assessed in the ledger
if fetch_advisories >"$tmp/advisories" &&
  jq -se 'length > 0 and all(type == "array")' "$tmp/advisories" >/dev/null 2>&1; then
  jq -rs --argjson major "$major" --rawfile ledger "$LEDGER" '
    add | .[] | select(.ghsa_id as $id | $ledger | contains("\n| [\($id)](") | not)
    | select(.vulnerabilities // [] | length > 0 and all(.patched_versions // ""
        | [capture("^\\s*>=\\s*v?(?<x>[0-9]+)\\.(?<y>[0-9]+)\\.(?<z>[0-9]+)\\s*$") | [.x, .y, .z | tonumber]]
        | length == 1 and .[0] <= [$major, 0, 0]) | not)
    | ["advisory:\(.ghsa_id)", "- **\(.severity // "unknown")** [\(.ghsa_id)](\(.html_url)): `\(.summary // "" | gsub("`"; "\u0027"))`"
      + " (upstream fix: \([.vulnerabilities[]? | .patched_versions // "?"] | unique | join(", ")
        | if . == "" then "?" else . end))"] | @tsv
  ' "$tmp/advisories" >"$tmp/advisories.tsv"
  while IFS=$'\t' read -r key line; do item "$key" "$line"; done <"$tmp/advisories.tsv"
  info+=("- Advisories: $(jq -s 'add | length' "$tmp/advisories") published upstream, $(wc -l <"$tmp/advisories.tsv") relevant and missing from $LEDGER")
else
  warn "Could not fetch $UPSTREAM security advisories"
  carry "see warnings" advisory
fi

# d) COPR publishes the spec version
copr_link="https://copr.fedorainfracloud.org/coprs/$COPR_OWNER/$COPR_PROJECT/"
golang_build=""
code=$(curl -sS --retry 3 --retry-all-errors --max-time 30 -o "$tmp/copr" -w '%{http_code}' \
  "https://copr.fedorainfracloud.org/api_3/package/?ownername=$COPR_OWNER&projectname=$COPR_PROJECT&packagename=$COPR_PACKAGE&with_latest_build=true&with_latest_succeeded_build=true") ||
  code="network error"
[ "$code" != 200 ] || jq -e '.builds | type == "object"' "$tmp/copr" >/dev/null 2>&1 || code="200, unexpected body"
case $code in
  200)
    published=$(jq -r '.builds.latest_succeeded.source_package.version // "" | sub("^[0-9]+:"; "") | sub("-[^-]*$"; "")' "$tmp/copr")
    last=$(jq -r '.builds.latest // {} | "\(.state // "none") \(.id // "")"' "$tmp/copr")
    state=${last% *} build=${last#* }
    info+=("- COPR [$COPR_OWNER/$COPR_PROJECT]($copr_link): publishes ${published:-nothing}; latest build ${build:+#$build }$state")
    case $state in
      pending | starting | importing | running | waiting) carry "COPR build #$build in progress" copr copr-build golang ;;
      *)
        failed=""
        [ "$state" != failed ] || failed="[#$build](https://copr.fedorainfracloud.org/coprs/build/$build/)"
        if [ "$published" != "$version" ]; then
          line="- **COPR does not publish $version**: [$COPR_OWNER/$COPR_PROJECT]($copr_link) has ${published:-no succeeded build}."
          item "copr:$version" "$line${failed:+ Latest build $failed failed.}"
        else
          [ -z "$failed" ] || item "copr-build:$build" "- **Latest COPR build $failed failed** ($version is still published)."
          # COPR result dir of the published build (zero-padded id); any chroot, both use the same golang
          golang_build=$(jq -r '.builds.latest_succeeded | "\(.repo_url)/\(.chroots[0])/\(.id | tostring
            | "0" * (8 - length) + .)-\(.source_package.name)"' "$tmp/copr")
        fi
        ;;
    esac
    ;;
  404)
    item "copr:$version" "- **COPR does not publish $version**: $(jq -r '.error // "not found"' "$tmp/copr" 2>/dev/null || echo 'not found')"
    ;;
  *)
    warn "COPR API unavailable ($code)"
    carry "see warnings" copr copr-build golang
    ;;
esac

# e) COPR API token (days left computed by the copr-token job)
if [ -n "$COPR_TOKEN_DAYS_LEFT" ]; then
  renew="Regenerate the config at https://copr.fedorainfracloud.org/api/ and update secret \`COPR_CONFIG\` (environment \`copr\`)."
  case $COPR_TOKEN_DAYS_LEFT in
    missing) item copr-token:missing "- **Secret \`COPR_CONFIG\` is empty or not readable**: COPR submission fails. $renew" ;;
    unknown) item copr-token:unknown "- **\`COPR_CONFIG\` has no valid \`# expiration date:\` line**: expiry cannot be checked. $renew" ;;
    unavailable) # copr-token job failed
      warn "COPR token expiry not checked: the copr-token job did not succeed"
      carry "see warnings" copr-token
      ;;
    *)
      [[ $COPR_TOKEN_DAYS_LEFT =~ ^-?[0-9]+$ ]] || die "invalid COPR_TOKEN_DAYS_LEFT: $COPR_TOKEN_DAYS_LEFT"
      if [ "$COPR_TOKEN_DAYS_LEFT" -lt 0 ]; then
        item copr-token:expired "- **COPR API token expired** $((-COPR_TOKEN_DAYS_LEFT)) day(s) ago. $renew"
      elif [ "$COPR_TOKEN_DAYS_LEFT" -lt "$TOKEN_WARN_DAYS" ]; then
        item copr-token:expiring "- **COPR API token expires in $COPR_TOKEN_DAYS_LEFT day(s)**. $renew"
      fi
      info+=("- COPR token: $COPR_TOKEN_DAYS_LEFT day(s) left")
      ;;
  esac
fi

# f) golang: every Go binary embeds the standard library, so a newer Rocky Linux golang needs a rebuild.
# Compared with the golang the published COPR build installed (no published build: the copr item covers it).
if [ -n "$ROCKY_GOLANG" ] && [ -n "$golang_build" ]; then
  used=$(curl -fsSL --retry 3 --retry-all-errors --max-time 60 "$golang_build/chroot_scan.tar.gz" |
    tar -xzO --wildcards '*/var/log/dnf.rpm.log' | sed -n 's/.* Installed: golang-\([0-9][^ ]*\)\.[^.]*$/\1/p' | tail -n1) || used=""
  # COPR builds with RHEL's golang, which never has Rocky's own rebuild suffix (1.20.12-2.el9_3.0.1, .rocky.0.1)
  [[ ! $ROCKY_GOLANG =~ ^(.*\.el[0-9_]+)(\.rocky)?\.0\.[0-9]+$ ]] || ROCKY_GOLANG=${BASH_REMATCH[1]}
  # ROCKY_GOLANG is "unavailable" when the rocky-golang job failed
  if [[ ! $ROCKY_GOLANG =~ ^[0-9][0-9.]*-[0-9][0-9A-Za-z._]*$ ]] || [ -z "$used" ]; then
    warn "golang not compared (newest in Rocky Linux: $ROCKY_GOLANG; in $golang_build/chroot_scan.tar.gz: ${used:-not found})"
    carry "see warnings" golang
  else
    info+=("- golang: Rocky Linux has $ROCKY_GOLANG, published COPR build used $used")
    # sort -V orders EL golang version-releases (no epoch, ~ or ^) like rpm; COPR's RHEL golang may be newer than Rocky's
    if vlt "$used" "$ROCKY_GOLANG"; then
      line="- **Rocky Linux golang $ROCKY_GOLANG** is newer than $used in the published COPR build: merge a PR"
      line+=" \"Rebuild with golang $ROCKY_GOLANG\" that raises \`BuildRequires: golang >=\` to it."
      item "golang:$ROCKY_GOLANG" "$line Follow \"Releases and changelog\" in MAINTAINING.md."
    fi
  fi
fi
[ -z "$run_url" ] || info+=("- [Workflow run]($run_url)")

report() {
  echo "<!-- lts-watch-keys: ${keys[*]} -->"
  printf '## Incus %s LTS watch (%s)\n\n### Action items\n\n' "$series" "$today"
  if [ ${#lines[@]} -gt 0 ]; then printf '%s\n' "${lines[@]}"; else echo "None."; fi
  if [ ${#warnings[@]} -gt 0 ]; then printf '\n### Warnings\n\n'; printf '%s\n' "${warnings[@]}"; fi
  printf '\n### Info\n\n'
  printf '%s\n' "${info[@]}"
}
body=$tmp/body.md
report >"$body"
[ -z "${GITHUB_STEP_SUMMARY:-}" ] || cat "$body" >>"$GITHUB_STEP_SUMMARY"
cat "$body"

new=()
for i in "${!keys[@]}"; do
  [[ " $old_keys " == *" ${keys[i]} "* ]] || new+=("${lines[i]}")
done
if [ ${#keys[@]} -gt 0 ] && [ -z "$number" ]; then
  gh_do label create "$ISSUE_LABEL" --force --color D93F0B --description "Weekly Incus LTS watch"
  gh_do issue create --title "Incus LTS watch: action needed" --label "$ISSUE_LABEL" --body-file "$body"
elif [ -n "$number" ] && { [ ${#keys[@]} -gt 0 ] || [ ${#warnings[@]} -gt 0 ]; }; then # no "all clear" with warnings
  gh_do issue edit "$number" --body-file "$body"
  if [ ${#new[@]} -gt 0 ]; then
    { printf 'New since the last check:\n\n'; printf '%s\n' "${new[@]}"; } >"$tmp/comment.md"
    [ -z "$run_url" ] || printf '\n[Workflow run](%s)\n' "$run_url" >>"$tmp/comment.md"
    gh_do issue comment "$number" --body-file "$tmp/comment.md"
  fi
elif [ -n "$number" ]; then
  gh_do issue edit "$number" --body-file "$body"
  gh_do issue close "$number" --comment "All clear on $today: no LTS action items left.${run_url:+ [Workflow run]($run_url)}"
fi

# Checks that could not run fail the run (after reporting), so a persistently broken watch gets noticed.
[ ${#warnings[@]} -eq 0 ] || die "${#warnings[@]} check(s) could not run, see the report"
