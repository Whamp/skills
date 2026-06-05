# Generating Property-Based Tests

How to create complete, runnable property-based tests.

## Process

### 1. Analyze Target Function

- Read function signature, types, and docstrings
- Understand input types and constraints
- Identify output type and expected behavior
- Note preconditions or invariants
- Check existing example-based tests as hints

### 2. Discover Properties

Work through these questions systematically:

| Question | Property Type |
|----------|---------------|
| Does it have an inverse? | Roundtrip |
| Is applying it twice the same as once? | Idempotence |
| What quantities are preserved? | Invariant (length, sum, count) |
| Is argument order irrelevant? | Commutativity |
| Can operations be regrouped? | Associativity |
| Is there a neutral element? | Identity |
| Does `x <= y` imply `f(x) <= f(y)`? | Monotonicity |
| Can I relate `f(x)` to `f(transform(x))`? | Metamorphic |
| Is there a reference impl? | Oracle |
| Can output be verified more easily than computed? | Easy-to-verify |

**Do** design at least two properties per function. "No crash" alone is insufficient.

**Do** write one sentence describing what bug each property would catch.

### 3. Design Input Strategies

**Do** build constraints INTO the strategy, not via `assume()`.

**Do** use realistic size limits to prevent slow tests.

**Don't** over-constrain — use the widest valid input domain.

### 4. Generate Test Code

**Do** add clear docstrings explaining what each property verifies.

**Do** add `@example` / explicit edge cases for empty, single-element, and boundary values.

**Do** set `@settings` / run counts appropriate for context.

### 5. Include Edge Cases

```python
@example([])           # Empty
@example([1])          # Single element
@example([1, 1, 1])    # Duplicates
@example("")           # Empty string
@example(0)            # Zero
@example(-1)           # Negative
```

## Settings Recommendations

```python
# Development (fast feedback)
@settings(max_examples=10)

# CI (thorough)
@settings(max_examples=200)

# Nightly/Release (exhaustive)
@settings(max_examples=1000, deadline=None)
```

**Do** register profiles for consistent CI behavior:

```python
# conftest.py
from hypothesis import settings
settings.register_profile("ci", max_examples=500)
settings.register_profile("dev", max_examples=50)
# Activate via: HYPOTHESIS_PROFILE=ci pytest
```

## Example Test Patterns

### Roundtrip (Encode/Decode)

```python
@given(valid_messages())
def test_roundtrip(msg):
    """Encoding then decoding returns original."""
    assert decode(encode(msg)) == msg
```

### Idempotence

```python
@given(st.text())
def test_normalize_idempotent(s):
    """Normalizing twice equals normalizing once."""
    assert normalize(normalize(s)) == normalize(s)
```

### Sorting Properties

```python
@given(st.lists(st.integers()))
@example([])
@example([1])
@example([1, 1, 1])
def test_sort(xs):
    result = sort(xs)
    assert len(result) == len(xs)           # Length preserved
    assert sorted(result) == sorted(xs)     # Elements preserved
    assert all(result[i] <= result[i+1]     # Ordered
               for i in range(len(result)-1))
    assert sort(result) == result           # Idempotent
```

### Metamorphic Relation

```python
@given(st.lists(st.integers(), min_size=1), st.integers())
def test_search_after_insert(xs, elem):
    """If we insert elem, searching for it must succeed."""
    ys = xs + [elem]
    assert search(ys, elem) is True
```

### Algebraic Laws (Monoid)

```python
@given(st.text(), st.text(), st.text())
def test_concat_associative(a, b, c):
    """String concatenation is associative."""
    assert (a + b) + c == a + (b + c)

@given(st.text())
def test_concat_identity(a):
    """Empty string is the identity for concatenation."""
    assert a + "" == a and "" + a == a
```

## Stateful Testing (Hypothesis)

For data structures and stateful systems, use `RuleBasedStateMachine` to test sequences of operations against a reference model:

```python
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import hypothesis.strategies as st

class DatabaseMachine(RuleBasedStateMachine):
    """Test key-value store against dict reference model."""

    def __init__(self):
        super().__init__()
        self.model = {}       # reference
        self.db = KeyValueDB()  # system under test

    @rule(key=st.text(), value=st.binary())
    def put(self, key, value):
        self.model[key] = value
        self.db.put(key, value)

    @rule(key=st.text())
    def get(self, key):
        assert self.model.get(key) == self.db.get(key)

    @rule(key=st.text())
    def delete(self, key):
        self.model.pop(key, None)
        self.db.delete(key)

    @invariant()
    def size_matches(self):
        assert len(self.model) == self.db.size()

TestDatabase = DatabaseMachine.TestCase
```

Stateful testing excels at finding bugs in operation *sequences* that no single operation reveals. Use `Bundle` to track generated references across rules.

## Shrinking

PBT libraries automatically shrink failing inputs to minimal counterexamples. Understand how this works:

- **Hypothesis**: Integrated shrinking — reduces the internal choice sequence, not the value type. Produces simpler examples (e.g., `[0, 0]` not `[42, 42]`).
- **fast-check**: Similar integrated approach.
- **proptest/QuickCheck**: Type-based shrinking — each type defines how to shrink.

**Do** trust the shrinker. Don't manually minimize.

**Don't** use `filter()` / `assume()` heavily — they interfere with shrinking by rejecting candidates.

**Do** prefer `map` over `filter` for constrained values (e.g., `fc.nat().map(n => n * 2)` for evens).

## Checklist Before Finishing

- [ ] Tests are not tautological (don't reimplement the function)
- [ ] At least one strong property (not just "no crash")
- [ ] Edge cases covered with `@example` decorators
- [ ] Strategy constraints are realistic, not over-filtered
- [ ] Settings appropriate for context (dev vs CI)
- [ ] Docstrings explain what each property verifies
- [ ] Tests actually run and pass (or fail for expected reasons)

## When Tests Fail

See `references/interpreting-failures.md` for how to interpret failures and determine if they represent genuine bugs vs test errors vs ambiguous specifications.
