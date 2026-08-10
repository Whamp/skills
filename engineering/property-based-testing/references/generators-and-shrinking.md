# Generators and shrinking

A property test has three related search surfaces:

- **Domain** — values the generator can produce
- **Distribution** — values the engine tends to try under a budget
- **Shrink path** — simpler candidates the engine can reach after failure

The generator and precondition define the quantified domain. The assertion and oracle define the expected relation.

## 1. Define the domain

Start from the supported contract, not a sample of production-looking data. Keep every supported value reachable in principle. Add size or complexity bounds only when they are contractual or measured execution cost requires them.

Create separate generators for materially different contracts:

- supported values expected to succeed
- invalid values expected to be rejected
- legacy or compatibility representations
- resource-limit cases expected to stop safely

For a sparse constrained domain, generate correct values by construction or derive them from an independent specification. Rejection sampling is suitable when valid values remain common and shrinking stays useful.

Construct inputs independently of the system under test. If setup must call the same API being tested, validate the setup result through another observation so one bug cannot corrupt both the generated domain and the assertion.

## 2. Generate dependencies jointly

Model relationships directly instead of generating independent values and hoping assumptions connect them. Examples:

- `(lower, upper)` with `lower <= upper`
- a collection paired with a key known to be present or absent
- a graph paired with a reachable node
- a state paired with a legal next command
- a buffer paired with a valid slice range

Dependent generation improves valid-case density and preserves relationships during shrinking. It also exposes collisions and aliasing that independent wide ranges can make vanishingly rare.

## 3. Treat size as a search budget

Size controls cost, shape, and interaction probability; it is not a proxy for realism.

- Preserve small values because they diagnose and often expose boundary defects.
- Reach larger values when depth, overflow, complexity, or interaction count is a named risk.
- Prefer a focused generator over globally increasing all sizes.
- Use exhaustive generation for a tractable finite domain when the framework supports it.

Measure before narrowing the domain. A smaller run count over a broad domain can be more useful than many cases from a weakened domain.

## 4. Observe the distribution

Name categories tied to the risk and collect them with the framework's event, classification, statistics, or coverage API. Typical categories include:

- empty, singleton, and multi-element shapes
- boundaries and values adjacent to them
- duplicates, collisions, aliases, and shared references
- valid, invalid, and partially valid inputs
- recursive depth and branching shape
- each command and important state transition
- success, rejection, and each error family

Set a coverage threshold only when the category has a justified minimum under the configured budget. Otherwise inspect the statistics and redesign generation when a critical category is absent. A realistic frequency is optional; a bug-finding frequency is the goal.

Explicit examples are useful for named contractual boundaries and durable regressions. They are not a substitute for checking the generated domain, and their absence is not itself a defect.

## 5. Preserve shrinking

Use the framework's native combinators so generation and shrinking stay coupled. Filtering, mapping, flat-mapping, and mutable test inputs have different shrink behavior across frameworks; follow the matching adapter.

Validate custom search machinery:

- Every generated valid value satisfies the generator's claimed invariant.
- Every generated invalid value violates the intended rule rather than an unrelated one.
- Shrunk counterexamples remain in the claimed domain where the framework promises that behavior.
- A planted failing predicate shrinks to a stable, intelligible case.

Use the framework shrinker first. When the result remains noisy, inspect the generator composition and shrink semantics before manually simplifying the example.

## 6. Calibrate execution

Begin with repository defaults. Measure per-case cost, total suite time, discarded cases, category reach, and shrink time before changing settings.

Use separate profiles only when the project benefits from distinct loops, such as a tight presubmit search and a longer scheduled search. Preserve replay metadata in every profile. A higher case count compensates for neither a weak oracle nor an unreachable fault condition.

When ordinary generation cannot reach a risk-bearing category within the budget, use [advanced search](advanced-search.md).

## Completion criterion

Generator design is complete when the claimed domain is reachable, every dependency is represented in generation, every material category has observed evidence, custom generation preserves its invariants, a planted failure shrinks intelligibly, and measured runtime fits the intended test loop.
