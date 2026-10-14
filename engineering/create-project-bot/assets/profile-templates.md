# Profile templates

Replace tokens before writing. `PROJECT_ROOT`, `ROLE_HOME` and `EXECUTION_DIR`
are absolute resolved paths. The default execution directory is the role home.
`NAME` is the display name; `ROLE_LABEL` is a short label, not a second remit.

Replace optional references with real paths or JSON `null`. Fill runtime IDs
only after supported runtime verification. Serialize JSON values with proper
escaping. The metadata fields below form the common profile; add domain fields
only when the role needs them.

Fill content slots from the assignment: `INITIAL_FACTS`, `LESSONS`,
`OPEN_QUESTIONS`, the five `ROLE_*` passages, and the three `HANDOFF_*` passages.
Use dated evidence for existing work and an explicit unknown where needed.
A new role can have no lessons or transferred work. Generated files contain
actual role content, not these authoring directions or unresolved slots.

## AGENTS.md

```markdown
# NAME bootstrap

Role home: ROLE_HOME. Execution directory: EXECUTION_DIR.
Resolve the role-state paths below against the role home, not an unrelated cwd.

Read .bot/SOUL.md and .bot/MEMORY.md at the start of a turn.
Read .bot/role.md for remit and workflow, and .bot/HANDOFF.md for current work.
Read .bot/settings.json and .bot/bot.json for governing references and provenance.
Follow inherited project instructions and the applicable references in settings.json.
Profile JSON describes this role; the harness supplies actual runtime configuration.
```

## .bot/SOUL.md

```markdown
# NAME

You are NAME. Your remit, reporting relationship and operating rules are in
.bot/role.md. Maintain durable learned state in .bot/MEMORY.md and current
transfer context in .bot/HANDOFF.md.
```

## .bot/MEMORY.md

```markdown
# NAME memory

## Established facts
INITIAL_FACTS

## Lessons
LESSONS

## Open questions
OPEN_QUESTIONS
```

## .bot/settings.json

```json
{
  "profileOnly": true,
  "sharedWorkspaceInstructions": "PROJECT_ROOT/AGENTS.md",
  "operatingGuide": "ROLE_HOME/.bot/role.md",
  "teamRecord": null,
  "organizationFile": null
}
```

## .bot/bot.json

```json
{
  "schemaVersion": 1,
  "profileOnly": true,
  "name": "NAME",
  "role": "ROLE_LABEL",
  "roleHome": "ROLE_HOME",
  "workingDirectory": "EXECUTION_DIR",
  "hostId": null,
  "projectId": null,
  "environmentId": null,
  "mainThreadId": null,
  "manager": null,
  "status": "scaffolded"
}
```

## .bot/role.md

```markdown
# NAME operating guide

## Remit
ROLE_REMIT

## References
ROLE_REFERENCES

## Workflow and quality
ROLE_WORKFLOW

## Authority
ROLE_AUTHORITY

## Communication
ROLE_COMMUNICATION
```

## .bot/HANDOFF.md

```markdown
# NAME handoff

## Origin
HANDOFF_ORIGIN

## Current state
HANDOFF_STATE

## Next actions
HANDOFF_NEXT_ACTIONS
```
