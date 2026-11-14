---
name: agent-vault-secret
description: Store a secret in Agent Vault while the human supplies the value, so it never enters your context. Use when the human wants to give you a password, API key, or token; when a task needs a credential you do not have; or when an exposed agent token needs rotating.
---

# Add a secret to Agent Vault

Agent Vault sits between an agent and target services, attaching real credentials
to outbound requests, so the agent calls an API through the proxy without ever
holding the key.

The value must never enter your context. You supply the credential *name*; the
human supplies the *value* through one of the intake paths in step 3. Ask for
values only through those paths, and read back only credential names.

If the human pastes a secret into chat anyway, it is already exposed. Say so,
store it through an intake path anyway, and recommend that they rotate it at the
provider.

## 1. Configure the instance

Once per host. The host, SSH user, container, and vault belong to the consumer,
so the scripts ship with no defaults. Write them to
`${XDG_CONFIG_HOME:-$HOME/.config}/agent-vault-secret/config`:

```ini
host=my-vault-host
ssh_user=root
container=Agent-Vault
vault=default
proxy_url=http://10.0.0.5:14322
```

[`config.example`](config.example) is the same file. A `--host`, `--user`,
`--container`, `--vault`, or `--proxy-url` flag overrides it, and so does the
matching `AGENT_VAULT_SECRET_HOST`, `AGENT_VAULT_SECRET_SSH_USER`,
`AGENT_VAULT_SECRET_CONTAINER`, `AGENT_VAULT_SECRET_VAULT`, or
`AGENT_VAULT_SECRET_PROXY_URL` variable.

The first four are required. `proxy_url` is optional and only used by step 6.

The steps below write `$host`, `$container`, `$vault`, and `$proxy_url` for those
values.

If the commands are missing, run [`scripts/install.sh`](scripts/install.sh). If
this host cannot reach the vault host over SSH, run every command in this skill
on a host that can, through SSH. A redirected file still travels on standard
input: `ssh that-host agent-vault-set-secret NAME < "$secret_file"`.

Complete when `agent-vault-set-secret --check` prints the four resolved values.

## 2. Agree the credential names

Propose a name for each credential and confirm it with the human. Use the
environment variable names expected by the API when they are known, such as
`OPENAI_API_KEY`, `CREDITSIGHTS_USERNAME`, or `CREDITSIGHTS_PASSWORD`.
Use uppercase with underscores.

Complete when the human has confirmed every name.

## 3. Collect the value

Use the first path that fits. Tell the human which path you chose and what they
will see.

| Path | Use when | Who runs the command |
| --- | --- | --- |
| **Secret prompt** | Your harness has a tool that collects a secret into a file you never read, such as T3 Code's `request_secret` with `delivery: "file"`. | You |
| **Approval link** | You can run commands, and the human has a browser that can reach the vault. Works from a phone. | You |
| **Window** | You run on the machine where the human sits at a graphical session. | You |
| **Terminal** | The human prefers it, or none of the paths above fits. | The human |

If you cannot run commands at all, as in a chat-only app, hand the task to an
agent that can, or give the human the terminal command below.

**Secret prompt.** Request one value per credential name through the harness
tool. Redirect the delivered file into the terminal command, so the value goes
from the file to the vault over SSH, then delete the file:

```bash
agent-vault-set-secret OPENAI_API_KEY < "$secret_file"
rm -f "$secret_file"
```

Keep `$secret_file` out of every other command, including `cat`.

**Approval link.** Create a proposal with one empty slot per credential. Add a
description so the human knows which value to paste:

```bash
agent-vault-request-secret \
  --key 'CREDITSIGHTS_USERNAME=CreditSights login email' \
  --key 'CREDITSIGHTS_PASSWORD=CreditSights password' \
  --message 'Store the CreditSights login for the research agent'
```

Give the human the printed approval link. They open it, sign in to Agent Vault,
enter each value, and approve. Then wait for the result:

```bash
agent-vault-request-secret --wait 14
```

It exits `0` when the proposal is applied, `1` when it is rejected or expired,
and `3` when it is still pending after `--timeout` seconds (default 1800).
Approving a slot for a name that already exists replaces the stored value; that
is how this path rotates a credential. To request a service and its credentials
in one approval, write the proposal JSON described in step 5 and pass it with
`--file`.

**Window.** A native window opens on the screen of the machine running *you*.
Over a remote session it opens on the wrong screen.
`[ -n "${WAYLAND_DISPLAY:-}${DISPLAY:-}" ]` shows whether a window is possible.
Repeat `--key` for several values; one window walks through them in order:

```bash
agent-vault-add-secret --key CREDITSIGHTS_USERNAME --key CREDITSIGHTS_PASSWORD
```

`--dry-run` exercises the window without connecting to the vault.

**Terminal.** Print this command for the human to run in their own terminal. It
asks for each value at a hidden prompt:

```bash
agent-vault-set-secret CREDITSIGHTS_USERNAME CREDITSIGHTS_PASSWORD
```

Run it yourself only with standard input redirected from a secret file, as in
the secret prompt path. Run interactively, the value would appear in a terminal
you read.

Every path checks SSH access, the container, and the vault before it asks for a
value.

Complete when the command reports success for every name, the proposal is
applied, or the human confirms they submitted every value.

## 4. Confirm the credential landed

List keys only — never read a value back:

```bash
ssh -o IdentitiesOnly=yes "$host" \
  "docker exec $container agent-vault vault credential list"
```

Complete when every new key appears in the list.

If either intake command reports an Agent Vault preflight failure, test the SSH
route without entering a secret:

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes "$ssh_user@$host" true
```

When that route needs a non-default key, add a matching `Host` entry to
`~/.ssh/config` with `IdentityFile` and `IdentitiesOnly yes`, then rerun the
probe. Also check that the configured container is running and the vault exists.

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

To have the human approve the service and its credential slots together, put
both in one proposal file and pass it to `agent-vault-request-secret --file`:

```json
{
  "services": [{
    "name": "typesafe-api",
    "host": "api.typesafe.ai/v1/*",
    "auth": {"type": "bearer", "token": "TYPESAFE_API_KEY"}
  }],
  "credentials": [{
    "action": "set",
    "key": "TYPESAFE_API_KEY",
    "description": "Typesafe API key"
  }],
  "message": "Typesafe API access for the extraction agent"
}
```

When the credential is already stored, leave it out of `credentials`: a slot asks
for the value again and replaces the stored one on approval.

Stored login credentials do not create a working service by themselves. A JSON
login exchange, OTP, SSO, or refresh-token workflow needs a compatible broker or
adapter. Do not map such a service to Basic authentication unless its own docs
say it accepts Basic authentication.

Complete when `vault service list` shows the service enabled against the new key,
or when an unsupported login exchange is named as the blocker.

## 6. Verify it actually works

Listing keys proves nothing about the value. Make a real call through the proxy,
using an agent token that holds the `proxy` role on the vault.

```bash
ssh -o IdentitiesOnly=yes "$host" \
  "docker exec $container agent-vault ca fetch" > /tmp/av-ca.pem

curl -s --proxy "$proxy_url" --cacert /tmp/av-ca.pem \
  --proxy-header "Proxy-Authorization: Bearer $TOKEN" \
  -X POST "https://api.typesafe.ai/v1/systemone" \
  -H "Content-Type: application/json" \
  -d '{"state":"test","model":"jev-latest","questions":{"q":{"type":"noul","instructions":"Is this a test?"}}}'
```

`$TOKEN` comes from wherever the consumer keeps secrets; retrieve it without
printing it.

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
- `scripts/install.sh` puts the three commands on this host's PATH, or on another
  host with `--host <ssh-host>`. Re-run it after moving the skill.
- The approval link carries a read-only token. Submitting values on the page
  requires an Agent Vault login, so sharing the link with the human is safe.
- Maintenance and the interfaces this depends on: [`MAINTENANCE.md`](MAINTENANCE.md).
