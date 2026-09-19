---
name: agent-vault-secret
description: Add, update, or rotate a secret in Agent Vault with the human supplying the value, so it never enters an agent's context. Use when asked to add a credential to Agent Vault, give an agent access to a new API, or rotate an exposed agent token.
---

# Add a secret to Agent Vault

Agent Vault sits between an agent and target services, attaching real credentials
to outbound requests, so the agent calls an API through the proxy without ever
holding the key.

The value must never enter your context. You supply the credential *name*; the
human supplies the *value*. Never ask for, echo, or accept the secret in chat,
and never read it back with `credential get`.

## 1. Configure the instance

Once per host. The host, SSH user, container, and vault belong to the consumer,
so the scripts ship with no defaults. Write them to
`${XDG_CONFIG_HOME:-$HOME/.config}/agent-vault-secret/config`:

```ini
host=my-vault-host
ssh_user=root
container=Agent-Vault
vault=default
```

[`config.example`](config.example) is the same file. A `--host`, `--user`,
`--container`, or `--vault` flag overrides it, and so does the matching
`AGENT_VAULT_SECRET_HOST`, `AGENT_VAULT_SECRET_SSH_USER`,
`AGENT_VAULT_SECRET_CONTAINER`, or `AGENT_VAULT_SECRET_VAULT` variable.

The steps below write `$host`, `$container`, and `$vault` for those values.

Complete when `agent-vault-set-secret --check` prints the four resolved values.

## 2. Agree the credential name

Ask the human what the credential should be called — conventionally the
environment variable name the API uses, e.g. `OPENAI_API_KEY`,
`TYPESAFE_API_KEY`. Uppercase with underscores.

Complete when the human has confirmed one name.

## 3. Ask how the human will supply the value

Two intake paths. Ask which one, unless the situation already settles it — then
say which you are using and why.

| Path | Use when | What happens |
| --- | --- | --- |
| **Window** | You run on a host with a graphical session the human is sitting at. | A native window opens on that screen. They paste the value there. |
| **Terminal** | Anywhere else: a laptop at a TTY, a remote host, an SSH session, no display. | You print a command. They run it in their own terminal and type the value at a hidden prompt. |

The window draws on the screen of the machine running *you*, not the machine the
human is looking at. Over a remote session it opens on the wrong screen, so use
the terminal path. `[ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]` on your host is a
quick check for whether a window is even possible.

**Window** (you run this; it blocks until they finish):

```bash
agent-vault-add-secret --key OPENAI_API_KEY
```

**Terminal** (the human runs this, not you):

```bash
agent-vault-set-secret OPENAI_API_KEY
```

**Never run the terminal path yourself.** The value would land in a terminal you
can read, and from there in your context — the whole thing this workflow exists
to prevent. Print the command and let the human run it.

The window path also takes `--dry-run`, which exercises the UI without writing.

Complete when the human confirms they have submitted the value.

## 4. Confirm the credential landed

List keys only — never read a value back:

```bash
ssh -o IdentitiesOnly=yes "$host" \
  "docker exec $container agent-vault vault credential list"
```

Complete when the new key appears in the list.

## 5. Define the service

A credential is inert until a service tells the proxy which host it applies to
and how to attach it. Find the API's host and auth scheme from its own docs — do
not guess.

```bash
ssh -o IdentitiesOnly=yes "$host" \
  "docker exec $container agent-vault vault service add \
     --name typesafe-api \
     --host 'api.typesafe.ai/v1/*' \
     --auth-type bearer \
     --token-key TYPESAFE_API_KEY"
```

`--host` takes a bare hostname, a one-level wildcard (`*.example.com`), or a
path-scoped form (`api.example.com/v1/*`). Prefer the narrowest path scope that
covers the endpoints in use. Auth types are `bearer`, `basic`, `api-key`,
`custom`, and `passthrough`; each has matching `--*-key` flags for the credential
name.

Complete when `vault service list` shows the service enabled against the new key.

## 6. Verify it actually works

Listing keys proves nothing about the value. Make a real call through the proxy,
using an agent token that holds the `proxy` role on the vault.

```bash
ssh -o IdentitiesOnly=yes "$host" \
  "docker exec $container agent-vault ca fetch" > /tmp/av-ca.pem

curl -s --proxy "$PROXY_URL" --cacert /tmp/av-ca.pem \
  --proxy-header "Proxy-Authorization: Bearer $TOKEN" \
  -X POST "https://api.typesafe.ai/v1/systemone" \
  -H "Content-Type: application/json" \
  -d '{"state":"test","model":"jev-latest","questions":{"q":{"type":"noul","instructions":"Is this a test?"}}}'
```

`$PROXY_URL` is the proxy's address, for example `http://10.0.0.5:14322`. `$TOKEN`
comes from wherever the consumer keeps secrets; retrieve it without printing it.

A `401` means the credential value is wrong. A `403` means the service is
disabled or the agent lacks proxy access. A `200` means the whole path works.

Delete `/tmp/av-ca.pem` afterwards. Complete when the call returns `200`, or when
a non-`200` has a stated cause.

## Rotating an exposed agent token

Two different things get called "a token" here, and only one of them is this.

The **agent token** is the string an agent presents to Agent Vault so the proxy
knows which agent is calling. It is a password for the proxy and nothing more. It
is not the upstream API key, and Agent Vault has no way to mint or change a key
at a provider — only that provider can. To replace an upstream key, get a new one
from the provider and store it as a credential (step 2).

`agent rotate` rotates the agent token and invalidates the old one immediately —
use it when a token has leaked into a log, a transcript, or a shared context. It
needs the owner session, which is already logged in on the vault host, so no
separate login is required.

```bash
ssh -o IdentitiesOnly=yes "$host" \
  "docker exec $container agent-vault agent rotate my-agent"
```

Add `--token-only` to print just the raw token for scripting. Rotating a token
does not change credential values, services, or roles — only the string that
agent authenticates with.

Complete when the new token is stored wherever the consumer keeps secrets and a
proxied request with it returns `200`.

## Notes

- `credential set` upserts, so re-running with the same key rotates the value.
- The value is passed as a command argument on the vault host, so it is briefly
  visible in that host's process list. That is why the vault host should be
  single-user.
- Shared agent tokens are readable by anything that can reach the secret store.
  Rotate with `agent rotate` if one is exposed.
- `scripts/install.sh` puts both commands on this host's PATH, or on another host
  with `--host <ssh-host>`. Re-run it after moving the skill.
- Maintenance and the interfaces this depends on: [`MAINTENANCE.md`](MAINTENANCE.md).
