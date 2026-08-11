# Adversarial test audit

Use this branch for AI-generated, inherited, bulk-created, or suspicious tests. Audit evidence rather than appearance. A **live** test is collected by the intended command, reaches the claimed seam, reaches its decisive oracle, and can turn red for the named risk.

## 1. Bound the audit and map the evidence

Choose a risk-bearing slice: the tests added by a change, tests around changed code, a generated batch, or a named subsystem. Record excluded tests instead of implying a whole-suite conclusion.

Derive each contract from the strongest available authority:

1. issue, specification, acceptance criteria, or public documentation
2. public types, schemas, callers, and recorded product decisions
3. historical defects and the behavior of their accepted fixes
4. existing tests as corroboration

Derive expected outcomes before consulting production output. The current implementation shows what exists; it does not establish its own oracle. When undocumented compatibility is the contract, establish it from released behavior or consumer reliance rather than one current execution. Surface conflicts between authorities as unresolved product decisions.

Create an evidence map:

```text
Contract: <observable behavior and authority>
Risk: <plausible failure>
Observation: <public result, state, event, or error>
Candidate tests: <tests that claim to protect it>
Oracle source: <independent source of the expected result>
```

**Complete when:** every test in scope maps to a named contract and risk, or is marked `unresolved`; every resolved contract has an authority and independent oracle source; and the audit boundary, exclusions, and unresolved decisions are explicit.

## 2. Prove each test is live

For every candidate test:

1. Use the runner's collection, listing, or focused execution output, then the intended CI command, to prove the test is selected. Account for focus, skip, todo, tag, feature, filter, and exclusion markers.
2. Run the test directly with retries disabled when the runner permits it. Record retries, setup failures, timeouts, and failures outside the decisive assertion separately from behavioral failures.
3. Prove the setup reaches the claimed seam with focused coverage, a trace, or the smallest safe temporary probe.
4. Prove the decisive oracle is reached with a safe temporary assertion tripwire or a counterfeit expected to reach that assertion. Restore every probe.
5. Make preconditions explicit before the decisive assertion. Place the assertion on every successful path rather than behind an optional branch or early return.
6. Await work that affects the observation. Make callbacks signal completion, and make exception handlers fail on unexpected errors.

A broad green run is not collection evidence. Coverage can prove reach, but only an oracle tripwire or discrimination run proves the test observes the result.

Classify each test as `live`, `not collected`, `skipped`, `vacuous`, or `blocked`, with the command and evidence behind the classification.

**Complete when:** every test in scope has a liveness classification; every `live` test has collection, seam-reach, and oracle-reach evidence; and every non-live or blocked test has a concrete cause.

## 3. Challenge AI-slop signals

Use these signals to choose probes, then classify the test from execution evidence rather than a smell count:

| Signal | Adversarial question | Preferred repair |
| --- | --- | --- |
| Implementation echo | Was the expected value copied from current output, a production constant, or the production algorithm? | Re-derive it from a worked literal, invariant, reference model, or public postcondition. |
| Completion-only oracle | Is successful completion itself the contract, or would any non-throwing, non-null, truthy, or broadly successful result pass? | When completion is not the contract, assert the contract-bearing value, state transition, event, or error. |
| Fixture echo | Does the assertion merely recover a value inserted by setup while the claimed behavior can be bypassed? | Counterfeit the behavior and observe its public effect. |
| Mock echo | Does the test assert a scripted mock response or only the calls used to obtain it? | Keep the mock at an external boundary and assert the owned behavior after that boundary. |
| Choreography lock | Can a behavior-preserving refactor break call counts, call order, or private-state assertions? | Move the oracle to the public seam unless choreography is the contract. |
| Happy-path clone | Do parameterized or neighboring tests exercise the same risk with cosmetically different data? | Give each case a distinct risk, boundary, or diagnostic role; collapse the rest. |
| Oracle laundering | Does a helper or broad snapshot hide the decisive expectation from the test body and review? | Expose focused contract fields; keep a snapshot only when the serialized artifact is the contract. |
| Permissive failure | Does any exception, rejection, or error text satisfy the test? | Assert the public error type, code, payload, and required side effects. |
| Framework trivia | Does the test prove a getter, constructor, mock library, or language feature rather than a product decision? | Move it to the boundary where product wiring matters, or apply the removal rules. |

**Complete when:** every signal found has been challenged at the claimed seam, and each proposed repair names the stronger observation or counterfeit it will add.

## 4. Build a counterfeit set

A single easy mutant invites overfitting. Build the smallest proportionate **counterfeit set** for each contract-risk cluster:

1. **No-op:** suppress the effect, return a default, or skip the state transition.
2. **Boundary:** invert a branch, move a threshold, drop an error mapping, or mishandle an empty, repeated, maximum, or invalid case.
3. **Semantic:** implement a plausible alternative that preserves obvious examples while violating the contract. Derive it from the issue, defect history, adjacent code, or a credible developer mistake rather than the assertion's syntax.

Use the pre-fix revision or reproduced defect first when available; it is usually the strongest semantic counterfeit. Existing mutation tools can supply additional probes, but treat surviving and killed operators as leads rather than a score target.

For high-consequence behavior and each contract-risk cluster represented only by generated tests, exercise at least two distinct rungs, including a semantic counterfeit. After repairing the tests, introduce one new semantic **holdout** that did not shape their assertions. When a safe counterfeit is disproportionate, record the exact survivor and constraint.

Run the narrowest candidate test or risk cluster against each counterfeit so an unrelated test cannot claim the kill. Inspect the red reason, then record a kill matrix:

```text
Contract/risk | Counterfeit | Expected detector | Actual red reason | Survivor or constraint
```

A test need not kill every counterfeit. A kept test must kill a named counterfeit or contribute unique boundary, regression, setup, or diagnostic evidence.

**Complete when:** every high-consequence cluster and every cluster represented only by generated tests has a no-op or boundary challenge plus a semantic challenge and holdout; every kept test has a recorded contribution; and every plausible survivor in the exercised set is repaired or explicitly accepted with its constraint.

## 5. Replace weak tests without losing evidence

Freeze the original tests, evidence map, and counterfeit set before editing. Repair in this order:

1. replace a contaminated or permissive oracle with a contract-derived one
2. choose inputs and explicit preconditions that distinguish the named risk
3. move observation to the narrowest public seam that contains the risk
4. restore dependency realism required by that risk
5. simplify setup and improve failure diagnostics

When current behavior conflicts with a contract-derived expectation, preserve the expectation and resolve the production behavior or product decision before declaring green.

Run the old and replacement tests separately against the same pre-fix defect or counterfeit set. Keep the old test until the replacement provides equal or stronger discrimination and preserves any unique boundary or diagnostic signal. Apply [test suite maintenance](test-suite-maintenance.md) before quarantine or removal.

**Complete when:** before-and-after evidence shows the replacement is live, kills every required counterfeit the old test killed, closes the targeted survivor, and loses no unique contract, boundary, regression, or diagnostic evidence.

## 6. Validate the audited slice

Run collection again, then the focused tests, relevant suite, and repository validation. Stress the seeds, order, worker count, scheduler, time, or external responses implicated by the audited risks. Confirm that every temporary probe and counterfeit is gone.

Report:

```text
Scope and exclusions:
Contract authorities and unresolved decisions:
Liveness classifications:
Counterfeit kill matrix:
Kept, repaired, quarantined, and removed tests:
Accepted survivors and constraints:
Validation commands and results:
```

**Complete when:** every test in scope has a disposition backed by liveness and discrimination evidence; every high-consequence contract has a live detector; the relevant suite and project checks pass; and the report exposes unresolved contracts, survivors, and exclusions.

## Research basis

- [SWE-Mutation](https://aclanthology.org/2026.findings-acl.1976/) found that realistic agent-generated mutants exposed substantially weaker test discrimination than conventional mutants.
- [TESTGENEVAL](https://proceedings.iclr.cc/paper_files/paper/2025/file/26ded5c8ee8ec1bc4caced4e1c9b1584-Paper-Conference.pdf) found low mutation performance and little new coverage from model-generated test completion on mature suites.
- [Do LLMs generate test oracles that capture the actual or the expected program behaviour?](https://arxiv.org/abs/2410.21136) found that models tend to reproduce implemented behavior rather than intended behavior.
- [Design choices made by LLM-based test generators prevent them from finding bugs](https://arxiv.org/abs/2412.14137) found that pass-only filtering can discard bug-revealing tests and retain tests that validate faulty implementations.
