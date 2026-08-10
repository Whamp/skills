# Designing properties

A useful property combines a grounded contract with an oracle that rejects realistic counterfeits. Property names such as “round trip” or “invariant” identify shapes, not strength.

## Quality axes

Evaluate a property on five independent axes:

- **Grounding** — the relation follows from an owned contract.
- **Independence** — the oracle does not share the decisive logic or misconception with the system under test.
- **Discrimination** — a plausible wrong implementation makes the property fail.
- **Reach** — the generated domain can exercise the fault conditions.
- **Diagnosis** — failures shrink to an example that explains the violated relation.

A property can be broad but weak, narrow but decisive, or complete for one contract and silent about another. Build a portfolio around risks, not a universal ranking.

## Oracle patterns

### Postcondition or verifier

Check an output more cheaply and independently than producing it.

For sorting, ordering and multiset preservation together specify the result more strongly than length alone. For a solver, verify that the returned witness satisfies every constraint. For a parser, validate source spans, tree invariants, or consumption of the intended input.

Use a verifier when constructing a correct result is hard but checking one is simple.

### Differential or model oracle

Compare the system with a smaller reference model, established implementation, alternate algorithm, or specification interpreter:

```text
normalize_optimized(x) ≈ normalize_reference(x)
```

Independence matters more than implementation size. A language builtin can be an excellent oracle for a wrapper whose contract intentionally matches it. A copied algorithm or shared decisive helper can preserve the same bug on both sides.

For a new implementation replacing an old one, decide whether compatibility or the written specification wins when they disagree.

### Round trip and canonicalization

Choose the direction and equivalence explicitly.

For semantic values:

```text
decode(encode(value)) ≈ value
```

For accepted representations:

```text
encode(decode(representation)) == canonicalize(representation)
```

Generate both domains when both directions matter: encoder output may cover only a canonical subset of what the decoder accepts. Use semantic equivalence for representations with insignificant ordering, whitespace, aliases, lossy fields, normalization, or multiple valid encodings. Add an independent format invariant or alternate implementation when both directions share code and could agree on the same mistake.

### Metamorphic relation

Relate observations before and after a controlled input transformation when no direct oracle is cheap:

```text
observe(f(transform(x))) ≈ transform_observation(observe(f(x)))
```

Examples include permutation invariance, translation or scale relations, adding irrelevant data, and decomposing then recombining work. Ground the transformation in the contract; a plausible-sounding symmetry is not automatically required behavior.

### Preservation invariant

Check what an operation must preserve while changing something else: ownership, element multiplicity, conservation totals, tree ordering, referential integrity, permissions, or schema compatibility.

Pair preservation with an observation of intended change. “Length is preserved” alone admits permutations, corruption, and replacement with repeated defaults.

### Algebraic law

Commutativity, associativity, identity, absorption, and idempotence are valuable when the abstraction promises them. Confirm the law for the actual type and equivalence relation. Floating-point arithmetic, ordered collections, side effects, overflow, and error accumulation often invalidate textbook laws.

Combine algebraic laws with postconditions when degenerate implementations can satisfy the law. A function that always returns a constant may be idempotent and commutative.

### Invalid-input and error contract

Search the complement of the valid domain when rejection behavior is part of the API. Assert the relevant exception, error value, status, diagnostic location, rollback, or lack of partial mutation. Generate varied invalid inputs rather than one malformed constant.

“No crash” is complete when availability over arbitrary untrusted input is the contract. When accepted results carry stronger promises, pair robustness with those postconditions.

### Inductive or decomposition property

Specify a base case and how behavior changes under constructors or smaller subproblems:

```text
f(empty) == base
f(insert(x, xs)) relates to x and f(xs)
```

Check that the constructors can represent every value in the claimed domain. Otherwise the induction specifies only a subset.

### Stateful model

When correctness depends on history, a single-call property cannot express the contract. Use commands, model transitions, postconditions, and invariants from [stateful and concurrent testing](stateful-and-concurrent-testing.md).

## Equivalence

Define `≈` beside the property:

- Structural equality for exact representations
- Semantic equality for alternate valid forms
- Multiset equality when order is irrelevant but multiplicity matters
- Domain identity such as normalized keys or case folding
- Absolute and relative tolerances with explicit units for numeric approximation

An undefined equivalence turns round trips and differential tests into ambiguous bug reports.

## Counterfeit check

For each assertion, write one implementation that should fail. Useful counterfeits include:

- Return the input unchanged
- Return a constant or empty value
- Drop, duplicate, or reorder one element
- Accept every invalid input or reject every valid input
- Skip one state transition
- Use the wrong boundary comparison
- Preserve a stale cache or mutate before validation

If a counterfeit survives, strengthen the observation or acknowledge that the property does not cover that risk.

## Completion criterion

Property design is complete when every claimed contract has an explicit domain, precondition, relation, equivalence, source, and named counterfeit; together the chosen properties cover the task's material risks without relying on duplicated decisive logic.
