#!/usr/bin/env bash
#
# install — put the Agent Vault secret commands on a host's PATH.
#
# The skill itself is installed with the Skills CLI:
#
#   npx skills add Whamp/skills --global --skill agent-vault-secret --yes
#
# This script adds the two commands. On this host they become symlinks into the
# installed skill directory, so there is one copy of each script. A remote host
# gets a copy of the whole skill directory, because a symlink cannot cross hosts.
#
# Usage:
#   scripts/install.sh                  # this host
#   scripts/install.sh --host laptop    # remote host over SSH
#   scripts/install.sh --dry-run

set -euo pipefail

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
skill_name="$(basename "$skill_dir")"
bin_dir="$HOME/.local/bin"

target_host=""
dry_run=false

usage() {
  cat <<'EOF'
install.sh [--host <ssh-host>] [--dry-run]

  --host <ssh-host>   install on a remote host over SSH instead of this one
  --dry-run           show what would be installed, change nothing
  -h, --help          show this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --host) target_host="${2:?--host needs a value}"; shift 2 ;;
    --dry-run) dry_run=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

for src in \
  "$skill_dir/scripts/agent-vault-add-secret.mjs" \
  "$skill_dir/scripts/agent-vault-set-secret.sh" \
  "$skill_dir/SKILL.md"
do
  [ -f "$src" ] || { printf 'missing source file: %s\n' "$src" >&2; exit 1; }
done

where="${target_host:-this host}"
printf 'Installing Agent Vault secret commands on %s from %s\n' "$where" "$skill_dir"
printf '  ~/.local/bin/agent-vault-add-secret\n'
printf '  ~/.local/bin/agent-vault-set-secret\n'
[ -n "$target_host" ] && printf '  ~/.agents/skills/%s/ (copy)\n' "$skill_name"

if [ "$dry_run" = true ]; then
  printf '\ndry run — nothing installed\n'
  exit 0
fi

if [ -n "$target_host" ]; then
  stage="$(mktemp -d)"
  trap 'rm -rf "$stage"' EXIT

  mkdir -p "$stage/.agents/skills" "$stage/.local/bin"
  cp -a "$skill_dir" "$stage/.agents/skills/$skill_name"
  install -m 755 "$skill_dir/scripts/agent-vault-add-secret.mjs" \
    "$stage/.local/bin/agent-vault-add-secret"
  install -m 755 "$skill_dir/scripts/agent-vault-set-secret.sh" \
    "$stage/.local/bin/agent-vault-set-secret"

  tar -C "$stage" -czf - . | ssh \
    -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=25 \
    "$target_host" \
    'mkdir -p "$HOME/.local/bin" "$HOME/.agents/skills" && tar -xzf - -C "$HOME"'
else
  mkdir -p "$bin_dir"
  ln -sfn "$skill_dir/scripts/agent-vault-add-secret.mjs" "$bin_dir/agent-vault-add-secret"
  ln -sfn "$skill_dir/scripts/agent-vault-set-secret.sh" "$bin_dir/agent-vault-set-secret"
fi

printf '\nInstalled. Verify on %s with:\n' "$where"
printf '  command -v agent-vault-add-secret agent-vault-set-secret\n'
printf '  agent-vault-set-secret --check\n'
