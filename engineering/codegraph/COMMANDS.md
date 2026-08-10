# CodeGraph command atlas

Run `codegraph --help` for the top-level list and `codegraph help <command>` before using a flag you have not used recently.

## Index and diagnostics

```bash
codegraph --version
codegraph info
codegraph build .
codegraph build . --no-incremental
codegraph stats -T
codegraph config --explain
```

`build` creates or refreshes `.codegraph/graph.db`. It is indexing, not validation.

## Orientation

```bash
codegraph map -T
codegraph structure --depth 2 -T
codegraph structure --modules -T
codegraph triage -T --limit 20
codegraph communities -T --drift
```

Use these before choosing files for a non-trivial change.

## Locate

```bash
codegraph where <symbol> -T
codegraph where --file <path> -T
codegraph brief <file> -T
codegraph children <symbol> -T
codegraph search "natural language behavior" -T --file <path-fragment> --kind function
codegraph ast --kind await --file <path-fragment> -T
codegraph ast <string-or-regex> --kind string --file <path-fragment> -T
```

`search` requires embeddings:

```bash
codegraph models
codegraph embed . --model minilm
codegraph search "query" -T
```

Hybrid search uses BM25 plus semantic ranking after embeddings exist.

## Understand one target

```bash
codegraph context <symbol> -T --file <path>
codegraph context <symbol> -T --depth 1
codegraph deps <file> -T --brief
codegraph exports <file> -T
codegraph exports <file> -T --unused
codegraph exports <file> -T --unused --json
codegraph exports <file> --include-tests --unused
codegraph dataflow <symbol> -T --file <path>
```

Use `--file` and `--kind` to disambiguate common names. For `exports --unused --json`, inspect both `results` and `reexportedSymbols`; unused public-surface suspects may be reported as re-exported symbols rather than direct results.

## Relationships and blast radius

```bash
codegraph fn-impact <symbol> -T
codegraph impact <file> -T
codegraph path <from> <to> -T --from-file <path> --to-file <path>
codegraph path <file-a> <file-b> --file -T
codegraph dataflow <symbol> -T --impact
codegraph implementations <interface-or-trait> -T
codegraph interfaces <type> -T
codegraph branch-compare <base> <target> -T
```

Use these before editing shared code or public contracts.

## Runtime and control-flow views

```bash
codegraph flow --list -T
codegraph flow <entrypoint> -T --depth 3
codegraph sequence <entrypoint> -T --depth 3
codegraph sequence <entrypoint> -T --dataflow
codegraph cfg <function> --format mermaid
```

`flow --list` can be very large in generated-heavy repos; scope or redirect output when needed.

## Health and architecture

```bash
codegraph complexity -T --above-threshold --health
codegraph cycles -T
codegraph cycles --functions -T
codegraph roles -T --role dead
codegraph roles -T --role dead --json
codegraph roles -T --dynamic
codegraph check --cycles --signatures -T
```

`roles` is not path-positional. To scope it, use supported flags from `codegraph help roles` or post-filter JSON by `.file`.

`check` is a structural gate. It still is not project validation.

## Change inspection

```bash
codegraph build .
codegraph diff-impact -T
codegraph diff-impact --staged -T
codegraph diff-impact <ref> -T
codegraph diff-impact -T -f mermaid
```

Use after editing to see whether changed symbols affect unexpected callers or files.

## Automation and artifacts

```bash
codegraph batch where <a> <b> -T
codegraph batch context --from-file targets.json -T
codegraph export -f mermaid -T -o graph.mmd
codegraph export -f json -T -o graph.json
codegraph plot -T --cluster community --overlay complexity,risk --no-open -o graph.html
codegraph snapshot save <name>
codegraph snapshot list
codegraph snapshot restore <name>
codegraph watch .
```

Most query commands support `-j`, `--ndjson`, `--csv`, or `--table`; check command help because support is not uniform.

## Ownership and history

```bash
codegraph owners <target> -T
codegraph co-change --analyze --since "1 year ago" -T
codegraph co-change <file> -T
```

These depend on CODEOWNERS or git history. Empty output may mean the repo lacks that source data.

## MCP and multi-repo

```bash
codegraph mcp
codegraph mcp --multi-repo
codegraph registry add .
codegraph registry list
codegraph registry prune
```

Use MCP only when configured in the agent environment; otherwise the CLI is enough.

## Known rough edges

- Do not say “`codegraph build .` passed” as if it were a test. Say the index rebuilt.
- “No uses found” is absence of a visible static edge, not deletion proof. Cross-check package subpath imports, barrel wrappers, path aliases, dynamic/string-key dispatch, generated/config consumers, and tests.
- Some commands document `--file` as repeatable; if the native engine throws a conversion error, retry unscoped or disambiguate with `where`, then use `--from-file` / `--to-file` where available.
- Some table/limit flags are not uniform across commands. Confirm with `codegraph help <command>`.
- Generated files can dominate results. Use `-T`, `--file`, `--kind`, limits, and scoped paths to keep output useful.
