# Publishing and sessions

These commands were verified against Sideshow CLI 0.11.1. Run each through `bash -lc` so Will's hosted workspace environment is loaded. Parse every write result for `userFeedback`, `sessionId`, post `id`, surface ids, version, and `url`.

## Single-surface posts

```sh
bash -lc 'npx -y sideshow markdown plan.md --title "Migration plan" --session SESSION'
bash -lc 'npx -y sideshow mermaid flow.mmd --title "Request flow" --session SESSION'
bash -lc 'npx -y sideshow diff change.patch --layout split --title "Retry change" --session SESSION'
bash -lc 'npx -y sideshow code app.ts --line-start 80 --filename src/app.ts --language typescript --title "Entry point" --session SESSION'
bash -lc 'npx -y sideshow terminal test.log --term-title "Test run" --cols 100 --title "Verification" --session SESSION'
bash -lc 'npx -y sideshow json response.json --title "API response" --session SESSION'
bash -lc 'npx -y sideshow image screenshot.png --caption "Settings after save" --title "Result" --session SESSION'
bash -lc 'npx -y sideshow publish sketch.html --title "Cache layout" --kit issues --session SESSION'
```

Most textual commands accept `-` for stdin. `code` infers common languages and a display filename from the path. `terminal` renders ANSI SGR styling, not cursor-addressed TUIs. `diff` accepts unified/git patches and `unified` or `split` layout. `json` validates before publishing.

## Composite posts

`publish` sends one post write containing HTML first and native surfaces in flag order. Surface flags are repeatable:

```sh
bash -lc 'npx -y sideshow publish sketch.html \
  --md rationale.md \
  --mermaid flow.mmd \
  --diff change.patch --layout split \
  --terminal tests.log \
  --json result.json \
  --code app.ts \
  --image screenshot.png \
  --title "Retry design" --session SESSION'
```

For a native-only composite, publish the first surface, retain the post id, then add and inspect one surface per invocation:

```sh
bash -lc 'npx -y sideshow markdown rationale.md --title "Retry design" --session SESSION'
bash -lc 'npx -y sideshow surface add POST_ID --mermaid flow.mmd --session SESSION'
bash -lc 'npx -y sideshow surface add POST_ID --diff change.patch --layout split --session SESSION'
```

One-add-per-invocation is load-bearing in 0.11.1: repeated flags cause separate writes but the CLI prints only the final response, which can hide feedback returned by an earlier write. Default append preserves invocation order. With `--after`, advance the anchor to the newly returned surface id before the next addition; repeatedly using one anchor reverses the inserted order. `--before` and `--after` accept a surface id or zero-based index.

## Sessions and identity

Resolution order is `--session`, `SIDESHOW_SESSION`, then local state keyed by agent process and working directory. After the first write, pin its returned session id explicitly.

Create the conversation's session on its first post:

```sh
bash -lc 'npx -y sideshow markdown /tmp/plan.md --title "Migration plan" --new-session --session-title "Auth migration"'
```

- `--session-title` applies only while creating a session.
- `--new-session` bypasses auto-detected local state only. An explicit `--session` or `SIDESHOW_SESSION` still wins.
- `--agent` or `SIDESHOW_AGENT` sets the agent label; prefer the configured default over a copied literal.
- One Pi conversation has one Sideshow session; represent distinct tasks or concepts as posts.

Recover and inspect identity with scoped reads:

```sh
bash -lc 'npx -y sideshow sessions'
bash -lc 'npx -y sideshow list --session SESSION'
bash -lc 'npx -y sideshow show POST_ID'
```

`list --all` can be large. `show` returns the post's session, surfaces, stable ids, current version, and history. Existing-post commands are globally addressed by post id and do not all accept a session guard; verify `show` after handoff, compaction, or recovery.
