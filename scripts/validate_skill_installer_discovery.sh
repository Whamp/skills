#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "validate skill installer discovery: expected skills CLI version" >&2
  exit 2
fi

skills_cli_version=$1
repository_root=$(git rev-parse --show-toplevel)
discovery_root=$(mktemp -d "${TMPDIR:-/tmp}/skill-installer-discovery-XXXXXX")
trap 'rm -rf "$discovery_root"' EXIT

tar \
  --exclude='./.git' \
  --exclude='./.worktrees' \
  --exclude='./node_modules' \
  -C "$repository_root" \
  -cf - . \
  | tar -C "$discovery_root" -xf -

npx --yes "skills@$skills_cli_version" add "$discovery_root" --list
