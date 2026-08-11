# Rust testing

Use the crate's existing runner, feature flags, fixtures, and test layout. Start with `cargo test` unless the repository already standardizes another runner.

## Place the test at the Rust seam

- Put focused unit tests in `#[cfg(test)] mod tests` beside the module when that location gives the clearest access to the unit under test.
- Put public crate and cross-module behavior in `tests/` integration tests.
- Put user-facing examples in documentation tests so `rustdoc` verifies that they compile and run.
- Keep shared integration-test support in a clearly named module; do not create a generic dumping ground.

Do not make an item public only to test it. Test a private helper directly only when it owns meaningful behavior that cannot be expressed more clearly through the module's public seam.

## Assert Rust outcomes

For `Result`, assert the relevant success value or error variant and payload rather than only `is_ok()` or `is_err()`. Use panic tests only when panic is the documented contract; ordinary invalid input should follow the API's error contract.

For floating point, choose tolerances from the numeric domain and expected error propagation. A single comparison against `f64::EPSILON` is not a general tolerance. When the project uses `approx`, choose its absolute, relative, or ULP comparison deliberately and make the tolerance visible in the assertion.

Use temporary directories for filesystem behavior and real byte sequences for encoding boundaries. Include `NaN`, infinity, signed zero, integer extremes, Unicode, and invalid bytes only when they belong to the supported or rejected domain being specified.

## Async and concurrency

Use `#[tokio::test]` when Tokio owns the async runtime. For timer behavior, enable Tokio's `test-util` feature and use `#[tokio::test(start_paused = true)]`; paused time advances when no other future can become ready while preserving timer order. Test protocol handlers through `AsyncRead` and `AsyncWrite` and use `tokio_test::io::Builder` when scripted I/O is the relevant seam.

Use Loom for small synchronization algorithms where alternate interleavings are the risk. Replace synchronization and thread types with Loom's versions inside `loom::model`, keep the modeled state small, and follow the installed Loom version's configuration. Loom models only part of the C11 memory model and can both omit allowed executions and report conservative failures; a green model is evidence, not proof.

## Unsafe code

Run Miri when executed Rust paths may violate aliasing, initialization, alignment, validity, or other undefined-behavior rules:

```bash
rustup +nightly component add miri
cargo +nightly miri test
```

Miri checks only the paths and executions it interprets. It does not prove soundness, does not support most FFI or networking, and explores only some concurrent executions. Use different inputs and, where relevant, seeds or specialized concurrency tools.

Rust sanitizers are target- and toolchain-dependent unstable features. Consult the current Rust Unstable Book and the repository's CI targets before retaining a sanitizer command; do not copy a command across platforms by assumption.

## Documentation and compile-time contracts

Ordinary rustdoc examples pass when they compile and run without panic. Use hidden `#` setup lines to keep examples readable. Use:

- `no_run` when the example should compile but its effects should not execute in tests
- `should_panic` when panic is the example's contract
- `compile_fail` when compilation failure is the contract, while remembering a future compiler may accept code rejected today

Use trybuild when exact compile success or diagnostic output is part of a procedural macro or API misuse contract. Review its `.stderr` changes as carefully as snapshots.

## Route specialized search and tools

Load `property-based-testing` and its proptest adapter for broad generated domains, shrinking, state machines, or schedule search. Load `fuzzing` for cargo-fuzz campaigns. Keep those workflows out of this language reference.

Use cargo-nextest, coverage tools, mutation tools, snapshot crates, mock frameworks, or parameterization crates only when the repository already uses them or their specific benefit justifies adoption. Inspect the installed version's help and project configuration instead of assuming a universal command or installation mode.

## Primary references

- [The Rust Programming Language: testing](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [rustdoc documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html)
- [Tokio testing](https://tokio.rs/tokio/topics/testing)
- [Loom](https://github.com/tokio-rs/loom)
- [Miri](https://github.com/rust-lang/miri)
- [Rust sanitizers](https://doc.rust-lang.org/beta/unstable-book/compiler-flags/sanitizer.html)
- [`approx`](https://docs.rs/approx/latest/approx/)
- [trybuild](https://github.com/dtolnay/trybuild)
- [cargo-nextest installation](https://nexte.st/docs/installation/pre-built-binaries/)
