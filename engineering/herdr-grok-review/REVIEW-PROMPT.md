# Grok debug-review contract

```text
Perform a deep, adversarial code review of the committed diff `<fixed-point>...HEAD` in `<target-checkout>`.

Review identity
- Fixed point: <resolved-fixed-point-hash>
- HEAD: <resolved-head-hash-and-subject>
- Commits: <commit-list>
- Originating request/spec: <spec-source-or-verbatim-contract>
- Repository guidance: <guidance-paths>
- Coding standards: <standards-paths>
- Known baseline failures or dirty files: <baseline-exceptions-or-none>
- Prior review findings and reproductions: <prior-findings-for-rereview-or-none>
- Checkout fingerprint: <pre-review-fingerprint>

Use the shell freely for source inspection, builds, focused tests, and minimal throwaway probes. Use Git read-only. Keep `HEAD`, the index, branch metadata, local Git configuration, and all pre-existing checkout content unchanged. Put probes in uniquely named untracked files, install a shell cleanup trap before running them, and delete them before finishing. Perform the review yourself without invoking another model or paid agent.

Treat this as a debug review, not a summary. Independently establish the runtime mechanism and look for failures that ordinary happy-path tests miss.

For a re-review, rerun every prior reproduction, then review the complete updated diff for new defects and interactions. Passing the old probes alone does not justify a safe verdict.

Focus
<change-specific-focus-list>

Review boundaries
- correctness and fidelity to the originating request;
- backward compatibility of public and callback contracts;
- concurrency, cancellation, timeout, retry, and stale-callback races;
- persistence, replay, budgeting, and aggregate-accounting invariants;
- identity uniqueness and attribution across nested or parallel work;
- cleanup of subscriptions, timers, promises, sessions, and temporary artifacts;
- interactions between changed mechanisms, not only each mechanism in isolation;
- behavior immediately before, at, and after each timeout or grace bound, including cancellation that settles late or never settles;
- whether the design is genuinely simpler and makes invalid states harder to express.

Treat existing tests as partial evidence. For each suspected behavioral defect, build the smallest deterministic reproduction you can. Distinguish:
1. regressions introduced by this diff;
2. pre-existing defects exposed but not introduced by it;
3. baseline or environmental failures with no causal link.

Report in this order:

1. Actionable findings, ordered Blocker, High, Medium, Low. Each finding must include exact file:line, mechanism, user impact, regression status, the exact reproduction command, expected and actual results, relevant counters or persisted state, and probe cleanup status.
2. Explicit checks that passed and what each check actually proves. Include the final checkout fingerprint and compare it with the supplied baseline.
3. Grades for correctness, backward compatibility, elegance/simplicity, and robustness, each with a short rationale.
4. Exactly one merge verdict: SAFE, SAFE WITH FOLLOW-UP, or NOT SAFE.

Severity and verdict must agree. Any issue that makes the change unsafe as-is is a Blocker regardless of whether it affects an optional path. If there are no blockers, say so explicitly. Avoid hypothetical style complaints without behavioral or maintenance impact.
```
