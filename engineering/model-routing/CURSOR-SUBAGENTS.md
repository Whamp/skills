# Cursor models as Pi subagents

Read this reference after selecting a `cursor/*` route. The child `agent` selects its role. The `model` field selects the Cursor provider route.

Apply the caller's pool and model permission rules before selecting this route. Explicit-user-message approval requirements also apply to fallbacks, wrappers, and resumed children. Catalog presence and this example do not authorize a restricted model. Verify the selected role is executable with the required tools before launching; a reviewer tool-profile failure is separate from model availability.

Launch a normal Pi child with the exact selector:

```js
subagent({
  action: "execute",
  input: {
    agent: "reviewer",
    task: "Review the change for concurrency and lifetime failures.",
    model: "cursor/grok-4.6:slow:high",
    context: "fresh"
  }
})
```

Workflow children use the same `model` field on `runs.run()` or `runs.all()` items. The installed Pi Cursor provider handles authentication and runs the Cursor SDK agent loop. No Python or shell wrapper is needed.

Use `subagent({ action: "models" })` to copy current selectors. The `cursor-agent` and `cursor-agent-writer` agents invoke the separate Cursor CLI runtime. Use them only when the caller explicitly chooses that runtime. A failed Pi Cursor-provider launch does not authorize a CLI substitution.
