---
name: testing
description: Testing strategy and explicit behavioral evidence. Use for selecting test seams and levels, writing regression, unit, integration, contract, or browser tests, proving fixes, reviewing tests, diagnosing flakes, and interpreting coverage or mutation results. Use it to map plausible failures to explicit examples, property-based testing, or fuzzing after inspecting the relevant code and tests.
---

# Testing

Build the smallest executable argument that can disagree with a wrong implementation. A passing test matters only when its setup, observation, and oracle can expose the named risk.

## Route after inspecting the seam

Inspect the requested contract, relevant production code, types, callers, and
existing tests before selecting evidence. Group coupled claims when shared state,
ordering, composition, propagation, or lifecycle could make their interaction
fail.

Choose an evidence route for each plausible failure or interaction:

| Evidence route | Use when |
| --- | --- |
| **Examples** | The meaningful cases are enumerable, the expected result is still unclear, repository tooling is unavailable, or no executable generated campaign is intended. Continue with this skill. |
| **Property-based testing** | Generate many structured inputs, operation sequences, or schedules to find combinations and edge cases that selected examples may miss. Load `property-based-testing` when you can name the domain, risk, independent check of expected behavior, available repository runner, and executable property. |
| **Fuzzing** | Mutate inputs with coverage feedback to discover paths and failures that selected examples may miss. Load `fuzzing` when you can name a reachable production input seam, risk, observable failure check, supported engine, and bounded executable campaign. |

Specialist guidance explains how to run a generated search; the executable
property or campaign supplies the evidence. Keep examples for named boundaries
and minimized regressions. Load both specialist skills when separate risks
qualify for each route.

Load branch-specific guidance when its matching dimension applies:

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

**Complete when:** each plausible failure has an evidence route, each identified
interaction is covered, and every specialist load has an executable plan or the
missing information needed to choose is named.

## 1. Inventory and frame the contract

Build a compact contract inventory:

```text
Contract: <requested claim or coupled claims>
Preservation: <source-grounded adjacent behavior, or none>
Interaction: <shared state, ordering, composition, propagation, or lifecycle risk, or none>
Observation: <public surface where the behavior is visible>
Risk: <plausible failure>
Oracle and counterfeit: <independent expected result and wrong behavior it rejects>
Evidence route: <examples, generated search, existing evidence, or unverified>
```

Group coupled claims when shared evidence can discriminate their composition.
Keep independent claims separate. Several entries may share one evidence route,
and an inventory entry does not require a new test file.

Ground the inventory in specifications, public documentation, types, callers,
accepted behavior, and existing tests. Treat names and comments as search leads,
not proof. Confirm any production-interface or scope-expanding seam before adding
it.

**Complete when:** every requested claim and grounded preservation risk maps to
discriminating evidence or is marked unverified with the missing evidence named,
and every identified interaction risk is covered explicitly.

## 2. Choose the smallest discriminating surface

Place the test at the narrowest surface that still contains the risk:

- use an example test for a small set of named cases
- cross a real boundary when serialization, schema, configuration, lifecycle, or protocol behavior is the risk
- use a browser only when browser behavior or cross-system wiring is part of the claim
- use generated search only when a broad domain and compact oracle create leverage

Choose real dependencies and test doubles by what the test must detect. A fake is appropriate when it preserves the contract under test and removes an unrelated, destructive, unavailable, or prohibitively expensive dependency. A real dependency is required when its actual behavior is the risk.

Narrow evidence may localize a fault, but it does not discharge a contract when
representation, wiring, lifecycle, serialization, or user-visible behavior
through an outer boundary is the named risk. In that case, exercise an exact
journey and assert the specific boundary value or effect; reaching the surface is
not evidence by itself. The observation surface determines where evidence must
observe behavior, not where the implementation belongs. Broaden a shared or
global production seam only with independent support from source, types, or
callers.

**Complete when:** a narrower surface would miss the named risk, every replaced
dependency has an explicit realism tradeoff, the journey rejects the named
boundary counterfeit, and any broadened seam has support beyond the observation
path.

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
