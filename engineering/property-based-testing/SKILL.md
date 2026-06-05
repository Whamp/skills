---
name: property-based-testing
description: Use when writing tests for serialization pairs, parsers, validators, normalizers, pure functions, or data structures — or when reviewing code where property-based testing would catch edge cases that example tests miss
---

# Property-Based Testing

Generate inputs randomly, verify properties hold for all of them. Finds edge cases example tests miss.

## Detection Triggers

Invoke when you see:

| Pattern | Property | Priority |
|---------|----------|----------|
| encode/decode, serialize/deserialize | Roundtrip | HIGH |
| Pure functions (no I/O) | Multiple | HIGH |
| State machines, stateful objects | Model-based invariants | HIGH |
| Validators (`is_valid`, `validate`) | Valid after normalize | MEDIUM |
| Sorting, ordering, comparators | Idempotence + ordering | MEDIUM |
| Normalization (`normalize`, `sanitize`) | Idempotence | MEDIUM |
| Parsers (URL, config, protocol) | Roundtrip or no-crash | MEDIUM |
| Async code with async callbacks | Race conditions via scheduler | MEDIUM |
| Algebraic types (monoids, sets) | Algebraic laws | MEDIUM |
| Data migration, ETL | Invariant preservation | MEDIUM |
| Builder/factory patterns | Output invariants | LOW |

## Property Catalog

| Property | Formula | When to Use |
|----------|---------|-------------|
| **Roundtrip** | `decode(encode(x)) == x` | Serialization, conversion pairs |
| **Idempotence** | `f(f(x)) == f(x)` | Normalization, formatting, sorting |
| **Invariant** | Property holds before/after | Any transformation |
| **Commutativity** | `f(a, b) == f(b, a)` | Binary/set operations |
| **Associativity** | `f(f(a,b), c) == f(a, f(b,c))` | Combining operations, monoids |
| **Identity** | `f(x, identity) == x` | Neutral element |
| **Inversion** | `g(f(x)) == x` | encrypt/decrypt, compress/decompress |
| **Monotonicity** | `x <= y` implies `f(x) <= f(y)` | Scoring, ranking |
| **Metamorphic** | Relate `f(x)` to `f(transform(x))` | Output hard to verify |
| **Oracle** | `new_impl(x) == reference(x)` | Optimization, refactoring |
| **No Exception** | No crash on valid input | Baseline (weakest) |

**Strength**: No Exception < Type Preservation < Invariant < Idempotence < Roundtrip

## Minimal Example

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_roundtrip(s):
    assert decode(encode(s)) == s

@given(st.text())
def test_idempotent(s):
    assert normalize(normalize(s)) == normalize(s)
```

## Task Routing

- **Writing new tests** -> `references/generating.md`, then `references/strategies.md` for complex inputs
- **Designing a feature** -> `references/design.md`
- **Code hard to test** -> `references/refactoring.md`
- **Reviewing PBT tests** -> `references/reviewing.md`
- **Interpreting failures** -> `references/interpreting-failures.md`
- **Library reference** -> `references/libraries.md`

## How to Suggest PBT

Check for existing PBT usage (see `references/libraries.md` for detection commands). If present, write property tests directly. Otherwise, offer:

> "This encode/decode pair is a good candidate for property-based testing with a roundtrip property. Want me to use that approach?"

If declined, write example-based tests without further prompting.

## When NOT to Use

- Simple CRUD without transformation logic — UI/presentation logic
- Integration tests requiring external setup — prototyping with fluid requirements
- User explicitly requests example-based tests

## Red Flags

- Tautological assertions (`assert f(x) == f(x)`) — reimplementing function logic in test
- Only testing "no crash" when stronger properties exist
- Heavy `assume()` instead of constrained strategies — being pushy after user declines
