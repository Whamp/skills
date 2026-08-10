---
name: sideshow
description: Sideshow hosted review. Use when the user mentions Sideshow, requests a hosted visual review or feedback loop, or when a plan, comparison, diagram, diff, code, structured data, terminal output, screenshot, or interactive explainer would be easier to evaluate visually than in chat.
compatibility: Requires Node.js 22.18+, npx, and a configured SIDESHOW_URL/SIDESHOW_TOKEN workspace.
---

# Sideshow

Sideshow is a hosted, two-way review surface. Work **native first**: use Markdown, Mermaid, diff, code, terminal, JSON, or image; use HTML only for custom layout or interaction.

## 1. Verify the hosted route

Before this Pi conversation's first Sideshow post, run:

```sh
bash -lc 'test -n "$SIDESHOW_URL" && test -n "$SIDESHOW_TOKEN" && test -z "${SIDESHOW_SESSION:-}"'
bash -lc 'npx -y sideshow version'
bash -lc 'npx -y sideshow kits >/dev/null'
```

The assertions require an explicit workspace without printing the token and keep task-session selection explicit. Treat the configured `SIDESHOW_URL` as the trusted origin. `kits` proves that origin is reachable and its registry is readable; the first write proves write capability. This skill owns the CLI-first route. The references were verified against CLI 0.11.1; if `version` differs, consult `sideshow help` and the selected command's help before relying on versioned syntax.

Completion criterion: a hosted origin and token are configured, the CLI version is known, and `kits` succeeds without exposing the token.

## 2. Render native first

| Content | Surface |
| --- | --- |
| Plan, report, comparison, rationale, or table | `markdown` |
| Flow, architecture, state, sequence, or relationships | `mermaid` |
| Patch or code review | `diff` |
| Focused source file or excerpt | `code` |
| Commands, tests, or logs | `terminal` |
| API response, config, or structured test data | `json` |
| Screenshot or generated visual | `image` |
| Bespoke visualization, UI sketch, or interaction | `html` |

Compose related surfaces into one review unit; split independent concepts into separate posts. Prefer vertical Mermaid layouts for card readability.

Load only the reference for the branch being executed:

- Read [`references/PUBLISHING.md`](references/PUBLISHING.md) before publishing, composing surfaces, or selecting a session.
- Read [`references/REVISION-AND-FEEDBACK.md`](references/REVISION-AND-FEEDBACK.md) before any post mutation, feedback drain, reply, or write-failure recovery.
- Read [`references/OPERATIONS.md`](references/OPERATIONS.md) before using assets, HTML, kits, local serving, discovery, or trace integration.

For HTML, fetch the live `guide` after selecting the HTML branch and exercise the rendered layout or interaction with the applicable browser tool before claiming it works.

Completion criterion: every concept has the smallest fitting surface, HTML has a native-surface exception and browser evidence, and only the references required by the chosen branches were loaded.

## 3. Publish and pin identity

Write transient source under `/tmp`; keep it in the repository only when it is a project artifact. Use one named Sideshow session per Pi conversation. Create it on the conversation's first post, then retain the returned `sessionId`, post `id`, surface ids, and `url`. Represent distinct tasks or concepts as posts in that session.

Pass that session id on later publishes and `surface add` commands. Existing-post mutations and replies use the retained post id instead; after handoff, compaction, or recovery, run `show` and verify that post's `sessionId` before changing it.

Inspect `userFeedback` and refreshed identities after every mutating response: publish, update, `surface add/edit/move/remove`, and comment. Add one surface per `surface add` invocation so no intermediate response—and therefore no feedback—is hidden.

Treat a transport failure after a write as ambiguous. Recover with `sessions`, scoped `list`, and `show`; retry only the mutation proven missing.

Completion criterion: the post is in the conversation's session, every mutation response was inspected, all returned identities remain available, and ambiguous writes were recovered before retry.

## 4. Close the loop

At revision checkpoints and before the final chat response, run a short foreground drain:

```sh
bash -lc 'npx -y sideshow wait --session SESSION_ID --timeout 1'
```

A timeout means no current feedback, not approval. Continue and provide the URL unless Will explicitly requested an active review or the next step requires his decision; only then use a bounded longer foreground wait.

For each delivered comment:

- Reply with `comment` when no content change is required.
- For substantive feedback, map its post, surface, version, and anchor; revise that target; inspect the mutation response or `show` output to verify the new version; then drain again.

The shared server cursor normally delivers each comment once across writes, waits, watches, and MCP. Do not expect a second wait to replay a drained comment; explicit `--after` changes that behavior.

Completion criterion: every delivered comment is classified and handled, each requested content change is verified on its anchored target, the final drain has been inspected, and the chat response includes the current review URL plus what to inspect first.
