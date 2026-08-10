# Reviewing property-based tests

Review each property as a counterexample search system: contract, oracle, domain, distribution, shrinking, replay, and operating budget.

## Review process

### 1. Inventory the searches

Find the property framework in manifests, test configuration, and imports. Read the matching adapter and the production contract each test claims to exercise. Group tests by contract rather than by decorator or macro.

**Complete when:** every property test in scope is mapped to a named production contract and framework configuration.

### 2. Apply every criterion

| Criterion | Question | Evidence |
| --- | --- | --- |
| Grounding | Is the relation required for the generated domain? | Specification, docs, types, callers, established tests |
| Oracle | Is the decisive observation independent and semantically correct? | Reference/model implementation and equivalence definition |
| Discrimination | Which plausible counterfeit does the property reject? | Pre-fix failure, mutation result, or demonstrated counterexample |
| Domain | Can every supported value relevant to the claim be generated? | Generator construction and bounds |
| Dependencies | Are related inputs, state, and commands generated jointly? | Composite, flat-map, bundle, or command model |
| Distribution | Do risk-bearing categories actually occur? | Events, classifications, statistics, or sampled evidence |
| Shrinking | Can failures reduce while preserving their cause and domain? | A planted failure or recorded shrink trace |
| Replay | Can another run reproduce the minimized case? | Seed, path, failure database, corpus, or explicit example |
| Isolation | Are generated values, state, clocks, and schedules controlled? | Setup, cleanup, copying, deterministic scheduler |
| Budget | Does the search fit its intended loop without weakening the domain? | Measured runtime, discards, and configured profiles |

**Complete when:** every test has evidence or an explicit gap for every applicable criterion.

### 3. Test discrimination

Map each assertion to a plausible counterfeit. Use the target defect, a mutation tool, or a temporary local mutation such as:

- wrong boundary comparison
- dropped or duplicated element
- constant or identity result
- skipped state transition
- unconditional acceptance or rejection
- stale cached value

A surviving counterfeit is a precise coverage gap. Remove temporary mutations before reporting.

**Complete when:** every material assertion has a mutation result or is labeled unproven.

### 4. Avoid mechanical findings

Judge behavior rather than syntax:

- A direct comparison with a language builtin can be a valid differential oracle.
- A robustness property can be complete for a no-crash contract.
- Explicit examples are optional when generation already reaches the boundary; they are valuable for named regressions.
- Filtering is acceptable when valid cases remain common and shrinking stays useful.
- A low run count can be effective for a discriminating property; a high count cannot rescue a weak oracle.
- Type assertions are meaningful only when runtime type behavior is part of the contract.

### 5. Report findings

For each actionable gap, report:

```text
Property and location:
Claimed contract:
Missing or misleading evidence:
Surviving counterfeit or unreachable category:
Consequence:
Smallest corrective action:
```

Separate system defects found by the tests from defects in the property tests themselves. Prefer evidence-backed findings over a scalar health score.

## Completion criterion

The review is complete when every in-scope property is accounted for across all applicable criteria, every finding names observable consequence and source evidence, mutation survivors and search blind spots are explicit, and proposed changes preserve useful existing coverage.
