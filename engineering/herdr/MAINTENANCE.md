# Herdr Skill Maintenance

`Whamp/skills` owns the maintained `herdr` skill. Consumer installations update through the Skills CLI; the Herdr updater and `herdr --skill` remain upstream evidence, not update owners.

## Upstream baseline

- Repository: `https://github.com/herdrdev/herdr`
- Upstream skill: `skills/herdr/SKILL.md`
- Last-reviewed Herdr release: `v0.8.0`
- Release commit: `346411fa21afd297f5ed3b3fa56f9e3fbf7654b7`
- Last-reviewed skill commit: `f6060cf682f69ef8302c25e8924c0b27aef7ae16`
- Last-reviewed skill blob: `fafea549c0c46b87bac6c7ae4ad22ef7ac635a5e`
- Versioned-docs commit: `3642e67c7b9c1d8608d72f288e80b410c602e55c`
- Installed version at review: `herdr 0.8.0`
- Installed client/server protocol at review: `19`
- Review date: 3 August 2026

The upstream skill, the skill bundled by `herdr --skill`, and the recorded blob matched at review. The v0.8.0 runtime changed after the upstream skill's last edit, so an unchanged skill blob does not prove that the maintained guidance is current.

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

## Last review disposition: v0.8.0

### Accepted

- Automatic alternate-screen history collection and its passive-read limits → `CLI-REFERENCE.md`.
- API `truncated` metadata and the CLI text-only boundary → `CLI-REFERENCE.md`.
- Lifecycle-based prompt waits and their turn-tracking limit → `CLI-REFERENCE.md`.
- Five-second stalled-prompt detection and timeout precedence → `CLI-REFERENCE.md`.
- `idle` and `done` seen-state semantics → `CLI-REFERENCE.md`.
- Herdr's internal text-to-Enter prompt delay → `CLI-REFERENCE.md`.
- Response capture as part of coding-agent completion → `SKILL.md`.
- Structured `server_not_running` errors → `CLI-REFERENCE.md`.
- Ephemeral agent names → `CLI-REFERENCE.md`.
- Moved-pane ID and inherited-context alias semantics → `CLI-REFERENCE.md`.
- Bounded retirement and worktree-group close confirmation → `CLI-REFERENCE.md`.
- Last-tab workspace collapse → `CLI-REFERENCE.md`.
- `herdr --skill` as installed-version provenance → `MAINTENANCE.md`.
- Canonical `herdrdev/herdr` repository ownership → `MAINTENANCE.md`.
- Pinned versioned release documentation → `MAINTENANCE.md`.
- Client/server protocol capture → `MAINTENANCE.md`.

### Already covered

- Process-owned agent lifecycle → settle and ledger rules in `SKILL.md`.
- Headless agent-session restoration → persistent-sidecar policy in `SKILL.md`.
- Background workspace-close focus preservation → focus and ledger rules in `SKILL.md`.
- Grok and Antigravity integration kinds → installed-help discovery rule in `CLI-REFERENCE.md`.
- Hidden worktree compatibility `--json` flag → flag-free worktree commands in `CLI-REFERENCE.md`.

### Rejected

- `workspace.move_block` and `workspace.reordered` → API-only ordering features outside the sidecar workflow.
- UI, rendering, and theme changes → no command or lifecycle effect.
- IME and ConPTY changes → no local Linux command or lifecycle effect.
- Windows input and process-survival fixes → existing local commands require no syntax change.
- License change → no operational effect.
- Upstream explicit-only invocation posture → conflicts with the maintained proactive sidecar policy.
- Upstream monolithic skill structure → conflicts with the maintained progressive-disclosure shape.
