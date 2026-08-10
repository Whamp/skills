---
name: codegraph
description: "CodeGraph scout before broad grep/read. Use for repo explanation, navigation, diagnosis, runtime/reconnect flow, contract/RPC/schema tracing, refactor/cycle seams, dead-code cleanup, test targeting, and code review."
compatibility: "Requires the `codegraph` CLI (`npm install -g @optave/codegraph`) and, for MCP use, the Pi MCP adapter with a `codegraph` server entry."
---

# CodeGraph

CodeGraph is a scout: it indexes a structural map, narrows the search, and explains relationships. It produces **suspects**, not proof. It does **not** validate behavior. `codegraph build .` means “the graph rebuilt,” not “the code passed.” `codegraph check` and `diff-impact` are structural checks, not substitutes for tests, typecheck, lint, or runtime verification.

Scout before reading broadly: find exact files/symbols, trace relationships, then read the narrowed source. For absence claims, scout first, then corroborate with exact search, source reads, and the project’s package/export boundaries.

Report in three ledgers: CodeGraph evidence, source-read interpretation, and proof commands/manual checks. Do not merge them.

Before editing, run a **seam checkpoint**: name the existing behavioral seam you intend to preserve or extend, the invariant that must stay true, and the smallest scoped change that exercises that seam. CodeGraph can identify structure and blast radius; it cannot decide the behavioral contract for you.

## Blind spots

CodeGraph sees static structure, not every live dependency. Watch for:

- interface/property contracts where implementations and callers share shape rather than a symbol edge;
- schemas and generated/inferred protocol types whose value/type flow is indirect;
- computed keys, indexed dispatch, string-named RPC methods, reflection, config, or external clients;
- package subpath imports, barrel/re-export wrappers, path aliases, and cross-workspace consumers that may not resolve to a symbol edge;
- test-only consumers and wrapper files that only re-export a symbol without using it;
- local closure symbols, `Effect.fn` locals, object-literal handlers, and service methods implemented as properties; `where` may miss them even when `brief` names the containing file;
- runtime-only behavior: validation/decoding, auth, reconnect timing, cache warmup, environment/process effects, backwards compatibility;
- public protocol shape, event/message ordering, lifecycle/timer behavior, persistence ordering, dialect/config scoping, and test identity. These are often owned by conventions or tests rather than static symbol edges.

When one is in play, say so. Use CodeGraph to narrow the target, then use exact targeted search and source reads for the blind spot. Keep generated/schema-heavy results as a hint, not the report backbone: generated protocol files often prove a method/schema exists but not which app path handles it.

## CLI guardrails

The CLI is the source of truth. Before using a flag not shown here, run `codegraph help <command>`.

Known command shapes:

- Directory scoping for `structure` is positional: `codegraph structure apps/server/src --depth 2 -T`; do **not** use `--directory`.
- `cycles` has no `--limit`; cap display externally (`| head`) or use `--json` and post-process.
- `cycles --json` may order cycles differently from text output. Select a cycle by its file set or focus match, not by “Cycle N” alone.
- `cycles --functions` is separate from file-level cycles; run it when the report might imply a symbol/function cycle, and say explicitly when only a file-level cycle was found.
- `deps --json` returns `{ file, results: [{ file, imports, importedBy }] }`; read `results[0]`, not top-level `imports`.
- `deps --json` proves file import edges and `typeOnly`; it usually does not name the imported symbols or runtime calls. Use source reads or targeted exact search for import specifiers, call sites, and responsibility claims.
- `path` resolves symbols, not file paths. For file-to-file cycle edges, use `cycles` plus `deps --json`; do not waste time trying `codegraph path fileA fileB`.
- `fn-impact --file`/`-f` can be fragile across CLI versions. If it errors, rerun unscoped, then disambiguate by the reported definition path.
- `roles` is not path-positional; scope with supported flags such as `--file` or post-filter JSON by `.file`.
- `exports --unused --json` returns `results` plus `reexportedSymbols`; inspect both, or you will miss re-exported public-surface suspects.
- “No uses found” can mean “no visible static edge,” not “unused”; check the blind spots before treating it as absence evidence.
- `build`, `stats`, `map`, `structure`, `triage`, `deps`, `cycles`, and `complexity` are structural scouting only, not validation.

## Scout loop

1. Index and inspect graph health.

   ```bash
   codegraph build .
   codegraph stats -T
   ```

   `build` is incremental by default. It records structure for later queries; it is not a lint/test/typecheck gate. Completion criterion: the graph exists, `stats` shows language/quality/cycle/hotspot data, and you know whether tests are excluded (`-T`) or included. Do not report this step as validation.

2. Orient before choosing files.

   ```bash
   codegraph map -T
   codegraph structure --depth 2 -T
   codegraph triage -T --limit 20
   ```

   To narrow a large repo, pass the directory positionally:

   ```bash
   codegraph structure apps/server/src --depth 2 -T --limit 80
   codegraph structure packages --depth 2 -T --limit 80
   ```

   Completion criterion: you can name the likely modules, hotspots, and candidate files instead of guessing from filenames.

3. Pin exact targets.

   ```bash
   codegraph where <symbol> -T
   codegraph where --file <path> -T
   codegraph brief <file> -T
   ```

   If names are ambiguous, rerun with `--file`, `--kind`, or a file-level query. If `where` misses a local closure or property method after CodeGraph has named the file, use `brief <file>` plus a targeted exact search inside the narrowed area; record that the symbol edge was not visible. Completion criterion: every candidate has an exact path/line or a named CodeGraph blind spot with the narrowed file path.

4. Trace the relevant structure.

   ```bash
   codegraph context <symbol> -T --file <path>
   codegraph deps <file> -T --brief
   codegraph deps <file> -T --json
   codegraph exports <file> -T
   codegraph path <symbol-from> <symbol-to> -T
   codegraph dataflow <symbol> -T --file <path>
   ```

   For concise dependency summaries, prefer `deps --json` and extract `results[0].imports` / `results[0].importedBy` instead of dumping every symbol consumer. For cycles, this is the primary way to prove which imports create each file edge.

   For contract work, trace the spine as separate evidence: schema/type definition, method string or RPC tag, protocol/group assembly, server handler, client runtime wrapper, and app-surface adapters. If CodeGraph loses an edge at any spine segment, use a targeted exact search for that segment only, then read the narrowed files. Record the spine in the three ledgers.

   Completion criterion: you know the real call/import/data path and have read the narrowed source needed to support any claim you will make.

5. Choose the behavioral seam before editing.

   Use the graph to choose where to work, then read the existing code and tests at that seam. Prefer an existing choke point over a lower-level or global hook unless the graph and source reads show the choke point cannot express the behavior.

   Completion criterion: you can state three things before the edit: the seam, the invariant, and the scope guard. Examples of invariants: public event shape, polling/lifecycle cadence, compression or persistence ordering, dialect/config boundaries, exported API shape, stable test identities, and backwards-compatible input/output behavior.

6. Check blast radius before editing shared code.

   ```bash
   codegraph fn-impact <symbol> -T
   codegraph impact <file> -T
   codegraph implementations <interface-or-trait> -T
   codegraph interfaces <type> -T
   ```

   Completion criterion: every shared function/API/model you plan to touch has its callers, dependents, implementers, transitive risk, and scope guard accounted for. If the change touches shared parser/lexer/protocol/config/runtime code, identify the feature-specific gate that keeps unrelated consumers on their old behavior.

7. After edits, refresh the map and inspect structural impact.

   ```bash
   codegraph build .
   codegraph diff-impact -T
   codegraph diff-impact --staged -T
   codegraph cycles -T
   codegraph check --staged --cycles --signatures
   ```

   Completion criterion: the structural diff matches the intended change, with no surprise blast radius, cycles, or signature changes. Then run the project’s real validation commands, including the narrow behavior test for the invariant and the regression test for the nearest unrelated consumer when the edit touched shared code.

## Branches

- Repo explanation: run the scout loop, then read package manifests and narrowed entrypoints. Use `codegraph deps <entrypoint> -T --json`, `codegraph cycles -T | head`, and `codegraph complexity -T --above-threshold --limit 20`. Explain the repo as layers: workspaces, runtime entrypoints, shared contracts/runtime, main flows, hotspots, and caveats. Completion criterion: every major workspace and cross-workspace dependency path is accounted for with CodeGraph output or source reads.
- Targeted navigation: use `where`, `brief`, `deps`, and narrowed source reads to answer “where is this?” or “who owns this?” Completion criterion: every named target has an exact path/line and the owning module is identified.
- Diagnosis: start from the reported symbol/file/entrypoint, trace with `context`, `deps`, `path`, and source reads; use `flow`, `sequence`, or `cfg` only when control flow matters. If the report is scenario-led rather than symbol-led, first scout the likely layer directories with `structure`, then pin candidates with `brief`/`deps` before any exact search. Completion criterion: the suspected path from symptom to responsible code is explicit, unresolved forks and CodeGraph blind spots are named, and the three ledgers are complete.
- Blast radius and migration: for shared functions, types, interfaces, schemas, or RPC methods, combine `where`, `exports`, `fn-impact`, `impact`, `interfaces`, and `implementations`. Completion criterion: callers, dependents, implementers, and transitive risks are accounted for before editing.
- Contract/RPC migration: first scout the contract package with `structure`, `exports`, `deps`, and `where`; pick one concrete method/schema, not a whole surface. Then trace the spine: backing schema/type → method constant/string → RPC/schema registration → protocol/client factory → client-runtime state/RPC wrapper → server handler/service → app imports/call sites. Run `impact` once with `-T` for application blast radius and once including tests for test candidates. Use targeted exact search only where CodeGraph cannot see dynamic keys, interface properties, generated protocol types, or string dispatch; exclude generated files until you need to confirm schema/method existence. Completion criterion: the report names the chosen contract, server handler/service, client-runtime dependency, affected app surfaces, highest-risk files/functions, validation commands, and dynamic risks CodeGraph may miss.
- Refactor or architecture review: combine `triage`, `complexity --above-threshold`, `cycles`, `roles --role dead`, `communities --drift`, and `structure --modules`. Completion criterion: proposed seams or risks are tied to coupling, cohesion, cycle, complexity, or role evidence.
- Cycle seam review: first find the cycle structurally, then read only the files on the cycle before proposing a seam. Use the three ledgers.

  1. Rebuild/inspect, then capture both file and function cycles:

     ```bash
     codegraph build .
     codegraph stats -T
     codegraph structure <focused-dir> --depth 3 -T --limit 120
     codegraph cycles -T
     codegraph cycles -T --json
     codegraph cycles -T --functions --json
     ```

     Pick the cycle by matching the user's focus to its files; do not rely on text cycle numbering matching JSON order. Completion criterion: one exact file set is selected, and you know whether any function-level cycle overlaps it.

  2. For every file in the chosen cycle, collect dependency and symbol evidence:

     ```bash
     codegraph deps <file> -T --json
     codegraph brief <file> -T
     ```

     Build an edge table from `deps --json`: `A imports B`, including `typeOnly`. Use `brief`/`where` for symbol inventories; do not infer symbol participation or ownership from filenames. Completion criterion: every edge around the loop is accounted for exactly once.

  3. Read narrowed source only after the cycle files and imports are known. For each edge, verify the import line and the narrowed use that makes the dependency real; targeted exact search is allowed after CodeGraph has named the files. Identify each file's responsibility from code, not CodeGraph risk labels. Completion criterion: structural evidence, import/use evidence, and responsibility interpretation are separately available.

  4. Pick the seam by removing the least-owned edge: prefer extracting pure/shared logic out of UI/store modules over making lower-level model/state code import React components. Check blast radius with:

     ```bash
     codegraph fn-impact <candidate-symbol> -T
     codegraph impact <candidate-file> -T
     codegraph fn-impact <candidate-symbol> --include-tests --depth 3
     codegraph impact <candidate-file> --include-tests
     ```

     Completion criterion: the proposed seam names the edge to remove, the symbol or module to extract/invert, the direct callers/importers, and the likely tests affected.

  Final report criterion: name the exact file-level cycle; say whether a matching function-level cycle exists; list every cycle edge with CodeGraph import evidence and source-read import/use evidence; separate structural facts from responsibility interpretation; propose one smallest-blast seam as a plan, not proof; name affected files/functions; state CodeGraph blind spots; give the real test/typecheck commands that would prove the refactor.
- Dead-code cleanup: run the suspect funnel below. Completion criterion: every proposed removal has CodeGraph absence evidence, exact-search absence evidence across first-party consumers, source-read confirmation of what the symbol does, package/export-boundary risk named, tests considered with `--include-tests` where available, and rejected false positives listed separately.

  1. Build the suspect set with structural queries, not grep:

     ```bash
     codegraph roles -T --role dead --json
     codegraph exports <file> -T --unused
     codegraph exports <file> --include-tests --unused
     codegraph where <symbol> -T
     ```

     If collecting many files, parse both `results` and `reexportedSymbols` from `exports --unused --json`. For a directory, loop files or post-filter JSON; do not pass the directory to `roles` positionally.

  2. Demote every “No uses found” result to a suspect until corroborated. For each suspect, run exact fixed-string search for the exported identifier across the repo, excluding generated/vendor/build output, then read the defining file and any hits.

  3. Classify hits: real runtime/type consumer, test-only consumer, re-export wrapper, declaration-only/self-reference, generated/config/dynamic/string-key risk. A wrapper re-export is not a runtime use, but it may still be a public API commitment.

  4. Report candidates and rejects in separate lists. Put CodeGraph evidence and follow-up search/source evidence in separate columns or sentences; do not let one imply the other.
- Code review after edits: rebuild, then use `diff-impact`, `diff-impact --staged`, `cycles`, and `check --staged --cycles --signatures`. Completion criterion: structural diff matches the intended change, surprises are listed, the seam/invariant/scope guard still match the patch, and real tests/typecheck run.
- Test targeting: run impact/dependency queries with `--include-tests` when supported, then inspect likely test files. Completion criterion: the recommended test set covers touched code, direct callers, and changed contracts; gaps are explicit.
- Runtime/reconnect flow: use this for session restore, warm cache, live process recovery, reconnect, or restart scenarios. Scout server transport, persistence, runtime service, client-runtime state, and UI route/component directories before searching. Trace two paths when both exist: read-model restoration (persisted projection/cache → HTTP/WS snapshot/subscription → client state → UI) and live runtime recovery (persisted binding/cursor → service routing → adapter resume/start → provider-native RPC). Treat method strings, cache `afterSequence` cursors, generated protocol schemas, Effect layers, and object-literal handlers as blind spots requiring targeted search and source reads. Completion criterion: persistence tables/services, RPC/HTTP contracts, client state subscribers, UI renderers, blind spots, follow-up reads/searches, and proof commands/manual flows are all present in the three ledgers.
- Semantic search: only use `codegraph search "query"` after `codegraph embed .`; otherwise there are no embeddings. Use `--file` and `--kind` to narrow noisy results.
- Automation: use `batch`, JSON/NDJSON output, `export`, `plot`, and `snapshot` when results need to be compared, visualized, or scripted.

Read [`COMMANDS.md`](COMMANDS.md) when you need the command atlas, rare branches, output modes, or known CLI quirks.

## Reporting language

- Say: “rebuilt the CodeGraph index,” “stats show…,” “diff-impact shows…,” or “structural check found…”.
- Do not say: “CodeGraph passed,” “build passed,” or “validated” unless the project’s real validation commands also passed.

## Rules of thumb

- Prefer `-T` / `--no-tests` while scouting application code; rerun without `-T` or with the supported include-tests flag when test coverage or test-only callers matter.
- Use `codegraph help <command>` before relying on any flag not named in this skill.
- Use CodeGraph before broad grep/read, not instead of reading. The map narrows the work; source files and tests prove it.
- Let CodeGraph make the edit smaller, not more elaborate. After scouting, preserve the existing public shape and closest behavioral seam unless source reads prove a broader change is necessary.
- In reports, use the three ledgers. Do not let targeted search become a substitute for the initial structural scout.
- If output is stale, low-quality, or missing relationships, rebuild before trusting it. Use `--no-incremental` only when the incremental graph looks corrupt.
- If MCP is configured, you may use it; otherwise run the CLI through `bash`.
