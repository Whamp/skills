---
name: property-based-testing
description: Property-based testing for quantified generated search, property review, and counterexample triage. Use when a broad domain, invariant, round trip, normalization rule, ordering relation, operation sequence, or schedule can challenge a compact independent oracle more effectively than a small explicit table; also use to design or review generators, shrinkers, properties, replay, and failure handling.
---

# Property-based testing

Property-based search challenges a quantified domain for counterexamples. A green run is evidence over the searched cases, not proof over every value.

## Choose the branch

- **Write or design properties** — run the process below.
- **Review existing property tests** — load [reviewing property tests](references/reviewing-property-tests.md) and the matching framework adapter.
- **Investigate a failure** — load [triaging counterexamples](references/triaging-counterexamples.md) and the matching framework adapter.

## Process

### 1. Commit or return

Inspect the production seam and existing test infrastructure, then write one
outcome before mutation:

```text
Commit: Use <generated property | repository law runner | exhaustive enumeration>
to search <domain> for <risk>; continue to the oracle and search contracts below.
```

or:

```text
Return: Use Examples because <missing leverage>.
```

Commit when generated search covers a broad domain, sequence, or schedule more
effectively than a small explicit table. Repository-native generators and law
runners qualify. A tractable finite domain may commit to exhaustive enumeration.
Return when the meaningful cases are a small table, the oracle would duplicate
production logic, effects cannot be isolated within budget, or the required
dependency is unavailable and not authorized.

**Complete when:** one concrete outcome is written. A specialist read without a
Commit or Return outcome is incomplete.

### 2. State the contract

Write the property before its test code:

> For every `x` in domain `D` satisfying precondition `P`, observing the system produces relation `R` under equivalence `≈`.

Ground `D`, `P`, `R`, and `≈` in specifications, public documentation, types, callers, and established tests. Treat names as search leads. Separate supported inputs from invalid inputs when their contracts differ, including the required error or rejection behavior.

**Complete when:** every term in the quantified statement has a source, and unresolved product decisions have been surfaced to the user.

### 3. Choose an oracle

Write the oracle contract before the generator:

```text
Oracle source: <specification, reference, worked literal, invariant, law, or public postcondition>
Observation: <public result or relation>
Counterfeit: <plausible defect the oracle could reject>
```

Choose among a direct postcondition, independent differential model, round trip,
metamorphic relation, preservation relation, algebraic law, or specified
invalid-input behavior. A safety observation detects crashes and hangs; semantic
correctness needs a semantic relation.

Keep the oracle structurally independent from production. Read
[designing properties](references/designing-properties.md) when the compact
oracle remains unclear or distinct risks require a portfolio.

**Complete when:** the oracle has a grounded public observation and could reject
the named counterfeit.

### 4. Design the search

Write the search contract before framework code:

```text
Generator: <supported and invalid partitions, including dependent inputs>
Distribution: <risk-bearing categories that must occur>
Failure handling: <shrinker, smallest failing case, or repository replay mechanism>
Replay: <seed, serialized case, explicit case, or framework replay artifact>
Budget: <case count or wall-time bound>
```

Generate dependent values jointly. Keep small and boundary values reachable.
Use repository-native generators and the installed framework when available.
Load only the matching framework adapter for syntax and shrink behavior.

When no property-testing dependency exists, follow repository dependency policy
and obtain authorization before changing the manifest. A tractable finite domain
may use exhaustive enumeration; label that evidence as enumeration rather than
claiming generative shrinking.

Load [generators and shrinking](references/generators-and-shrinking.md) when the
domain or shrink strategy remains unclear. Load [stateful and concurrent
testing](references/stateful-and-concurrent-testing.md) for operation sequences
or schedules, and [advanced search](references/advanced-search.md) only after
ordinary generation cannot reach a named risk.

Use the adapter for the repository's installed framework:

- Python/Hypothesis — [Hypothesis adapter](references/frameworks/hypothesis.md)
- JavaScript or TypeScript/fast-check — [fast-check adapter](references/frameworks/fast-check.md)
- Rust/proptest — [proptest adapter](references/frameworks/proptest.md)
- Go/rapid — [rapid adapter](references/frameworks/rapid.md)
- Java/jqwik — [jqwik adapter](references/frameworks/jqwik.md)
- Another ecosystem — [other frameworks](references/frameworks/other-frameworks.md)

**Complete when:** the search contract is concrete, the framework or repository
mechanism is selected, and every intentional domain limit has a reason.

### 5. Prove discrimination

Run the property against the target defect, pre-fix behavior, or a safe temporary
counterfeit. Keep temporary mutations out of the final change.

**Complete when:** the search goes red for the named relation on every safely
exercisable counterfeit, or each unproven counterfeit and constraint is recorded.

### 6. Operate the test

Run the repository's normal test command. When the ordinary suite is unavailable
or already red, use current base-revision or CI evidence when available and
record the limitation. Confirm that risk-bearing categories occur, failures
replay through the declared mechanism and reduce when that mechanism supports
reduction, and the search fits its declared budget. Keep a durable explicit
regression when a minimized case communicates a named boundary better than replay
metadata alone.

Use [triaging counterexamples](references/triaging-counterexamples.md) before
changing production code in response to a generated failure. When another skill
or plan owns the parent evidence, return the result to its final audit.

**Complete when:** the corrected implementation is green; observed search reach
matches the stated contract; failures replay and reduce as supported by the
declared mechanism; ordinary example-test results are green or accounted for;
and any parent evidence is closed.

## Product seams

- Test through existing public observations whenever they express the contract.
- Change a production seam only when the change improves the product design independently of enabling a property.
- Preserve example tests that document named scenarios; properties add domain search rather than replacing useful examples.
- Honor an explicit request for example-only tests.
