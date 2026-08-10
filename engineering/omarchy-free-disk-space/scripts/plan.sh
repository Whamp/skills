#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
MODE=${1:-}

if [[ $MODE != "quick" && $MODE != "deep" ]]; then
  echo "Usage: plan.sh <quick|deep> [--workspace-root PATH ...]" >&2
  exit 2
fi
shift

runtime_dir=${XDG_RUNTIME_DIR:-/tmp}
[[ -d $runtime_dir && ! -L $runtime_dir ]] || {
  echo "Manifest runtime directory is unsafe: $runtime_dir" >&2
  exit 2
}

umask 077
manifest_path=$(mktemp --tmpdir="$runtime_dir" "omarchy-free-disk-space.${UID}.XXXXXX.manifest")

if ! "$SCRIPT_DIR/audit.sh" "$MODE" --emit-manifest "$manifest_path" "$@"; then
  rm -f -- "$manifest_path"
  exit 1
fi
