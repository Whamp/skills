# Property-Driven Development

Design features by defining properties upfront as executable specifications, before implementation.

## When to Use

- Designing a new feature from scratch
- Building something with clear algebraic properties (serialization, validation, transformations)
- Complex domain where edge cases are likely
- User wants to think through requirements rigorously before coding

## Process

### Phase 1: Understand the Feature

Gather information:
- **Purpose**: What problem does this solve?
- **Inputs**: What data does it accept? What makes inputs valid?
- **Outputs**: What does it produce? What guarantees?
- **Constraints**: What must always be true?
- **Edge cases**: Boundary conditions?
- **Relationships**: Inverse operations? Compositions?

### Phase 2: Discover Properties

Work through these questions systematically:

| Question | Property Type | Example |
|----------|---------------|---------|
| Does it have an inverse operation? | Roundtrip | `decode(encode(x)) == x` |
| Is applying it twice the same as once? | Idempotence | `f(f(x)) == f(x)` |
| What quantities are preserved? | Invariants | Length, sum, count |
| Is order of arguments irrelevant? | Commutativity | `f(a, b) == f(b, a)` |
| Can operations be regrouped? | Associativity | `f(f(a,b), c) == f(a, f(b,c))` |
| Is there a neutral element? | Identity | `f(x, 0) == x` |
| Does `x <= y` imply `f(x) <= f(y)`? | Monotonicity | Pricing, scoring |
| Is there an oracle/reference impl? | Oracle | `new(x) == old(x)` |
| Can output be easily verified? | Hard/Easy | `is_sorted(sort(x))` |
| How does `f(x)` relate to `f(transform(x))`? | Metamorphic | Filter then sort = sort then filter |

### Phase 3: Define Input Domain

Specify valid inputs as strategies. The strategy IS the specification.

**Do** build constraints INTO the strategy, not via `assume()`.

```python
@st.composite
def valid_registration_requests(draw):
    """Generate valid registration requests - this documents the domain."""
    username = draw(st.text(
        min_size=3, max_size=20,
        alphabet=st.characters(whitelist_categories=('L', 'N'))
    ))
    email = draw(st.emails())
    password = draw(st.text(min_size=8, max_size=100))
    age = draw(st.integers(min_value=13, max_value=150))
    return RegistrationRequest(
        username=username, email=email, password=password, age=age
    )
```

### Phase 4: Write Property Tests (Before Implementation)

Create tests that will fail initially:

```python
class TestFeatureSpec:
    """Property-based specification - should FAIL until implemented."""

    @given(valid_inputs())
    def test_core_property(self, x):
        """[What this guarantees]."""
        result = feature(x)
        assert property_holds(result)
```

### Phase 5: Iterate on Design

Properties reveal design questions. Surface them early.

## Common Design Questions Raised

Properties often expose gaps in the spec:

| Property Attempt | Question Raised |
|------------------|-----------------|
| Roundtrip for users | What about deleted/deactivated users? |
| Duplicate rejection | Case-sensitive? Unicode normalization? |
| Password storage | Which algorithm? Salted? Configurable? |
| Ordering guarantee | Stable sort? Tie-breaking rules? |
| Monotonicity in pricing | Do discounts break monotonicity? |
| Idempotence of migration | Re-running migration on migrated data — safe? |

**Don't** answer design questions yourself. Surface them to the user.

## Property Strength Hierarchy

Build properties incrementally from weak to strong:

1. **No crash**: Function completes without raising (weakest)
2. **Type preservation**: Output has expected type
3. **Invariants**: Specific properties hold on output
4. **Full specification**: All requirements satisfied (strongest)

**Do** start with weak properties when uncertain, then strengthen.

**Don't** skip to "full specification" — weak properties still catch bugs.

## Red Flags

- **Writing tautological properties**: `assert f(x) == f(x)` tests nothing
- **Starting too strong**: Build from weak to strong properties
- **Ignoring design questions**: Properties that feel awkward often reveal design gaps
- **Overly complex strategies**: 50+ line strategy = domain model needs simplification
- **Not involving the user**: Design questions should be discussed, not assumed

## Checklist

- [ ] Properties are not tautological
- [ ] At least one strong property defined
- [ ] Input strategy documents valid inputs
- [ ] Design questions have been surfaced
- [ ] Tests will actually FAIL without implementation
