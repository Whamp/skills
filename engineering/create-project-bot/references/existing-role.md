# Existing-role registration

Use this branch when a role home, profile or persistent conversation already
exists. Registration adds file-backed role state; migration changes the runtime
or its files and requires its own explicit scope.

1. Read the existing bootstrap, profile, guide and factual handoff. Identify the
   current conversation, project, host, execution directory, active work and
   authoritative shared references from actual records.

   **Complete when:** identity and ownership are supported by evidence rather
   than a title or normalized directory name.

2. Keep an existing process's code, execution directory, history, jobs, incident
   state and pending deliveries in place. Put the profile in the agreed role
   home. Its bootstrap must name that home explicitly when execution is elsewhere.

   **Complete when:** the proposed file diff preserves runtime and owner state;
   every retained dependency has a working reference.

3. Merge a matching profile idempotently. Preserve memory and provenance.
   Moving old flat profile files into `.bot/` requires updating every active
   bootstrap/reference affected by that move and preserving a recovery copy.
   Keep legacy Sidebar IDs as historical provenance only when relevant.

   **Complete when:** a second registration creates neither another identity
   nor another conversation; all changed references resolve.

4. For an existing conversation, provide the explicit role-home bootstrap
   pointer through the supported harness and verify consumption. A profile-only
   registration does not require a fork, cwd switch or shared-environment edit.

   **Complete when:** startup/context evidence shows the role instructions were
   read in the preserved runtime. Otherwise report registration pending.

A requested replacement conversation needs a source-linked factual handoff:
remit, constraints, judgments with dates, current work, unresolved work, next
actions and evidence locations. A fresh session with a handoff is not native
history inheritance. Retain the original conversation and registered evidence;
retirement needs explicit scope and lifecycle checks.
