---
name: testing
description: Testing strategy and explicit behavioral evidence. Use for selecting test seams and levels, writing regression, unit, integration, contract, or browser tests, proving fixes, reviewing tests, diagnosing flakes, and interpreting coverage or mutation results. Use it to choose explicit examples, property-based testing, or fuzzing as the primary search mechanism for each risk.
---

# Testing

Build the smallest executable argument that can disagree with a wrong implementation. A passing test matters only when its setup, observation, and oracle can expose the named risk.

## Route before choosing examples

Inspect the requested contract, relevant production code, types, callers, and
existing tests before choosing evidence.

Choose one primary search mechanism for each independently falsifiable risk:

| Primary search | Use when |
| --- | --- |
| **Examples** | The meaningful cases form a small explicit table or named regression. Continue with this skill. |
| **Property-based testing** | A broad generated domain, operation sequence, or schedule can challenge a compact independent oracle. Load `property-based-testing`. |
| **Fuzzing** | Coverage-guided mutation is useful at a reachable production input seam with a named risk, oracle, supported engine, and bounded budget. Load `fuzzing`. |

A primary search mechanism is not exclusive evidence ownership. Explicit examples
may still document named boundaries, minimized regressions, or separate risks.
Every branch returns to this skill's final evidence audit.

Load branch-specific guidance only when its matching dimension applies:

| Dimension | Guidance |
| --- | --- |
| Test-first sequencing requested by the user | Load an installed `tdd` skill for red-green sequencing; this skill still owns evidence quality. |
| Database, HTTP, filesystem, queue, service, or contract boundary | Read [integration and contract testing](references/integration-and-contract.md). |
| Real browser journey or deployment wiring | Read [end-to-end browser testing](references/e2e.md). |
| JavaScript or TypeScript execution details | Read [JavaScript and TypeScript testing](references/javascript-typescript.md). |
| Rust execution details | Read [Rust testing](references/rust.md). |
| AI-generated tests or suspected test slop | Read [adversarial test audit](references/adversarial-test-audit.md). |
| Flakes, coverage, mutation results, duplication, quarantine, or removal | Read [test suite maintenance](references/test-suite-maintenance.md). |

Load more than one branch when dimensions combine, such as Rust code crossing a
database boundary.

**Complete when:** each independently falsifiable risk has a primary search
mechanism, or the missing information needed to choose one is named.

## 1. Inventory and frame the contract

Write one contract card for each independently observable requested claim and
each source-grounded preservation risk:

```text
Contract: <requested behavior>
Preservation: <adjacent existing behavior, or none>
Observation: <public surface where the contract is visible>
Risk: <plausible failure>
Oracle: <independent source of the expected result>
Counterfeit: <wrong behavior the evidence can reject>
Primary search: <Examples | Property-based testing | Fuzzing>
Evidence: <existing test, transient probe, durable test, or command>
```

Use one card for a single claim. Several cards may share one invariant or
evidence route when each card states why it applies. A contract card does not
require a new test file.

Ground cards in specifications, public documentation, types, callers, accepted
behavior, and existing tests. Treat names and comments as search leads, not
proof. Confirm any production-interface or scope-expanding seam before adding it.

**Complete when:** every requested claim and grounded preservation risk has an
evidence route, or is marked unverified with the missing evidence named.

## 2. Choose the smallest discriminating surface

Place the test at the narrowest surface that still contains the risk:

- use an example test for a small set of named cases
- cross a real boundary when serialization, schema, configuration, lifecycle, or protocol behavior is the risk
- use a browser only when browser behavior or cross-system wiring is part of the claim
- use generated search only when a broad domain and compact oracle create leverage

Choose real dependencies and test doubles by what the test must detect. A fake is appropriate when it preserves the contract under test and removes an unrelated, destructive, unavailable, or prohibitively expensive dependency. A real dependency is required when its actual behavior is the risk.

Narrow evidence may localize a fault, but it does not discharge a contract whose
observation is a runnable artifact, serialized boundary, user-facing entry point,
or downstream consumer. Exercise an exact journey through that surface when the
surface itself is part of the contract.

**Complete when:** a narrower surface would miss the named risk, every replaced
dependency has an explicit realism tradeoff, and every contract observed through
an outer surface has an evidence route through that surface.

## 3. Build an independent test

Follow the repository's existing framework, naming, fixture, and file-layout conventions. Test through the selected seam and observe public behavior rather than private calls or intermediate state.

Keep the oracle independent:

- derive the expected result from a specification example, worked literal, reference implementation, invariant, or public postcondition before consulting production output
- keep expected-value calculation structurally independent from production; avoid repeating the same algorithm
- assert the meaningful result, not merely that execution completed or returned a value
- control time, randomness, locale, ordering, scheduling, and external responses when they affect the result
- make test data reveal the contract; omit irrelevant fields and accidental noise

Extract setup behind helpers only when the helper names a domain operation or hides substantial mechanics. Keep the behavior and decisive assertion readable from the test.

**Complete when:** the test can fail while the code still compiles, and a reader can explain the expected result without opening production internals.

## 4. Prove discrimination

Use the strongest safe discrimination proof available:

1. For a bug, run the test against the buggy or pre-fix revision and then against the fix.
2. For new behavior, run the test before implementing the behavior and again after implementation.
3. For behavior that already exists, use an available mutation tool or safely introduce a local temporary counterfeit—for example, suppress the state transition, return the wrong boundary value, or invert the condition—then restore the implementation.
4. When none of those proofs is safe or proportionate, record the unproven counterfeit and the constraint that prevented exercising it. Prefer an honest limitation over changing production code merely to manufacture a red result.

Inspect every red result. A setup error, timeout, unrelated exception, or failure in a different assertion does not prove the intended behavior. Leave no deliberate defect in the final change.

**Complete when:** the strongest safe proof goes red for the named reason and green after the correct behavior is restored, or the unproven counterfeit and blocking constraint are explicitly recorded.

## 5. Close the evidence

Use this evidence ladder:

1. While iterating, run the narrow evidence affected by the latest change.
2. After the last relevant mutation, run each contract card's evidence on the
   final patch.
3. Run the nearest affected regression scope.
4. Run the repository's required broad checks when they are available and
   proportionate.

A command that rewrites source, fixtures, snapshots, goldens, generated files, or
configuration is a mutation and invalidates earlier evidence for affected risks.
Inspect the resulting diff before relying on later validation.

Confirm that new and renamed tests are collected. Account for focus, skip, todo,
tags, feature flags, exclusions, order, concurrency, retry, and shared state when
they affect the claim.

Classify each failed, timed-out, skipped, or zero-test command as a product
failure, runner failure, known baseline failure, unrelated failure, or expected
red. Resolve it, revert the responsible change, or record the limitation. A
narrower green result does not supersede an unresolved affected-scope failure.

When the broad suite is already red, use current base-revision or CI evidence
when available to identify pre-existing failures. Completion then requires green
targeted and affected-scope evidence plus an accounting of the broad result; it
does not require repairing unrelated baseline failures.

Repeat a green command only after changed code, command side effects, or a newly
identified risk could change its result. Repeat a red command when a relevant
edit, setup correction, or changed hypothesis makes the rerun informative.

Before finishing:

- mark every contract card `verified` or `unverified` with its limitation;
- account for unexpected or scope-expanding changed paths;
- preserve commands and failure context needed to reproduce limitations.

A card is closed when it is verified or its limitation is recorded. Stop test
work when all cards are closed on the final patch and another test or
rerun would address no changed code, open card, changed risk, or unresolved
failure.

**Complete when:** every contract card has current final-patch evidence or an
explicit limitation; targeted and affected-scope evidence has no hidden failure;
required broad results are accounted for; and no deliberate counterfeit remains.
