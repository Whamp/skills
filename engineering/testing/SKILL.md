---
name: testing
description: Testing design and maintenance. Use when choosing a test seam or level; writing or reviewing regression, unit, integration, contract, browser, JavaScript/TypeScript, or Rust tests; proving a bug fix; auditing AI-generated tests or suspected test slop; diagnosing flaky tests; interpreting coverage or mutation results; or deciding whether tests should be improved, quarantined, or removed. Routes property testing and fuzzing.
---

# Testing

Build the smallest executable argument that can disagree with a wrong implementation. A passing test matters only when its setup, observation, and oracle can expose the named risk.

## Route the work

Choose every branch that materially affects the test:

| Need | Route |
| --- | --- |
| Small, explicit examples or regressions | Continue with this process. |
| Test-first sequencing | When the user requests TDD and an installed `tdd` skill is available, load it for red-green sequencing. This skill still owns test selection and quality. |
| Broad generated domains, operation sequences, or schedules | Load the `property-based-testing` skill. |
| Coverage-guided exploration of parsers, protocols, unsafe code, or untrusted inputs | Load the `fuzzing` skill. |
| Database, HTTP, filesystem, queue, service, or contract boundary | Read [integration and contract testing](references/integration-and-contract.md). |
| Real browser journey or deployment wiring | Read [end-to-end browser testing](references/e2e.md). |
| JavaScript or TypeScript execution details | Read [JavaScript and TypeScript testing](references/javascript-typescript.md). |
| Rust execution details | Read [Rust testing](references/rust.md). |
| AI-generated tests or suspected test slop | Read [adversarial test audit](references/adversarial-test-audit.md). |
| Flakes, coverage, mutation results, duplication, quarantine, or removal | Read [test suite maintenance](references/test-suite-maintenance.md). |

A language reference supplements the chosen test surface; it does not choose that surface. Load more than one reference when both dimensions matter, such as Rust code crossing a database boundary.

## 1. Frame the evidence

Write the test claim before writing test code:

```text
Behavior: <observable contract>
Risk: <plausible failure this test should expose>
Seam: <public input and observation point>
Oracle: <independent source of the expected result>
Counterfeit: <wrong implementation or defect that must make the test fail>
```

Ground the contract in specifications, public documentation, types, callers, accepted behavior, and existing tests. Treat names and comments as search leads, not proof. If selecting the seam would change scope or expose a new production interface, confirm that decision before writing the test.

**Complete when:** every field is concrete and the counterfeit could plausibly survive without this test.

## 2. Choose the smallest discriminating surface

Place the test at the narrowest surface that still contains the risk:

- use an example test for a small set of named cases
- cross a real boundary when serialization, schema, configuration, lifecycle, or protocol behavior is the risk
- use a browser only when browser behavior or cross-system wiring is part of the claim
- use generated search only when a broad domain and compact oracle create leverage

Choose real dependencies and test doubles by what the test must detect. A fake is appropriate when it preserves the contract under test and removes an unrelated, destructive, unavailable, or prohibitively expensive dependency. A real dependency is required when its actual behavior is the risk.

**Complete when:** a narrower test would miss the named risk and every replaced dependency has an explicit realism tradeoff.

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

## 5. Validate and operate

Run the narrow test while iterating. For every new or renamed test, use runner collection, listing, or focused execution output to confirm that the intended command selects it. Account for focus, skip, todo, tag, feature, and exclusion markers; a green suite does not prove an unseen test ran.

Then run the repository's required type checks, linters, and full test suite once the change is complete. When order, concurrency, retry, or shared state matters, also repeat the test under the relevant seed, order, worker count, or scheduler.

Use coverage to locate unexercised risk, not as a target by itself. Use mutation testing on changed or risk-bearing code when the tool exists and survivors can become concrete test goals. Investigate small score changes and flaky results before drawing conclusions.

**Complete when:** new and renamed tests are collected, the intended test command and project validation are green, relevant nondeterminism has been stressed, and failures leave enough context to reproduce.

## Review checklist

- [ ] The test names an observable contract and plausible failure.
- [ ] The chosen surface is the narrowest one that contains the risk.
- [ ] The oracle is independent of the implementation.
- [ ] New and renamed tests are collected by the intended command.
- [ ] The test avoids private state and incidental call choreography.
- [ ] The strongest safe discrimination proof was exercised, or its limitation was recorded.
- [ ] Time, randomness, concurrency, external responses, and durable state are controlled where relevant.
- [ ] Coverage, mutation, retries, and snapshots support a decision rather than replace one.
- [ ] The test remains useful after an internal refactor that preserves behavior.
