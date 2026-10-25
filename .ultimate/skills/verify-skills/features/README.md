# Skills verification map

Read [verify-skills](../SKILL.md) for launch, doctor, evidence and cleanup. Run recipes from its isolated checkout, with `RUN_ROOT` and `EVIDENCE_ROOT` set. Evidence belongs outside disposable scratch state. There is no app server to drive.

## Journeys

- [Contributor quality gate](quality-gate.md): the documented full repository check and explicit project-tooling checks.
- [Published collection discovery](discovery.md): listing every canonical skill, including user-only skills, without leaking local tooling.
- [Portable skill validation](portable-skill.md): accepting a valid manifest and rejecting a broken local reference.
- [Safe cleanup boundaries](cleanup-safety.md): approval and filesystem safety through isolated fixtures.

## Reporting

Capture the invoked command, output, exit code and revision for each driven entry point. Inspect the resulting names, diagnostics or fixture assertions, not just the final exit code. A journey not driven is unverified. Record failed preconditions in its report and update that feature's Gotchas when they reveal a durable constraint.

The original installer gate passes despite discovering only `lane`. Until its correction is verified, report the contributor gate's exit status separately from published collection discovery. These are distinct claims.
