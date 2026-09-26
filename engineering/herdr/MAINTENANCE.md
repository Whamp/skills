# Herdr Skill Maintenance

`Whamp/skills` owns the maintained `herdr` skill. Consumer installations update through the Skills CLI; the Herdr updater and `herdr --skill` remain upstream evidence, not update owners.

## Upstream baseline

- Repository: `https://github.com/herdrdev/herdr`
- Upstream skill: `skills/herdr/SKILL.md`
- Last-reviewed Herdr release: `v0.9.1`
- Release commit: `065ef9d6a531c49fb8bee7e818ef837065b21ee9`
- Last-reviewed skill commit: `956f23ff6b72d16fe66169730b76bf565d12d449`
- Last-reviewed skill blob: `bcb22ba8d7b8259f25fa2bfd76dd5e520fd52fbc`
- Versioned-docs commit: `956f23ff6b72d16fe66169730b76bf565d12d449`
- Installed version at review: `herdr 0.9.1`
- Installed client/server protocol at review: `22`
- Review date: 26 September 2026

The upstream skill, the skill bundled by `herdr --skill` at v0.9.1, and the release-tag blob all matched the recorded blob. The upstream skill changed with the v0.9.1 release itself, so review the next release against this baseline rather than assuming the bundled skill lags the runtime.

## Maintained invariant

Upstream is a capability reference, not the policy source. Preserve the published invocation policy, proactive background-terminal behavior, tab-first sidecar topology, sidecar vocabulary, and progressive-disclosure shape. Import only useful CLI, lifecycle, safety, and capability changes.

## Review triggers

Review upstream when:

- Herdr is upgraded;
- the upstream skill changes;
- native Herdr tool schemas change; or
- a local task exposes stale command or lifecycle guidance.

## Review procedure

1. Capture the installed interface and protocol as durable evidence:

   ```bash
   evidence_dir=/tmp/herdr-skill-review
   rm -rf "$evidence_dir"
   mkdir -p "$evidence_dir"

   herdr --version > "$evidence_dir/version.txt"
   herdr status > "$evidence_dir/status.txt"
   herdr --skill > "$evidence_dir/bundled-SKILL.md"
   git hash-object "$evidence_dir/bundled-SKILL.md" \
     > "$evidence_dir/bundled-skill-blob.txt"
   herdr api schema --json > "$evidence_dir/api-schema.json"
   python3 "$HOME/.agents/skills/herdr/capture-cli-help.py" \
     --output "$evidence_dir/cli-help.json"
   ```

   `capture-cli-help.py` recursively appends `--help` to every discovered command path, including hidden top-level compatibility groups. It exits nonzero and lists failures when any path cannot be captured. This step is complete when `cli-help.json` has an empty `failures` array, every command referenced by the maintained skill appears in its `commands` array, and the client/server versions and protocols are recorded.

2. Fetch release evidence, pinned versioned docs, and the current upstream skill independently:

   ```bash
   evidence_dir=/tmp/herdr-skill-review
   repository=herdrdev/herdr
   release_tag=$(gh api "repos/$repository/releases/latest" --jq .tag_name)
   release_version=${release_tag#v}

   gh api "repos/$repository/releases/tags/$release_tag" \
     > "$evidence_dir/release.json"
   gh api -H 'Accept: application/vnd.github.raw' \
     "repos/$repository/contents/CHANGELOG.md?ref=$release_tag" \
     > "$evidence_dir/CHANGELOG.md"

   tag_type=$(gh api "repos/$repository/git/ref/tags/$release_tag" --jq .object.type)
   tag_sha=$(gh api "repos/$repository/git/ref/tags/$release_tag" --jq .object.sha)
   if [ "$tag_type" = tag ]; then
     release_commit=$(gh api "repos/$repository/git/tags/$tag_sha" --jq .object.sha)
   else
     release_commit=$tag_sha
   fi
   printf '%s\n' "$release_commit" > "$evidence_dir/release-commit.txt"

   docs_path="docs/versions/$release_version/website/src/content/docs/agent-automation.mdx"
   docs_commit=$(gh api \
     "repos/$repository/commits?path=$docs_path&per_page=1" \
     --jq '.[0].sha')
   printf '%s\n' "$docs_commit" > "$evidence_dir/versioned-docs-commit.txt"
   for document in agent-automation cli-reference socket-api agents integrations; do
     gh api -H 'Accept: application/vnd.github.raw' \
       "repos/$repository/contents/docs/versions/$release_version/website/src/content/docs/$document.mdx?ref=$docs_commit" \
       > "$evidence_dir/$document.mdx"
   done

   upstream_commit=$(gh api \
     "repos/$repository/commits?path=skills/herdr/SKILL.md&per_page=1" \
     --jq '.[0].sha')
   printf '%s\n' "$upstream_commit" > "$evidence_dir/upstream-skill-commit.txt"
   gh api -H 'Accept: application/vnd.github.raw' \
     "repos/$repository/contents/skills/herdr/SKILL.md?ref=$upstream_commit" \
     > "$evidence_dir/upstream-SKILL.md"
   gh api \
     "repos/$repository/contents/skills/herdr/SKILL.md?ref=$upstream_commit" \
     --jq .sha > "$evidence_dir/upstream-skill-blob.txt"
   gh api \
     "repos/$repository/contents/skills/herdr/SKILL.md?ref=$release_tag" \
     --jq .sha > "$evidence_dir/release-skill-blob.txt"
   ```

   Herdr publishes the immutable release snapshot on the default branch after tagging, so pin it by its latest path commit instead of expecting it inside the release tag. This step is complete when every named artifact exists, every fetched file is nonempty, and the release, docs, and skill commits are recorded beside their content.

3. Compare three independent surfaces:

   - bundled `herdr --skill` against the release and current upstream skill blobs;
   - the current upstream skill against the previously recorded commit and canonical `SKILL.md`;
   - release notes, changelog, pinned docs, installed help, and API schema against the previously reviewed release and canonical CLI guidance.

   Confirm changed commands and semantics with the installed binary before updating canonical prose. Record protocol changes because mixed client/server versions may be incompatible.

4. Give every skill-relevant release item exactly one written disposition:

   - **accepted** into one named canonical file;
   - **already covered**, with the existing canonical source named; or
   - **rejected**, with a reason tied to the maintained invariant.

   Keep one release item per bullet. Do not advance the baseline until every relevant item has exactly one disposition. An unchanged upstream skill blob is not evidence that runtime capabilities are unchanged.

5. Validate every command family referenced by the canonical skill. Confirm the public default remains model-invoked in Pi and Codex.

6. Update the commit, blob, release, protocol, review date, and last-review disposition below. Run the `Whamp/skills` repository validation, merge the canonical change, and update the consumer with `npx skills update herdr --global --yes`. Confirm the installed files match the merged source, the installer receipt names `Whamp/skills`, and consumer ownership and invocation inventories remain synchronized.

The review is complete when the baseline matches the captured evidence, every accepted behavior is validated against the installed interface, every rejected behavior has a recorded reason, the canonical source is merged with passing CI, and each updated consumer reports the skill current.

## Last review disposition: v0.9.1

### Accepted

- `herdr machine` profiles and `--machine <label-or-id>` CLI forwarding: selector discipline, per-server ID scoping, no local fallback, connection failure does not prove a mutation was not applied → `CLI-REFERENCE.md`.
- Explicit group intent for closing a primary workspace with worktree workspaces (`workspace close --group`, `workspace_group_close_required`) → `CLI-REFERENCE.md`.
- `--trust-repository` per-request Git trust rule → `CLI-REFERENCE.md`.
- `agent start` blocked-startup `agent_not_ready` with retained name → `CLI-REFERENCE.md`.
- `agent prompt` ordered submission, success-after-write semantics, pre-send `agent_blocked` rejection, observed-activity gate, caller-timeout-includes-submission → `CLI-REFERENCE.md`.
- `herdr status` feature gating under mixed client/server versions → `CLI-REFERENCE.md`.
- Named-test-session isolation and the no-host-kill rule → `CLI-REFERENCE.md`.
- Outside-session control guard, adapted to allow explicit user requests → `SKILL.md`.
- Per-server ID scoping and `--machine` consistency note → `SKILL.md`.
- Baseline advanced to v0.9.1: bundled, release, and current upstream skill blobs identical → `MAINTENANCE.md`.

### Already covered

- Alternate-screen history as application-owned collection → existing auto-collection passage in `CLI-REFERENCE.md`.
- Per-client done-badge divergence → existing `idle`/`done` seen-state text in `CLI-REFERENCE.md`.
- Do not blindly resubmit after timeout or stall → existing "Prompt consumption remains unproven" in `CLI-REFERENCE.md`.
- `pane split` caller default (#4123) → caller-resolution rule in `CLI-REFERENCE.md`; native `pane_split` already defaults to the caller's pane.
- Recent reads include unscrolled output (#3444) → existing read-source guidance in `CLI-REFERENCE.md`.
- Qwen, Muse, and Letta detection → installed-help discovery rule in `CLI-REFERENCE.md`.
- Lifecycle subscriptions start with live events (#1270) → API-only ordering feature outside the sidecar workflow.
- Foreground cwd follows the process-group leader (#3270) → improves existing cwd-preservation guidance; no text change required.

### Rejected

- UI, rendering, theme, IME, mouse, clipboard, and image changes → no command or lifecycle effect.
- Windows input, SSH, and installer fixes → no local Linux command or lifecycle effect.
- Removed `--no-session` mode → never documented here; launches already attach to a background server.
- 30-second idle terminal-observer disconnect (#3612) → bounded CLI waits unaffected; revisit only if a long-lived observer pattern appears.
- Upstream explicit-only invocation posture (reaffirmed) → conflicts with the maintained proactive sidecar policy; consumers are model-invoked on all hosts.
- Upstream monolithic skill structure (reaffirmed) → conflicts with the maintained progressive-disclosure shape.
