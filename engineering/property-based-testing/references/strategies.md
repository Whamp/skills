# Input Strategy Reference

## Python/Hypothesis

| Type | Strategy |
|------|----------|
| `int` | `st.integers()` |
| `float` | `st.floats(allow_nan=False)` |
| `str` | `st.text()` |
| `bytes` | `st.binary()` |
| `bool` | `st.booleans()` |
| `list[T]` | `st.lists(strategy_for_T)` |
| `dict[K, V]` | `st.dictionaries(key_strategy, value_strategy)` |
| `set[T]` | `st.frozensets(strategy_for_T)` |
| `tuple[T, ...]` | `st.tuples(strategy_for_T, ...)` |
| `Optional[T]` | `st.none() \| strategy_for_T` |
| `Union[A, B]` | `st.one_of(strategy_a, strategy_b)` |
| Custom class | `st.builds(ClassName, field1=..., field2=...)` |
| Enum | `st.sampled_from(EnumClass)` |
| Constrained int | `st.integers(min_value=0, max_value=100)` |
| Email | `st.emails()` |
| UUID | `st.uuids()` |
| DateTime | `st.datetimes()` |
| Regex match | `st.from_regex(r"pattern")` |
| From type hints | `st.from_type(MyClass)` |

### Composite Strategies

```python
@st.composite
def valid_users(draw):
    name = draw(st.text(min_size=1, max_size=50))
    age = draw(st.integers(min_value=0, max_value=150))
    email = draw(st.emails())
    return User(name=name, age=age, email=email)
```

### Dependent Generators

Use `@st.composite` with `draw` to build values that depend on each other:

```python
@st.composite
def sorted_pair(draw):
    """Generate (a, b) where a <= b."""
    a = draw(st.integers())
    b = draw(st.integers(min_value=a))
    return (a, b)
```

### Recursive Strategies

For tree-like or nested data (JSON, ASTs, configs):

```python
json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
    lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(), children, max_size=5),
    max_leaves=10,
)
```

### Dynamic Generation with `data()`

When input depends on runtime conditions:

```python
@given(data())
def test_dynamic(data):
    n = data.draw(st.integers(min_value=1, max_value=10))
    xs = data.draw(st.lists(st.integers(), min_size=n, max_size=n))
    assert len(xs) == n
```

## JavaScript/fast-check

| Type | Strategy |
|------|----------|
| number | `fc.integer()` or `fc.float()` |
| string | `fc.string()` |
| boolean | `fc.boolean()` |
| array | `fc.array(itemArb)` |
| object | `fc.record({...})` |
| optional | `fc.option(arb)` |
| email | `fc.emailAddress()` |
| scheduler | `fc.scheduler()` |

### Example

```typescript
const userArb = fc.record({
  name: fc.string({ minLength: 1, maxLength: 50 }),
  age: fc.integer({ min: 0, max: 150 }),
  email: fc.emailAddress(),
});
```

### @fast-check/vitest Integration

With `@fast-check/vitest` installed, use `it.prop()` or the `g()` helper for inline generation:

```typescript
import { it, fc } from '@fast-check/vitest';

// it.prop: declare arbitraries upfront
it.prop([fc.string(), fc.string(), fc.string()])('should detect substring', (a, b, c) => {
  expect(isSubstring(a + b + c, b)).toBe(true);
});

// g(): generate values inline (useful for filling unused fields)
it('should compute positive age', ({ g }) => {
  const user: User = { name: g(fc.string), birthday: '2010-02-03' };
  expect(computeAge(user)).toBeGreaterThan(0);
});
```

**Note:** Pass the arbitrary *function* to `g()`, not the result: `g(fc.string)` not `g(fc.string())`. Pass options as a second arg: `g(fc.date, { min: new Date('2010-01-01') })`.

Without `@fast-check/vitest`, use `fc.assert(fc.property(...))` directly (or `fc.asyncProperty` + `await` for async).

### fast-check Strategy Tips

- **Prefer `map` over `filter`** for constrained values: `fc.nat().map(n => n * 2)` for evens, `fc.tuple(fc.string(), fc.string()).map(([a, b]) => a + 'X' + b)` for strings containing 'X'
- **Use `size: '-1'`** instead of `maxLength` when you just need smaller inputs for performance — `maxLength` should reflect actual domain constraints only
- **Defaults are generous**: fast-check generates up to ~10 items by default; only add size constraints when the algorithm genuinely needs them

### Async Race Condition Testing

`fc.scheduler()` controls promise resolution order, exposing race conditions:

```typescript
it('should resolve in call order', async () => {
  await fc.assert(
    fc.asyncProperty(fc.scheduler(), async (s) => {
      const seen: number[] = [];
      const call = vi.fn().mockImplementation((v) => Promise.resolve(v));

      const queued = queue(s.scheduleFunction(call));
      await s.waitFor(
        Promise.all([
          queued(1).then((v) => seen.push(v)),
          queued(2).then((v) => seen.push(v)),
        ])
      );

      expect(seen).toEqual([1, 2]);
    })
  );
});
```

Use `fc.scheduler()` whenever testing code that accepts async functions as input.

## Rust/proptest

| Type | Strategy |
|------|----------|
| i32, u64, etc | `any::<i32>()` |
| String | `any::<String>()` or `"[a-z]+"` (regex) |
| Vec<T> | `prop::collection::vec(strategy, size)` |
| Option<T> | `prop::option::of(strategy)` |

### Strategy Composition with `prop_compose!`

```rust
prop_compose! {
    fn valid_user()(
        name in "[a-z]{3,20}",
        age in 0u8..150,
        email in "[a-z]{3,10}@[a-z]{3,8}\\.[a-z]{2,4}"
    ) -> User {
        User { name, age, email }
    }
}
```

### Dependent Generators with `prop_flat_map`

```rust
// Generate a vec, then pick a valid index into it
prop_compose! {
    fn vec_and_index()(vec in prop::collection::vec(any::<i32>(), 1..100))
        (index in 0..vec.len(), vec in Just(vec))
    -> (Vec<i32>, usize) {
        (vec, index)
    }
}
```

### Example

```rust
proptest! {
    #[test]
    fn test_roundtrip(s in "[a-z]{1,20}") {
        let encoded = encode(&s);
        let decoded = decode(&encoded)?;
        prop_assert_eq!(s, decoded);
    }
}
```

**Prefer** `prop_map` over `prop_filter` — filtering discards values and slows generation.

## Go/rapid

```go
rapid.Check(t, func(t *rapid.T) {
    s := rapid.String().Draw(t, "s")
    n := rapid.IntRange(0, 100).Draw(t, "n")
    // test with s and n
})
```

### Stateful Testing with rapid

```go
rapid.Check(t, func(t *rapid.T) {
    var model []int
    var stack Stack

    t.Repeat(map[string]func(*rapid.T){
        "push": func(t *rapid.T) {
            v := rapid.Int().Draw(t, "v")
            model = append(model, v)
            stack.Push(v)
        },
        "pop": func(t *rapid.T) {
            if len(model) == 0 { t.Skip("empty") }
            expected := model[len(model)-1]
            model = model[:len(model)-1]
            assert.Equal(t, expected, stack.Pop())
        },
    })
})
```

## Java/jqwik

```java
@Property
void sortingPreservesLength(@ForAll List<Integer> list) {
    List<Integer> sorted = new ArrayList<>(list);
    Collections.sort(sorted);
    Assertions.assertEquals(list.size(), sorted.size());
}

@Provide
Arbitrary<User> validUsers() {
    return Combinators.combine(
        Arbitraries.strings().ofMinLength(1).ofMaxLength(50),
        Arbitraries.integers().between(0, 150)
    ).as(User::new);
}
```

## Best Practices

1. **Constrain early**: Build constraints into strategy, not `assume()`
2. **Size limits**: Use `max_size` to prevent slow tests
3. **Realistic data**: Match real-world constraints
4. **Reuse strategies**: Define once, use across tests
