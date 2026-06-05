# Interpreting Property-Based Test Failures

How to analyze failures and determine if they represent genuine bugs.

## The Self-Reflection Problem

Property-based testing generates many failing examples. Not all failures are bugs:
- **Test bugs**: Property is wrong, strategy generates invalid inputs
- **Ambiguous specs**: Behavior undefined for edge cases
- **Genuine bugs**: Code violates documented guarantees

Before reporting a bug, **validate the failure** through systematic analysis.

## Failure Analysis Workflow

### 1. Reproduce with Minimal Example

Start with the shrunk failing input from the test output.

```python
# Hypothesis provides the minimal failing case
# Falsifying example: test_normalize(s='\x00')

# Create standalone reproducer
def test_reproduce():
    s = '\x00'
    result = normalize(normalize(s))
    assert result == normalize(s)  # Fails
```

**Do** verify the failure is consistent, not flaky.

**Do** use `@reproduce_failure` (Hypothesis) or `--hypothesis-seed` to pin the exact case.

### 2. Ground the Property

Before assuming a bug, verify your property against authoritative sources:

| Source | What It Tells You |
|--------|-------------------|
| **Type annotations** | Return type constraints, nullability |
| **Docstrings** | Explicit guarantees, preconditions |
| **Function name** | Semantic expectations (e.g., `sort` implies ordering) |
| **Error handling** | What inputs should raise vs handle |
| **Existing unit tests** | Implicit contracts maintainers expect |
| **External docs/specs** | Protocol specs, format definitions |

### 3. Check Strategy Realism

Does the strategy generate inputs the function should actually handle?

**Red flags:**
- Generating inputs outside documented domain
- Missing constraints that real callers would have
- Overly aggressive size/complexity

**Questions to ask:**
- Would real code pass this input?
- Does the docstring exclude this case?
- Is this a precondition violation, not a bug?

### 4. Classify the Failure

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Fails on edge case not in spec | Ambiguous specification | Clarify with maintainer |
| Fails on input violating preconditions | Over-broad strategy | Fix the strategy |
| Property contradicts docstring | Wrong property | Fix the property |
| Clear violation of documented guarantee | Genuine bug | Report with evidence |
| Behavior differs from similar functions | Possible inconsistency | Investigate further |

### 5. Decide Action

- **Test bug** -> Fix the property or strategy, don't report
- **Ambiguous spec** -> Open discussion issue, not bug report
- **Genuine bug** -> Report with minimal reproducer and evidence

## Property Grounding Checklist

Before reporting a failure as a bug, verify:

- [ ] Property matches documented return type
- [ ] Property matches docstring guarantees
- [ ] Input is within documented domain (preconditions met)
- [ ] No `assume()` filtering out the failing case inappropriately
- [ ] Checked existing tests don't contradict your property
- [ ] Behavior contradicts docs, not just expectations

## Real-World Failure Patterns

### Numerical Instability

```python
@given(st.floats(min_value=0, max_value=1e308))
def test_probability_non_negative(x):
    prob = compute_probability(x)
    assert prob >= 0  # Fails for x=1e-320
```

**Classification**: Genuine bug if docstring says "returns probability in [0, 1]".

### Hash/Equality Inconsistency

```python
@given(valid_objects())
def test_hash_equality(obj):
    obj2 = create_equal_copy(obj)
    assert obj == obj2
    assert hash(obj) == hash(obj2)  # Fails
```

**Classification**: Genuine bug — violates Python's `a == b` implies `hash(a) == hash(b)` contract.

### Roundtrip Failure on Edge Cases

```python
@given(st.text())
def test_roundtrip(s):
    assert decode(encode(s)) == s  # Fails for s='\uD800'
```

**Classification**:
- If docs say "valid UTF-8 only" -> Strategy bug, add filter
- If docs say "any string" -> Genuine bug

### Iterator Off-by-One

```python
@given(st.lists(st.integers()))
def test_iterator_yields_all(xs):
    result = list(custom_iterator(xs))
    assert result == xs  # Fails: missing last element
```

**Classification**: Genuine bug if documented to iterate all elements.

## When NOT to Report

Do not report as bugs:

1. **Precondition violations**: Docs say "positive integers only" and you passed -1
2. **Undefined behavior**: Spec explicitly says behavior is undefined
3. **Implementation details**: Relying on undocumented internal behavior
4. **Platform-specific**: Bug only on unusual platform/version
5. **Test artifact**: Failure disappears with realistic constraints

## Confidence Threshold

Report only when you can answer YES to all:

1. Did you reproduce with a minimal example?
2. Did you verify the property against docs/types/docstrings?
3. Can you point to a specific documented guarantee that's violated?
4. Is the failing input within the documented domain?
5. Have you ruled out test bugs and ambiguous specs?

If uncertain on any point, open a discussion first, not a bug report.
