# Cursor models as Pi subagents

## Check the execution and tool contract

The `cursor/*` provider requires the `pi-cursor-sdk` extension in the child runtime. Pi launches the child, but Cursor's SDK runs its inner agent loop. This is not Pi's native tool loop or the separate Cursor CLI agent.

For the local SDK runtime, distinguish three tool sets:

| Tool set | How the child uses it |
| --- | --- |
| Cursor host tools | Use the file, shell, and search tools actually exposed by Cursor. Names and availability can differ from Pi. |
| Cursor-configured MCP | Comes from Cursor settings, independently of Pi's MCP configuration. |
| Pi bridge | Active Pi tools exposed through loopback MCP as `pi__*` names. Call the exposed name, not its Pi transcript label. |

The bridge defaults on. Overlapping Pi built-ins `read`, `bash`, `write`, `edit`, `grep`, `find`, and `ls` are hidden by default because Cursor has native equivalents. Active non-overlapping extension tools can still be bridged. Therefore, missing `pi__read` does not establish missing file access, and selecting Cursor does not imply all Pi tools are unavailable.

Use the current bootstrap tool manifest and exposed schemas as evidence. `/cursor-tools` reports the current tool configuration in an existing interactive session. MCP `listTools` does not enumerate Cursor host tools. `cursor-replay-*` IDs and display-only transcript names are not callable tools.

Pi `--tools`, `--exclude-tools`, and `--no-tools` affect Pi tools and bridge exposure, not Cursor host tools or Cursor-configured MCP. A Pi read-only allowlist is not a Cursor sandbox. Preserve the task's no-write, no-network, and no-delegation restrictions across every tool set. If the task requires enforced isolation that this runtime cannot establish, choose another permitted route rather than claiming the Pi allowlist enforces it. Do not change bridge, sandbox, or ambient-MCP settings merely to make a reviewer launch.

Complete when the child runtime loads the provider, its available tools cover the role, and its authority restrictions remain satisfied. Local bridge behavior does not apply to Cursor cloud runs; do not switch runtimes to recover missing tools.

## Launch a compatible role

Apply the caller's pool and model permission rules first. Explicit-user-message approval requirements also apply to wrappers, fallbacks, and resumed children. This example grants no model permission.

Discover an executable Pi role and a supported exact model selector before launch. A role that fails Pi's required-tool preflight never reaches the Cursor loop. Use a compatible supported role rather than assuming Cursor's native tools satisfy missing Pi registry entries.

```js
subagent({
  action: "execute",
  input: {
    agent: "reviewer",
    task: "Read-only review of the supplied diff and repository context. Use the file and search tools exposed in this run. Report cited findings and any inaccessible evidence. Do not edit, delegate, or access the network.",
    model: "cursor/grok-4.6:slow:high",
    context: "fresh"
  }
})
```

Use this shape only after verifying that `reviewer` is executable in the current host. Workflow children use the same `model` field on `runs.run()` or `runs.all()` items. The `cursor-agent` and `cursor-agent-writer` roles use the separate Cursor CLI runtime; a provider failure does not authorize that substitution.

## Give reviewers a usable brief

Provide the repository path, fixed review base, review axis, and evidence required. Describe operations such as reading files and searching references rather than requiring Pi tool names. If shell inspection is permitted, authorize only the required read-only commands and require an explicit repository directory. If shell use is forbidden, supply the diff and file list instead of asking the reviewer to run Git.

Require the child to use only tools exposed in its current run, including the exact `pi__*` names for any bridged extension tools. Tool availability never grants permission to edit, delegate, or contact a service.

If evidence is inaccessible, distinguish a Pi role-preflight failure, a provider/model launch failure, and a missing tool inside a running Cursor agent. Use an authorized native equivalent or supply the missing artifact when that preserves the review contract. Otherwise replace the route with a permitted capable alternative. Do not count a tool failure as completed review evidence.

## Evidence and version scope

Checked against installed `pi-cursor-sdk` 0.3.6 and `@cursor/sdk` 1.0.27. Recheck the installed extension after upgrades; do not assume the parent's tool set is inherited unchanged.

Upstream reference: [Cursor tool surfaces in Pi](https://github.com/fitchmultz/pi-cursor-sdk/blob/main/docs/cursor-tool-surfaces.md).
