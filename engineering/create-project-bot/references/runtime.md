# Runtime registration and acceptance

Read this branch only when the requester wants a working bot, or authorizes
binding a file-backed profile to an existing conversation.

## Provision or bind

1. Inspect the current harness's documented interface. Resolve actual project,
   host, model permission and execution-directory support. A directory, JSON
   profile or visual parent is not proof of a runtime binding.

   **Complete when:** the supported mechanism can select the requested execution
   context without guessing IDs or editing live internal records.

2. For a new role, create a normal persistent conversation in the intended
   project and execution directory. For an existing role, keep its conversation
   unless replacement is explicitly requested. Send its role-home `AGENTS.md`
   pointer and the bounded startup assignment.

   **Complete when:** the actual context matches the requested project/host/cwd;
   unverified bindings remain pending in the profile.

3. Have the role read its real bootstrap/profile files and applicable project
   references. Ask it to state its remit, authority, reporting/contact source,
   current work and next action, and resolve one representative existing
   reference. Use reading and reasoning, not a new operational run.

   **Complete when:** startup evidence demonstrates the intended role and
   reference access without creating schedules, credentials or external actions.

## Accept

Check the startup evidence yourself, including actual project/cwd and source
reads. A role's own ready marker is a review candidate, not acceptance.

Record verified IDs and provenance in `.bot/bot.json`; change status to
`verified` only for verified startup. Update an existing authoritative contact
index only after acceptance. A manager relationship is organizational routing,
not automatically native parent/lifecycle ownership.

Keep a concise `.bot/BOOTSTRAP-VERIFICATION.md` when a persistent startup was
tested. Record checks, source evidence, limits and acceptance owner; link it
from `HANDOFF.md`. Preserve role memory and active-work pointers.

**Complete when:** runtime facts, profile and contact authority agree, all
requested checks pass, and operational readiness beyond this startup remains
accurately bounded.

## BB compatibility

When BB is the harness, use its current CLI skill or `bb guide` and command
help for supported provisioning and contact operations. Confirm the destination
project and environment/cwd independently; native thread parenting does not
move either. A fresh conversation with a handoff does not inherit native history.

Use a separate supported environment when a cwd change is authorized. Retain
shared environments used by other threads. File-backed profiles work through
their bootstrap, not a dependency on Bots Sidebar.
