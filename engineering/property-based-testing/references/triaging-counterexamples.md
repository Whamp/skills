# Triaging counterexamples

A failing property proves a discrepancy among the system, property, generator, oracle, and environment. Classify that discrepancy before editing production code.

## 1. Capture the failure

Record the shrunk input or command sequence, original failure when available, seed and replay path, framework and version, exact command, platform, and relevant configuration. Preserve the first failure output before reruns overwrite a failure database or corpus.

**Complete when:** another run has enough information to attempt the exact case under the same environment.

## 2. Replay the shrunk case

Use the framework's native replay mechanism first. Repeat the minimized case enough to distinguish a deterministic discrepancy from timing, shared state, mutation of generated values, or another environmental effect.

**Complete when:** the case reproduces consistently or the varying environmental factor is named.

## 3. Re-ground the quantified contract

Verify each part of the property against owned sources:

1. external specification and public API documentation
2. explicit product decisions and compatibility commitments
3. types, validation, callers, and established tests
4. names and nearby conventions as leads requiring confirmation

Check that the input belongs to the claimed domain, the precondition held, the oracle is independent, and the equivalence relation matches the contract. Platform-specific behavior is a defect when the platform lies inside the supported contract; report the platform as part of the evidence.

**Complete when:** the domain, precondition, relation, and equivalence are either sourced or identified as ambiguous.

## 4. Classify the discrepancy

| Class | Evidence | Next action |
| --- | --- | --- |
| System defect | Supported input violates a grounded relation | Fix production code and retain the property |
| Property defect | Asserted relation is not required | Correct or remove the property |
| Generator defect | Input is outside the claimed domain or misses required structure | Repair generation and validate it independently |
| Oracle or model defect | Reference behavior is wrong or shares the decisive bug | Repair or replace the oracle |
| Shrink or replay artifact | Reported case changed through mutation, invalid shrinking, or version-sensitive replay | Fix test mechanics and recapture |
| Flaky environment | Outcome depends on state, time, schedule, platform setup, or cleanup | Isolate the factor and add deterministic control |
| Ambiguous contract | Owned sources do not decide expected behavior | Ask for a product decision and record it |

## 5. Isolate the cause

Read the smallest causal execution, not only the smallest input. For stateful failures, identify the first command after which model and system diverge. For numeric failures, inspect units, overflow, exceptional values, and the chosen tolerance. For round trips, determine which direction and which equivalence failed.

Use manual simplification only after native shrinking, and confirm that simplification preserves the same cause.

**Complete when:** the report names the first violated relation and the smallest known causal setup.

## 6. Preserve the regression

Keep the general property. Add an explicit example when the minimized case is stable, contractual, and more legible than replay metadata. Treat version-sensitive replay blobs and transient seeds as diagnostic aids rather than the only permanent regression.

A useful report contains:

```text
Property:
Quantified domain and precondition:
Minimal counterexample or command sequence:
Expected relation and source:
Observed result:
Framework replay data:
Environment:
Classification:
First causal divergence:
```

## Completion criterion

Triage is complete when the exact case is replayable, every component of the discrepancy is checked, one classification is supported by evidence, the first causal divergence is identified, and the durable property or regression reproduces before the fix and passes after it.
