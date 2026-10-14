---
name: create-project-bot
disable-model-invocation: true
description: Create or register a project bot with durable .bot state and verified startup.
---

# Create a project bot

A **role home** holds one bot's identity, memory and operating guidance.
Its working files stay outside `.bot/`. Its execution directory normally
equals its role home; an existing process can keep a different execution directory.

## 1. Resolve the assignment

Read the project's instructions and existing role/contact conventions.
Resolve the project root, bot name, remit, role-home path, reporting contact,
existing permissions and requested result: **scaffold** or **working bot**.
Default to scaffold unless the request or existing authorization includes
conversation setup.

Use `<project-root>/<role-slug>/` by default. Use an existing role grouping
when the project defines one. For example, project `~/fleet` and role
`Endurance` give role home `~/fleet/endurance`.

Resolve the destination, including symlinks, inside the authorized project scope.
Inspect it before writing. If it already holds a role, continue that identity
rather than create a duplicate. Existing agents or profiles:
read [existing-role registration](references/existing-role.md).

**Complete when:** the home, remit and requested result are explicit; existing
ownership is resolved; remaining product or authority decisions are identified.
Ask only for decisions that the request and held project evidence cannot settle.

## 2. Separate role state from shared state

Use this layout:

```text
<role-home>/
  AGENTS.md
  .bot/
    SOUL.md
    MEMORY.md
    settings.json
    bot.json
    role.md
    HANDOFF.md
  <working files>
```

| File | Responsibility |
| --- | --- |
| `AGENTS.md` | Short bootstrap into this role and its inherited project rules. |
| `.bot/SOUL.md` | Durable identity and a pointer to the role's operating guide. |
| `.bot/MEMORY.md` | Durable facts, lessons and unresolved questions with provenance. |
| `.bot/settings.json` | References to governing files and contact authority. |
| `.bot/bot.json` | Descriptive identity, role home, execution directory and verified runtime IDs. |
| `.bot/role.md` | Remit, workflow, quality criteria, authority and communication. |
| `.bot/HANDOFF.md` | Initial assignment or factual transfer: current work and next actions. |

Project contracts, shared knowledge, queues and process runbooks stay at their
existing authoritative locations. Point to them from the profile. Keep sensitive
runtime state and credentials in their owner's protected store.

Profile JSON is **descriptive**, not runtime configuration. A profile grants no
new permissions, schedules or external access. A file-backed role needs no
Sidebar identity or replacement plugin record.

**Complete when:** every role file has one purpose, shared authorities have
explicit pointers, and role home versus execution directory is unambiguous.

## 3. Write the profile

Use [profile templates](assets/profile-templates.md). Fill them from the resolved
assignment and actual files. Use absolute resolved paths in JSON; use `null`
for absent optional references and unverified runtime IDs.

Keep detailed rules in `role.md`, learned state in `MEMORY.md`, and transfer
state in `HANDOFF.md`. A new role's handoff records its initial assignment;
it does not invent prior work. Route contacts through the project's existing
contact authority; record a direct verified contact only when none exists.

Preserve existing role memory and owner work. Propose a focused diff for an
existing file rather than replace it wholesale. Follow the repository's
versioning workflow and track only suitable role state.

**Complete when:** all seven files exist, JSON parses, populated references
resolve, placeholders are gone, and unrelated files remain unchanged.

## 4. Verify the requested result

For a **scaffold**, check the final tree, cross-file names and paths, inherited
rules, contact references, authority and initial handoff. Report it as scaffolded;
runtime IDs can remain `null`. A scaffold is not an active conversation.

For a **working bot**, read [runtime registration and acceptance](references/runtime.md).
Use the current harness's supported project/workspace mechanism. Verify actual
startup reads and the real execution context before recording active contacts.

**Complete when:** every requested file/setup check has evidence; runtime is
either verified or explicitly pending. Report the tree, the result and limits
directly to the requester. Additional automation or migration is separate work.
