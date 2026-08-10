---
name: rust-testing-expert
description: Companion to `tdd` and `integration-testing` for idiomatic Rust test code. Use when you already know you need tests in Rust and want the right patterns, tooling, and structure for unit and integration tests, trait-based mocking, tokio async testing, proptest, rstest, and unsafe-code validation with Miri and sanitizers. Does not cover fuzzing (see cargo-fuzz companion skill).
disable-model-invocation: true
---

# Rust Testing

> **Scope:** Testing functions, modules, and libraries. Not fuzzing or black-box e2e.

**Main objectives:** use tests to...

1. uncover hard-to-detect bugs (edge cases, race conditions, undefined behavior)
2. document how to use the code
3. prevent regressions
4. challenge the code — especially unsafe blocks

**Recommended tooling:** `cargo test`, `cargo-nextest`, `proptest`, `mockall`, `rstest`, `tokio` (with `test-util`), `assert_cmd` (for CLIs), `cargo-llvm-cov` or `cargo-tarpaulin` installed as dev-dependencies.
**Do** adapt to missing tools. **Do** recommend installing missing relevant tooling.

## Regression-first workflow

**Do** add regression tests BEFORE changing code:

```text
1. READ   → Understand current behavior
2. TEST   → Add test that passes with current code
3. CHANGE → Make your modification
4. VERIFY → Regression test still passes
```

**Do** follow this for optimizations especially — "optimization broke edge case we didn't test" is the most common failure mode.

## File and code layout

**Do** mimic the existing test structure of the project when adding new tests

**Do** use `#[cfg(test)] mod tests` for unit tests colocated with source

**Do** place integration tests in `tests/` directory, shared utilities in `tests/common/mod.rs`

**Do** extract logic from `main.rs` into `lib.rs` for testability in binary crates

**Prefer** naming tests after behavior: `parse_empty_input_returns_none`, not `test_parse_1`

**Do** put helper functions after all tests, below a `// Helpers` comment

## Core guidelines

**Do** follow the Arrange/Act/Assert pattern and make it visible:

```rust
#[test]
fn parses_valid_input() {
    // Arrange
    let input = r#"{"id": 1, "name": "Alice"}"#;

    // Act
    let result = parse_user(input);

    // Assert
    assert_eq!(result.unwrap().name, "Alice");
}
```

**Do** keep tests focused — assert on one precise aspect

**Prefer** stubs over mocks. Stubs provide an alternate implementation; mocks verify call counts. Call-count verification is usually an internal detail.

**Don't** rely on network calls — use trait-based mocking

**Don't** test internal details — test public API behavior

**Avoid** `#[should_panic]` for error testing — prefer `assert!(matches!(result, Err(MyError::Specific(_))))`

**Do** assert specific error types, not just `is_err()`

**Do** add custom messages to assertions: `assert_eq!(result, expected, "failed for input: {input}")`

**Do** implement `Debug` on types used in assertions for clear failure messages

**Do** use approximate comparison for floats (`(a - b).abs() < f64::EPSILON`)

**Do** assert collection contents, not just length

## Edge case requirements

Every function that handles data must have tests for:

**Do** test empty inputs, single-element inputs, maximum-size inputs

**Do** test Unicode handling: multi-byte characters, emoji, RTL text, mixed scripts

**Do** test invalid UTF-8 when accepting `&[u8]` — document and test behavior explicitly

**Do** test I/O error paths: missing files, permission denied — never silently ignore

**Do** test boundary values: `0`, `i64::MAX`, `i64::MIN`, `f64::NAN`, `f64::INFINITY`

## Mocking and test doubles

**Do** design for testability with traits — accept dependencies as generic parameters:

```rust
#[async_trait]
pub trait HttpClient: Send + Sync {
    async fn get(&self, url: &str) -> Result<String, Error>;
}

pub struct UserService<C: HttpClient> {
    client: C,
}
```

**Prefer** hand-written stubs for simple traits (1-2 methods)

**Do** use `mockall` with `#[automock]` for complex traits (3+ methods):

```rust
use mockall::automock;

#[automock]
pub trait Repository {
    fn find_by_id(&self, id: u64) -> Option<User>;
    fn save(&self, user: &User) -> Result<(), Error>;
}

#[test]
fn update_user_saves_changes() {
    let mut mock = MockRepository::new();
    mock.expect_find_by_id()
        .with(eq(42))
        .times(1)
        .returning(|_| Some(User { id: 42, name: "Alice".into() }));
    mock.expect_save()
        .times(1)
        .returning(|_| Ok(()));

    let service = UserService::new(mock);
    service.update_user(42, "Alice Updated").unwrap();
}
```

**Don't** mock types you own — test them directly

**Do** warn the developer when code requires >10 parameters or mocks — this is a code smell indicating too many responsibilities

## Async testing

**Do** use `#[tokio::test]` for async tests, not manual `block_on`

**Do** use `start_paused = true` for time-dependent tests — instant and deterministic:

```rust
#[tokio::test(start_paused = true)]
async fn request_times_out() {
    let task = tokio::spawn(async { client.fetch("/slow").await });
    tokio::time::advance(Duration::from_secs(30)).await;
    let result = task.await.unwrap();
    assert!(matches!(result, Err(Error::Timeout)));
}
```

**Do** use `flavor = "multi_thread", worker_threads = N` for concurrency tests

**Do** use `tokio::task::yield_now().await` after `time::advance` to let spawned tasks run

**Don't** use `std::thread::sleep()` — use `tokio::time::sleep().await`

**Do** add `tokio = { version = "1", features = ["test-util", "time", "macros", "rt"] }` to dev-dependencies

## Fixtures and parameterized tests

**Do** use `rstest` fixtures to eliminate duplicate setup:

```rust
use rstest::*;

#[fixture]
fn config() -> Config {
    Config::load("test")
}

#[rstest]
fn loads_default_settings(config: Config) {
    assert!(!config.is_production());
}
```

**Do** use `#[case]` for parameterized tests:

```rust
#[rstest]
#[case("42", 42)]
#[case("-17", -17)]
#[case("  123  ", 123)]
fn parses_valid_integers(#[case] input: &str, #[case] expected: i32) {
    assert_eq!(parse_int(input), Ok(expected));
}
```

## Property-based testing

**Do** use `proptest` for any test with a notion of "always" or "never"

**Do** use property-based tests for edge case discovery — complementary to example-based tests

**Don't** try to test 100% of algorithm cases with PBT — use both approaches

**Do** create custom strategies for domain types to respect business invariants:

```rust
use proptest::prelude::*;

fn valid_email() -> impl Strategy<Value = String> {
    ("[a-z]{3,10}", "[a-z]{2,8}", "[a-z]{2,4}")
        .prop_map(|(user, domain, tld)| format!("{user}@{domain}.{tld}"))
}

proptest! {
    #[test]
    fn roundtrip_serialization(value in valid_order()) {
        let serialized = serde_json::to_string(&value).unwrap();
        let deserialized: Order = serde_json::from_str(&serialized).unwrap();
        prop_assert_eq!(value, deserialized);
    }
}
```

**Don't** over-constrain strategies — use `any::<T>()` unless the algorithm requires narrower inputs

**Prefer** `prop_map` over `prop_filter` — filtering discards values and slows generation

**Do** use `prop_flat_map` for dependent generators (where one value constrains another)

Classical properties: roundtrip (encode/decode), idempotence (f(f(x)) == f(x)), commutativity, invariant preservation, oracle comparison against simpler implementation.

## Testing unsafe code

**Do** require extra testing rigor for unsafe code: unit tests + property-based tests + Miri

**Do** write oracle tests comparing unsafe implementation against safe reference:

```rust
proptest! {
    #[test]
    fn unsafe_matches_safe(data: Vec<i32>) {
        let safe = safe_sum(&data);
        let fast = unsafe { unsafe_sum(&data) };
        prop_assert_eq!(safe, fast);
    }
}
```

**Do** run Miri on unsafe code in CI:

```bash
rustup +nightly component add miri
cargo +nightly miri test
```

Key Miri flags: `-Zmiri-strict-provenance` (strict pointer provenance), `-Zmiri-disable-isolation` (allow I/O), `-Zmiri-symbolic-alignment-check`.

**Do** run sanitizers on code with `unsafe`:

```bash
# AddressSanitizer
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu

# ThreadSanitizer
RUSTFLAGS="-Z sanitizer=thread" cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu
```

## Test performance

**Prefer** `cargo-nextest` for faster parallel execution (process-per-test isolation)

**Do** avoid real I/O in unit tests — use in-memory buffers

**Do** use `cargo test -- --nocapture` for debugging, `cargo nextest run` for CI

**Do** use `TempDir` from `tempfile` for filesystem tests — auto-cleans on drop

**Do** use `OnceCell` or `LazyLock` for expensive one-time setup shared across tests

**Prefer** `cargo llvm-cov --html` for coverage reports
