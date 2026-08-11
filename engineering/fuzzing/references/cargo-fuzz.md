# Rust fuzzing with cargo-fuzz

cargo-fuzz is a Cargo subcommand that drives libFuzzer through `libfuzzer-sys`; it is not a separate fuzzing engine. Prefer it when the Rust project already uses it or when libFuzzer's supported toolchain fits the target.

## Check prerequisites

Before installation, read the current cargo-fuzz README. Its documented prerequisites include nightly Rust, LLVM sanitizer support, a C++11 compiler, supported architectures, and supported operating systems. Keep CI on a documented target rather than assuming the host is compatible.

Install and inspect the command surface:

```bash
cargo install cargo-fuzz
cargo +nightly fuzz --help
```

Initialize once at the crate root:

```bash
cargo +nightly fuzz init
cargo +nightly fuzz add parse_document
```

In a Cargo workspace, either include `fuzz` in `workspace.members` or initialize an independent fuzzing workspace with the currently documented `--fuzzing-workspace=true` option.

## Write the target

Start with bytes when malformed encodings and parser rejection are part of the risk:

```rust
#![no_main]

use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = my_crate::parse_document(data);
});
```

Ignoring the return value gives only a safety oracle. Add a semantic, differential, or metamorphic assertion when successful parses have a stronger contract.

Use structure-aware input when byte mutation spends most of the budget on shallow rejection. `fuzz_target!` accepts a type implementing `Arbitrary`; `libfuzzer-sys` re-exports the `arbitrary` crate. Derive `Arbitrary` only for types whose generated values represent the intended domain, and keep a separate byte target when malformed input still matters.

Custom structure-aware mutation can preserve syntax while using coverage feedback. Prefer it over generation only after measuring that valid structure is the barrier.

## Run and replay

Use the supported subcommands rather than forwarding older libFuzzer recipes through `run`:

```bash
cargo +nightly fuzz run parse_document
cargo +nightly fuzz tmin parse_document <failing-input>
cargo +nightly fuzz cmin parse_document
cargo +nightly fuzz coverage parse_document
cargo +nightly fuzz fmt parse_document <input>
```

Pass target options before `--` and libFuzzer options after it. Inspect both help surfaces before retaining flags:

```bash
cargo +nightly fuzz run parse_document -- -help=1
```

The `coverage` command replays the corpus without fuzzing and produces source-based coverage data. Use it to inspect target reach, not as a score target.

Keep target source and a small useful corpus in version control according to project policy. Minimize a failing artifact before adding it as regression evidence. Do not disable sanitizers merely because the immediate crate is safe Rust: dependencies, unsafe internals, and FFI may still be in the executed path. Choose sanitizer mode from the actual risk and current platform support.

## Primary references

- [cargo-fuzz README](https://github.com/rust-fuzz/cargo-fuzz)
- [Rust Fuzz Book: cargo-fuzz](https://rust-fuzz.github.io/book/cargo-fuzz.html)
- [Rust Fuzz Book: guide](https://rust-fuzz.github.io/book/cargo-fuzz/guide.html)
- [Rust Fuzz Book: structure-aware fuzzing](https://rust-fuzz.github.io/book/cargo-fuzz/structure-aware-fuzzing.html)
- [Rust Fuzz Book: coverage](https://rust-fuzz.github.io/book/cargo-fuzz/coverage.html)
