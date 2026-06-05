# Reviewing Property-Based Tests

Evaluate quality of existing property-based tests and suggest improvements.

## Quick Reference

| Issue | Severity | Detection | Fix |
|-------|----------|-----------|-----|
| Tautological | CRITICAL | Assertion compares same expression | Rewrite with actual property |
| Vacuous | CRITICAL | Contradictory `assume()` calls | Remove or fix filters |
| Weak (no assertion) | HIGH | Test body has no assert | Add meaningful assertion |
| Reimplementation | HIGH | Assertion mirrors function logic | Use algebraic property instead |
| Over-filtered | MEDIUM | Many `assume()` calls | Redesign strategy |
| Missing edge cases | MEDIUM | No `@example` decorators | Add explicit edge cases |
| Poor shrinking | MEDIUM | Complex strategies, `filter` chains | Simplify for better shrinking |
| Poor settings | LOW | Missing or bad `@settings` | Add appropriate settings |

## Quality Issues

### Issue: Tautological Properties (CRITICAL)

Properties that are always true regardless of implementation.

```python
# BAD - compares function to itself
@given(st.lists(st.integers()))
def test_sort_tautology(xs):
    assert sorted(xs) == sorted(xs)  # Always true!

# BAD - tests nothing about the function
@given(st.integers())
def test_useless(x):
    result = compute(x)
    assert result == result  # Always true!
```

### Issue: Vacuous Tests (CRITICAL)

Tests where assumptions filter out most/all inputs.

```python
# VACUOUS - impossible condition
@given(st.integers())
def test_vacuous(x):
    assume(x > 100)
    assume(x < 50)  # Impossible!
    assert compute(x) > 0
```

**Detection**: Multiple `assume()` calls, `assume` with very narrow conditions. Target filter rejection rate < 10%.

### Issue: Reimplementing the Function (HIGH)

```python
# BAD - just reimplements the logic
@given(st.integers(), st.integers())
def test_reimplements(a, b):
    assert add(a, b) == a + b  # Tests nothing if add() is just a + b

# GOOD - tests algebraic properties instead
@given(st.integers())
def test_add_identity(a):
    assert add(a, 0) == a

@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    assert add(a, b) == add(b, a)
```

### Issue: Missing Stronger Properties (MEDIUM)

```python
# EXISTS - but could be stronger
@given(st.lists(st.integers()))
def test_sort_length(xs):
    assert len(sort(xs)) == len(xs)
# MISSING: ordering property, element preservation, idempotence
```

**Do** check the property catalog in SKILL.md — are stronger properties available but not tested?

## Review Process

### 1. Locate Property-Based Tests

```bash
# Python/Hypothesis
rg "@given\(" --type py

# JavaScript/fast-check
rg "fc\.(assert|property)|it\.prop" --type js --type ts

# Rust/proptest
rg "proptest!" --type rust

# Go/rapid
rg "rapid\.Check" --type go
```

### 2. Analyze Each Test

Check for issues above, starting with CRITICAL then HIGH severity.

### 3. Evaluate Shrinking Quality

Will tests shrink to minimal counterexamples? Red flags:
- Heavy use of `filter()` / `assume()` (rejects shrink candidates)
- Complex custom generators without shrink support
- Strategies built from `map(hash_function)` (non-invertible, can't shrink through)

### 4. Check for Flakiness Potential

- Non-determinism in code under test
- Time-dependent assertions
- Global state dependencies
- Floating point comparisons without tolerance

### 5. Suggest Stronger Properties

Compare against the property catalog — are stronger properties available but not tested?

## Test Health Score

| Category | Score | What to Check |
|----------|-------|---------------|
| Property Strength | X/5 | Roundtrip > Idempotence > Type > No crash |
| Input Coverage | X/5 | Edge cases, strategy breadth |
| Assertions | X/5 | Meaningful, not tautological |
| Settings | X/5 | Appropriate for context |

## Mutation Testing Verification

Suggest specific mutations to verify tests catch bugs:

```
To verify test_sort catches bugs:

1. Return input unchanged: `return xs`
   - Should fail: test_ordering

2. Drop last element: `return sorted(xs)[:-1]`
   - Should fail: test_length_preserved

3. Reverse order: `return sorted(xs, reverse=True)`
   - Should fail: test_ordering
```

**Do** propose 2-3 mutations per tested function. If any mutation survives all properties, the test suite has a gap.

## Quality Checklist

For each test, verify:
- [ ] Not tautological (assertion doesn't compare same expression)
- [ ] Strong assertion (not just "no crash")
- [ ] Not vacuous (inputs not over-filtered)
- [ ] Good coverage (edge cases via `@example`)
- [ ] No reimplementation of function logic
- [ ] Appropriate settings for context
- [ ] Good shrinking potential (minimal `filter`/`assume` usage)
- [ ] Deterministic (no flakiness risk)

## Red Flags

- **Marking tautologies as "fine"**: `assert x == x` is NEVER a valid test
- **Accepting "no crash" as sufficient**: Always push for stronger properties
- **Ignoring vacuous tests**: Tests with contradictory `assume()` provide false confidence
- **Not checking for reimplementation**: `assert add(a,b) == a + b` tests nothing if that's how `add` is implemented
