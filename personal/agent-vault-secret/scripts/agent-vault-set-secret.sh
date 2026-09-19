#!/usr/bin/env bash
#
# agent-vault-set-secret — prompt for a secret on this terminal and write it to
# Agent Vault.
#
# This is the no-Glimpse path. It works on a laptop, over SSH, or anywhere a
# native window is unavailable. The value is read with `read -rsp` (no echo),
# never enters argv on this host, and is not written to shell history.
#
# Run this yourself, in a terminal no agent is attached to. If an agent runs it
# for you, the value lands in a terminal the agent can read, and from there in
# its context.
#
# Usage:
#   agent-vault-set-secret OPENAI_API_KEY
#   agent-vault-set-secret OPENAI_API_KEY --vault default
#   agent-vault-set-secret --help

set -euo pipefail

key=""
host=""
ssh_user=""
container=""
vault=""
proxy_url=""
check=false

config_path="${XDG_CONFIG_HOME:-$HOME/.config}/agent-vault-secret/config"

usage() {
  cat <<EOF
agent-vault-set-secret [CREDENTIAL_NAME] [options]

  CREDENTIAL_NAME     credential name to create or update (prompted if omitted)
  --host <ssh-host>   SSH host running the vault
  --user <ssh-user>   SSH user
  --container <name>  container name
  --vault <name>      vault to write into
  --proxy-url <url>   proxy address, used by the verification step
  -h, --help          show this help
  --check             print the resolved settings and exit

--host, --user, --container, and --vault fall back to the environment, then to
$config_path. See SKILL.md.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --vault) vault="${2:?--vault needs a value}"; shift 2 ;;
    --proxy-url) proxy_url="${2:?--proxy-url needs a value}"; shift 2 ;;
    --host) host="${2:?--host needs a value}"; shift 2 ;;
    --user) ssh_user="${2:?--user needs a value}"; shift 2 ;;
    --container) container="${2:?--container needs a value}"; shift 2 ;;
    --check) check=true; shift ;;
    -h|--help) usage; exit 0 ;;
    -*) printf 'unknown option: %s\n\n' "$1" >&2; usage >&2; exit 2 ;;
    *) key="$1"; shift ;;
  esac
done

# The host, user, container, and vault belong to the consumer, not to this
# skill, so there are no built-in defaults. The config file lives outside the
# skill directory, so reinstalling the skill cannot clobber it.
read_config_value() {
  [ -f "$config_path" ] || return 0
  sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$config_path" | tail -n 1
}

resolve_setting() {
  local value="$3"
  [ -n "$value" ] || value="$(printenv "$2" 2>/dev/null || true)"
  [ -n "$value" ] || value="$(read_config_value "$1")"
  printf '%s' "$value"
}

host="$(resolve_setting host AGENT_VAULT_SECRET_HOST "$host")"
ssh_user="$(resolve_setting ssh_user AGENT_VAULT_SECRET_SSH_USER "$ssh_user")"
container="$(resolve_setting container AGENT_VAULT_SECRET_CONTAINER "$container")"
vault="$(resolve_setting vault AGENT_VAULT_SECRET_VAULT "$vault")"
proxy_url="$(resolve_setting proxy_url AGENT_VAULT_SECRET_PROXY_URL "$proxy_url")"

missing=""
for name in host ssh_user container vault; do
  [ -n "${!name}" ] || missing="${missing}${missing:+, }$name"
done

if [ -n "$missing" ]; then
  {
    printf 'this host is not configured for Agent Vault.\n\n'
    printf 'Add these to %s:\n' "$config_path"
    printf '  host=<SSH host running the vault>\n'
    printf '  ssh_user=<SSH user>\n'
    printf '  container=<container name>\n'
    printf '  vault=<vault name>\n'
    printf '\nMissing: %s\n' "$missing"
    printf 'Or pass them as flags, or set AGENT_VAULT_SECRET_HOST,\n'
    printf 'AGENT_VAULT_SECRET_SSH_USER, AGENT_VAULT_SECRET_CONTAINER,\n'
    printf 'AGENT_VAULT_SECRET_VAULT.\n'
  } >&2
  exit 2
fi

if [ "$check" = true ]; then
  printf 'host=%s\nssh_user=%s\ncontainer=%s\nvault=%s\n' \
    "$host" "$ssh_user" "$container" "$vault"
  if [ -n "$proxy_url" ]; then
    printf 'proxy_url=%s\n' "$proxy_url"
  fi
  exit 0
fi

if [ -z "$key" ]; then
  printf 'Credential name (e.g. OPENAI_API_KEY): ' >&2
  read -r key
fi

# The name is interpolated into a shell command on the remote host, so it must
# be a plain identifier. Reject anything else rather than escaping it.
case "$key" in
  [A-Za-z_]*) ;;
  *) printf 'credential name must start with a letter or underscore\n' >&2; exit 2 ;;
esac
case "$key" in
  *[!A-Za-z0-9_]*) printf 'credential name may only contain letters, digits, and underscores\n' >&2; exit 2 ;;
esac

# The vault, container, user, and host go into the same remote command, so they
# must be plain identifiers or hostnames too.
require_safe_token() {
  local label="$1" value="$2"
  case "$value" in
    [A-Za-z0-9]*) ;;
    *) printf '%s must start with a letter or digit\n' "$label" >&2; exit 2 ;;
  esac
  case "$value" in
    *[!A-Za-z0-9._-]*) printf '%s may only contain letters, digits, dot, dash, and underscore\n' "$label" >&2; exit 2 ;;
  esac
}

require_safe_token "vault" "$vault"
require_safe_token "container" "$container"
require_safe_token "ssh user" "$ssh_user"
require_safe_token "ssh host" "$host"

printf 'Secret value for %s: ' "$key" >&2
read -rsp '' value
printf '\n' >&2

if [ -z "$value" ]; then
  printf 'empty value — nothing written\n' >&2
  exit 2
fi

# `printf` is a shell builtin, so the value never appears in this host's process
# list; it reaches the remote host on stdin.
printf '%s\n' "$value" | ssh \
  -o BatchMode=yes -o IdentitiesOnly=yes -o ConnectTimeout=25 \
  "$ssh_user@$host" \
  "read -r __v && docker exec $container agent-vault vault credential set --vault $vault \"$key=\$__v\""

unset value

printf 'Wrote %s to vault %s on %s.\n' "$key" "$vault" "$host" >&2
