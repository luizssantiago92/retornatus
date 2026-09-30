#!/usr/bin/env bash
# Composite action entrypoint. Inputs arrive as environment variables.
# Do not print the environment: GH_TOKEN is the comment credential.
set -euo pipefail

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

version="${RETORNATUS_VERSION:-latest}"
change="${RETORNATUS_CHANGE:-}"
base="${RETORNATUS_BASE:-}"
comment=$(printf '%s' "${RETORNATUS_COMMENT:-true}" | tr '[:upper:]' '[:lower:]')
fail_on=$(printf '%s' "${RETORNATUS_FAIL_ON:-not_satisfied}" | tr '[:upper:]' '[:lower:]')
event_name="${EVENT_NAME:-}"
pr_number="${PR_NUMBER:-}"
pr_base_sha="${PR_BASE_SHA:-}"
pr_fork=$(printf '%s' "${PR_FORK:-}" | tr '[:upper:]' '[:lower:]')
repo="${REPO:?REPO is required}"
default_branch="${DEFAULT_BRANCH:-main}"
omission_mode=$(printf '%s' "${RETORNATUS_OMISSION:-fail}" | tr '[:upper:]' '[:lower:]')

write_outputs() {
  local verdict_word="$1"
  local json_path="$2"
  if [ -z "${GITHUB_OUTPUT:-}" ]; then
    echo "error: GITHUB_OUTPUT is required" >&2
    exit 1
  fi
  {
    echo "verdict<<EOF"
    echo "$verdict_word"
    echo "EOF"
    echo "json<<EOF"
    echo "$json_path"
    echo "EOF"
  } >>"$GITHUB_OUTPUT"
}

run_json() {
  local outfile="$1"
  shift
  local errfile
  errfile="$(mktemp)"
  set +e
  "$@" --json >"$outfile" 2>"$errfile"
  local code=$?
  set -e
  if [ -s "$errfile" ]; then
    cat "$errfile" >&2
  fi
  rm -f "$errfile"
  if [ "$code" -eq 2 ]; then
    echo "error: usage error from: $*" >&2
    exit 2
  fi
  if [ ! -s "$outfile" ]; then
    echo "error: no JSON from: $*" >&2
    exit 1
  fi
}

note_skip() {
  local reason="$1"
  echo "Skipping pull request comment: ${reason}."
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    printf '\nPull request comment skipped (%s).\n' "$reason" >>"$GITHUB_STEP_SUMMARY"
  fi
}

post_or_update_comment() {
  local comment_file="$1"
  local workdir="$2"
  local repo_name="$3"
  local number="$4"
  local payload="$workdir/comment-payload.json"
  local list_err="$workdir/list.err"
  local post_err="$workdir/post.err"
  python3 -c 'import json, pathlib, sys; pathlib.Path(sys.argv[2]).write_text(json.dumps({"body": pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")}), encoding="utf-8")' \
    "$comment_file" "$payload"
  local ids=""
  if ! ids="$(gh api --paginate "repos/${repo_name}/issues/${number}/comments" \
      --jq '.[] | select((.body // "") | contains("<!-- retornatus-verdict -->")) | .id' \
      2>"$list_err")"; then
    if grep -Eq '403|Resource not accessible' "$list_err"; then
      note_skip "read-only token"
      return 0
    fi
    cat "$list_err" >&2
    return 1
  fi
  local existing="${ids%%$'\n'*}"
  existing="${existing//[[:space:]]/}"
  local method path
  if [ -n "$existing" ]; then
    if ! printf '%s' "$existing" | grep -Eq '^[0-9]+$'; then
      echo "error: comment id was not numeric" >&2
      return 1
    fi
    method="PATCH"
    path="repos/${repo_name}/issues/comments/${existing}"
    echo "Updating Retornatus comment ${existing}."
  else
    method="POST"
    path="repos/${repo_name}/issues/${number}/comments"
    echo "Creating Retornatus comment."
  fi
  if ! gh api --method "$method" "$path" --input "$payload" >/dev/null 2>"$post_err"; then
    if grep -Eq '403|Resource not accessible' "$post_err"; then
      note_skip "read-only token"
      return 0
    fi
    cat "$post_err" >&2
    return 1
  fi
  return 0
}

case "$fail_on" in
  not_satisfied|never) ;;
  *)
    echo "error: fail-on must be not_satisfied or never" >&2
    exit 2
    ;;
esac
case "$comment" in
  true|false) ;;
  *)
    echo "error: comment must be true or false" >&2
    exit 2
    ;;
esac
case "$omission_mode" in
  fail|warn) ;;
  *)
    echo "error: RETORNATUS_OMISSION must be fail or warn" >&2
    exit 2
    ;;
esac
if [ -n "$change" ] && ! printf '%s' "$change" | grep -Eq '^C-[0-9]+$'; then
  echo "error: change must look like C-0001" >&2
  exit 2
fi

case "$version" in
  latest)
    uv tool install --force retornatus
    ;;
  local)
    uv tool install --force --from "${GITHUB_WORKSPACE}" retornatus
    ;;
  *)
    if ! printf '%s' "$version" | grep -Eq '^[0-9A-Za-z][0-9A-Za-z._+-]*$'; then
      echo "error: version must be latest, local, or a release number" >&2
      exit 2
    fi
    uv tool install --force "retornatus==${version}"
    ;;
esac

tool_bin="$(uv tool dir --bin)"
export PATH="${tool_bin}:${HOME}/.local/bin:${PATH}"
hash -r
if ! command -v retornatus >/dev/null 2>&1; then
  echo "error: retornatus was not installed onto PATH" >&2
  exit 1
fi
if ! retornatus ci comment --help >/dev/null 2>&1; then
  echo "error: this Retornatus build has no 'ci comment' command." >&2
  echo "Install the release that ships with this action, or set version: local." >&2
  exit 1
fi

if [ -z "$base" ]; then
  if [ -n "$pr_base_sha" ]; then
    base="$pr_base_sha"
  else
    base="origin/${default_branch}"
  fi
fi
if printf '%s' "$base" | grep -Eq '[[:space:]`$;&|<>]'; then
  echo "error: base contains unsupported characters" >&2
  exit 2
fi
if ! git rev-parse --verify --quiet "${base}^{commit}" >/dev/null; then
  echo "error: base ${base} is not in this clone. Check out with fetch-depth: 0." >&2
  exit 1
fi

workdir="${RUNNER_TEMP:-/tmp}/retornatus-ci"
mkdir -p "$workdir"

changes=()
if [ -n "$change" ]; then
  changes+=("$change")
else
  while IFS= read -r cid; do
    [ -n "$cid" ] || continue
    changes+=("$cid")
  done < <(
    git diff --name-only "${base}...HEAD" -- .retornatus/changes \
      | sed -n 's|^\.retornatus/changes/\(C-[0-9][0-9]*\)/.*|\1|p' \
      | sort -u
  )
fi

code_changed=0
if [ -z "$change" ]; then
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    case "$path" in
      src/*|tests/*|scripts/*|templates/*|pyproject.toml|uv.lock)
        code_changed=1
        ;;
    esac
  done < <(git diff --name-only "${base}...HEAD")
fi

omission=0
if [ "${#changes[@]}" -eq 0 ] && [ "$code_changed" -eq 1 ]; then
  echo "Code changed but no .retornatus Change was touched (skip-by-omission)."
  if [ "$omission_mode" = "warn" ]; then
    echo "::warning::Code changed but no Change was touched"
  else
    omission=1
  fi
fi

echo "::group::gate suppressions"
run_json "$workdir/gate-suppressions.json" retornatus gate suppressions --base "$base"
echo "::endgroup::"

verify_args=()
gate_args=(--gate "$workdir/gate-suppressions.json")
if [ "${#changes[@]}" -gt 0 ]; then
  for cid in "${changes[@]}"; do
    echo "::group::verify ${cid}"
    run_json "$workdir/verify-${cid}.json" retornatus verify "$cid"
    echo "::endgroup::"
    echo "::group::gate scope ${cid}"
    run_json "$workdir/gate-scope-${cid}.json" retornatus gate scope "$cid" --base "$base"
    echo "::endgroup::"
    verify_args+=(--verify "$workdir/verify-${cid}.json")
    gate_args+=(--gate "$workdir/gate-scope-${cid}.json")
  done
fi

comment_file="$workdir/comment.md"
bundle="$workdir/verdict.json"
cmd=(
  retornatus ci comment
  --path "${GITHUB_WORKSPACE}"
  --bundle "$bundle"
  --verdict-file "$workdir/verdict.txt"
)
if [ "$omission" -eq 1 ]; then
  cmd+=(--omission)
  cmd+=(--note "Code changed but no .retornatus Change was touched.")
fi
if [ "${#verify_args[@]}" -gt 0 ]; then
  cmd+=("${verify_args[@]}")
fi
cmd+=("${gate_args[@]}")
"${cmd[@]}" >"$comment_file"
verdict="$(tr -d '[:space:]' <"$workdir/verdict.txt")"
case "$verdict" in
  SATISFIED|NOT_SATISFIED|INCONCLUSIVE) ;;
  *)
    echo "error: unexpected verdict '${verdict}'" >&2
    exit 1
    ;;
esac

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "<!-- retornatus step summary -->"
    cat "$comment_file"
  } >>"$GITHUB_STEP_SUMMARY"
fi

if [ "$comment" != "true" ]; then
  note_skip "comment input is false"
elif [ "$event_name" != "pull_request" ] || [ -z "$pr_number" ]; then
  note_skip "this run is not a pull request"
elif [ "$pr_fork" = "true" ]; then
  note_skip "fork pull requests use a read-only token"
else
  if ! post_or_update_comment "$comment_file" "$workdir" "$repo" "$pr_number"; then
    echo "error: could not create or update the pull request comment" >&2
    write_outputs "$verdict" "$bundle"
    exit 1
  fi
fi

write_outputs "$verdict" "$bundle"
if [ "$fail_on" = "not_satisfied" ] && [ "$verdict" != "SATISFIED" ]; then
  exit 1
fi
exit 0
