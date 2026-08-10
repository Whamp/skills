# Assets, HTML, and operations

These commands were verified against Sideshow CLI 0.11.1. Run each through `bash -lc` so the hosted workspace environment is loaded.

## Assets

```sh
bash -lc 'npx -y sideshow upload file.pdf --kind file --session SESSION'
bash -lc 'npx -y sideshow upload screenshot.png --kind image --session SESSION'
bash -lc 'npx -y sideshow asset-url screenshot.png'
```

Assets are content-addressed by SHA-256 and deduplicate. `asset-url` computes the future id and URL locally without contacting the server. The per-asset limit is 5 MiB and the workspace budget is 2 GiB. Referenced assets survive across sessions; unreferenced least-recently-used assets are eviction candidates.

## HTML and kits

Fetch the live design contract and visible kit registry after selecting HTML:

```sh
bash -lc 'npx -y sideshow guide'
bash -lc 'npx -y sideshow kits'
bash -lc 'npx -y sideshow publish board.html --kit issues --title "CI status" --session SESSION'
bash -lc 'npx -y sideshow publish deck.html --kit slides --title "Proposal" --session SESSION'
```

The live `guide` is authoritative for HTML fragment structure, theme variables, injected controls, SVG utilities, sizing, CSP/CDN rules, and kit vocabulary. HTML renders in a sandboxed iframe.

Choose the visual direction in this order:

1. Follow the look or design system Will requested.
2. Otherwise inspect and match the subject project's tokens, components, brand assets, and existing styled pages. A proposed product UI should look like that product, even when the current working directory is elsewhere.
3. When neither supplies a design system, use the live guide's theme variables and patterns. Do not copy a standalone full-page template into Sideshow's fragment surface.

Make decisions, risks, tradeoffs, and next actions obvious at a glance. Use sections, cards, tables, diagrams, and side-by-side comparisons instead of long prose. Prevent horizontal overflow at every nesting level; grid and flex children may need `minmax(0, 1fr)` and `min-width: 0`. When explaining existing UI or visual state, show current screenshots as image surfaces and reserve prose for rationale, tradeoffs, and open questions.

Exercise the current rendered layout and any claimed interaction with the applicable browser tool; publication alone proves only server acceptance.

## Discovery

```sh
bash -lc 'npx -y sideshow version'
bash -lc 'npx -y sideshow help'
bash -lc 'npx -y sideshow agent-howto'
bash -lc 'npx -y sideshow guide'
bash -lc 'npx -y sideshow setup'
bash -lc 'npx -y sideshow kits'
bash -lc 'npx -y sideshow test-post'
bash -lc 'npx -y sideshow demo'
bash -lc 'npx -y sideshow serve --port 8228 --open'
bash -lc 'npx -y sideshow mcp'
```

The configured hosted workspace needs no local server or Tailnet forwarding. `serve` creates a separate local workspace. `test-post` is idempotent but mutates the workspace; `demo` deliberately seeds content. `agent-howto` and `setup` are generic integration material, not transport-routing authority for this CLI-first skill. `mcp` starts the stdio server outside this skill's route.

## Experimental trace

Trace is outside Sideshow's product-facing surface taxonomy. Use it only when Will explicitly asks to inspect an agent run timeline:

```sh
bash -lc 'npx -y sideshow trace run.json --title "Agent trace" --session SESSION'
```

### Claude Code trace integration

These commands target Claude Code transcripts and hooks, not Pi sessions:

```sh
bash -lc 'npx -y sideshow trace-sync --session SESSION --transcript session.jsonl --pad 5'
bash -lc 'npx -y sideshow trace-sync --session SESSION --all --reset --quiet'
bash -lc 'npx -y sideshow install-hook --print'
bash -lc 'npx -y sideshow install-hook --shared'
bash -lc 'npx -y sideshow install-hook --user'
```

Default windowed `trace-sync` replaces the window around the session's posts on each run. With `--all`, the first sync replaces and later runs use a per-session cursor to append only the tail. `--reset` forces replacement. `install-hook` idempotently adds a Claude Code Stop hook; the internal `hook` command stays silent and non-blocking.

## Environment

- `SIDESHOW_URL`: workspace base URL; defaults to `http://localhost:8228`.
- `SIDESHOW_TOKEN`: bearer token for a deployed workspace.
- `SIDESHOW_SESSION`: fixed session override; it takes precedence over `--new-session`.
- `SIDESHOW_AGENT`: default agent label.
- `PORT`: local `serve` fallback port.

Keep secrets in the environment. The skill's non-printing assertion requires an explicit `SIDESHOW_URL` and a nonempty token. Treat that configured URL as the trusted origin. `kits` proves the origin is readable, while the first write proves write capability because public-read deployments may expose the kit registry without accepting writes.
