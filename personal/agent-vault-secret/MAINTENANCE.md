# Agent Vault Secret Skill Maintenance

`Whamp/skills` owns this skill. Consumers install it with the Skills CLI and
update it the same way.

## Consumer configuration

The skill ships with no host, user, container, or vault values, because those
belong to the consumer rather than to the skill. Each consumer supplies them in
`${XDG_CONFIG_HOME:-$HOME/.config}/agent-vault-secret/config`, which sits outside
the skill directory so reinstalling the skill cannot clobber it.

Keep consumer values out of this repository. A concrete host, SSH user, container
name, vault name, proxy address, or secret-store item title is a consumer fact,
not a skill fact.

## Interfaces this depends on

- `agent-vault` — `vault credential set`, `vault service add`, `agent rotate`,
  `ca fetch`. Last reviewed against 0.39.3.
- `glimpseui` — the window path. The script resolves it from
  `~/.pi/agent/npm/node_modules/glimpseui/src/glimpse.mjs` and two system
  locations.
- Hyprland — the window path floats its own window. Chromium sets the window
  class and title only after mapping, so a Hyprland window rule has nothing to
  match on; the script finds the window and floats it. Off Hyprland the window
  tiles.

## Review triggers

Review when:

- `agent-vault` is upgraded past the reviewed version;
- `glimpseui` changes its `open()` or message API;
- a consumer reports a script failing against a newer interface.

## Last review: agent-vault 0.39.3, 18 September 2026

Verified against the installed CLI:

- `vault credential set` upserts and takes the value as an argument. It has no
  stdin mode, which is why both paths pipe the value into a `read` on the vault
  host rather than passing it on this host's command line.
- `agent rename` leaves tokens valid; `agent rotate` invalidates the old one.
  They are separate commands, so a renamed agent keeps working.
- `agent rotate` needs the owner session, which is already present on the vault
  host.
- `ca fetch` writes the proxy root CA used by the verification step.
