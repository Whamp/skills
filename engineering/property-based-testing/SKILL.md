---
name: property-based-testing
description: Property-based testing for implementation and test work with broad structured behavior. Use when a feature or bug spans input combinations, round trips, encoding and decoding, serialization, normalization or idempotence, ordering or pagination, schema variants, stateful operation sequences, distributed or concurrent schedules, parsers or codecs with semantic invariants, or differential models; also use when designing or reviewing generators, shrinkers, properties, and counterexample handling.
---

# Property-based testing

A property test searches a quantified domain for a counterexample and shrinks failures. A green run is evidence over the searched cases, not proof over every value.

## Choose the branch

- **Write or design properties** — run the process below.
- **Review existing property tests** — load [reviewing property tests](references/reviewing-property-tests.md) and the matching framework adapter.
- **Investigate a failure** — load [triaging counterexamples](references/triaging-counterexamples.md) and the matching framework adapter.

## Process

### 1. Establish leverage

Use property-based testing when a broad or structured domain, operation sequence, or schedule can challenge a compact oracle. Prefer example tests when the meaningful cases are a small explicit table, the only oracle would duplicate the implementation, or effects cannot be isolated within the test budget.

Write the candidate in this form:

> Generate **[domain]** to challenge **[risk]**, checked by **[oracle]**.

**Complete when:** all three blanks are concrete. If the oracle blank remains vague, use examples or first clarify the contract.

### 2. State the contract

Write the property before its test code:

> For every `x` in domain `D` satisfying precondition `P`, observing the system produces relation `R` under equivalence `≈`.

Ground `D`, `P`, `R`, and `≈` in specifications, public documentation, types, callers, and established tests. Treat names as search leads. Separate supported inputs from invalid inputs when their contracts differ, including the required error or rejection behavior.

**Complete when:** every term in the quantified statement has a source, and unresolved product decisions have been surfaced to the user.

### 3. Choose an oracle

Load [designing properties](references/designing-properties.md). Choose the simplest observation independent enough to catch a plausible faulty implementation. For each proposed property, name the **counterfeit** implementation or bug class it should reject. Build a portfolio only when distinct risks need distinct observations; property count is not a quality target.

**Complete when:** every property has a grounded contract, an observable oracle, and at least one named counterfeit it should reject.

### 4. Design the search

Load [generators and shrinking](references/generators-and-shrinking.md) and the adapter for the repository's installed framework:

- Python/Hypothesis — [Hypothesis adapter](references/frameworks/hypothesis.md)
- JavaScript or TypeScript/fast-check — [fast-check adapter](references/frameworks/fast-check.md)
- Rust/proptest — [proptest adapter](references/frameworks/proptest.md)
- Go/rapid — [rapid adapter](references/frameworks/rapid.md)
- Java/jqwik — [jqwik adapter](references/frameworks/jqwik.md)
- Another ecosystem — [other frameworks](references/frameworks/other-frameworks.md)

Use the existing dependency and project test conventions. When no property-testing dependency exists, follow the repository's dependency policy; if adding one is not already authorized, present the leverage sentence before changing the manifest.

For state or operation sequences, also load [stateful and concurrent testing](references/stateful-and-concurrent-testing.md). When ordinary generation cannot reach the risk-bearing cases, load [advanced search](references/advanced-search.md).

**Complete when:** the full supported domain is reachable in principle or each deliberate scope limit is justified by measured cost; dependent inputs are generated jointly; risk-bearing categories are observed; and failures can shrink to replayable cases.

### 5. Prove discrimination

Run the property against the target defect, the pre-fix implementation, or a temporary plausible mutant. A green property against its named counterfeit has not yet earned confidence. Keep mutations local and out of the final change.

**Complete when:** the property set goes red on the target defect and on every named counterfeit that can be safely simulated; record any unproven counterfeit.

### 6. Operate the test

Run the repository's normal test command. Keep the suite's existing settings first, then adjust search effort from measured runtime and observed reach. Preserve exact replay data for failures and use [triaging counterexamples](references/triaging-counterexamples.md) before changing production code.

Keep a durable explicit example when a minimized case communicates a named boundary or regression better than replay metadata alone; retain the general property too.

**Complete when:** the corrected implementation is green, the search fits the intended suite budget, the failure is replayable, and the ordinary example-based tests still pass.

## Product seams

- Test through existing public observations whenever they express the contract.
- Change a production seam only when the change improves the product design independently of enabling a property.
- Preserve example tests that document named scenarios; properties add domain search rather than replacing useful examples.
- Honor an explicit request for example-only tests.
