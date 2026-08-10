---
name: fuzzing
description: Use when writing fuzz harnesses, running fuzzing campaigns, analyzing coverage, or triaging crashes for Rust, C/C++, or Go code. Covers cargo-fuzz, libFuzzer, AFL++, and Go native fuzzing. Does not cover web/API fuzzing or black-box e2e testing.
disable-model-invocation: true
---

# Fuzzing

> **Scope:** Coverage-guided fuzzing of libraries and parsers. Not web fuzzing, not property-based testing (see `rust-testing-expert` for proptest, Miri, sanitizer basics).

## When to fuzz

**Do** fuzz parsers, deserializers, protocol handlers, file format processors, and anything accepting untrusted input.

**Do** fuzz serialization roundtrips: `deserialize(serialize(x)) == x`.

**Do** fuzz code with `unsafe` blocks (Rust), raw pointer manipulation (C/C++), or CGo FFI boundaries.

**Don't** fuzz pure business logic better served by property-based testing.

## Universal harness principles

Every harness, regardless of language, must follow these rules:

| Rule | Rationale |
| ------ | ----------- |
| **Deterministic** | Same input = same behavior. No `rand()`, no `time()`, no `/dev/urandom`. Seed PRNGs from fuzzer input if randomness is needed. |
| **No global state leaks** | Reset or isolate state between iterations. Global state causes non-reproducible crashes. |
| **Fast** | Target 100-1000+ exec/sec. No logging, no I/O, no network. Mock expensive operations. |
| **Never call `exit()`** | Kills the fuzzer process. Return error codes or let the SUT `abort()`. |
| **Handle all input sizes** | Empty, tiny, huge, malformed — the harness must not crash on unexpected sizes. Reject gracefully with early return. |
| **Free resources** | Prevent memory exhaustion during long campaigns. |
| **Narrow targets** | One harness per format/protocol. Don't mix PNG and TCP in the same target. |

### Interleaved fuzzing

Test multiple related operations in one harness by using the first byte(s) as an operation selector:

```c
uint8_t mode = data[0];
switch (mode % N) {
    case 0: op_a(...); break;
    case 1: op_b(...); break;
}
```

Use when operations share input types and a single corpus makes sense across all of them.

## Corpus management

**Do** seed with valid example inputs — dramatically accelerates initial coverage.

**Do** minimize regularly:

- libFuzzer: `./fuzz -merge=1 minimized/ corpus/`
- AFL++: `afl-cmin -i queue/ -o minimized/ -- ./fuzz`
- cargo-fuzz: `cargo +nightly fuzz run target -- -merge=1`
- Go: corpus managed automatically under `testdata/fuzz/`

**Do** merge corpora from multiple campaigns or fuzzers.

**Don't** commit massive corpora to version control — store minimized corpora only.

## Dictionaries

Dictionaries provide domain-specific tokens (magic bytes, keywords, delimiters) to help the fuzzer bypass format checks.

```text
# png.dict
magic="\x89PNG\r\n\x1a\n"
ihdr="IHDR"
idat="IDAT"
```

Usage: `./fuzz -dict=format.dict corpus/` (libFuzzer/cargo-fuzz) or `afl-fuzz -x format.dict ...` (AFL++).

**Generate from:** header files (`grep -o '".*"' header.h`), binary strings (`strings ./bin`), man pages, or ask an LLM. Keep focused: 50-200 entries.

AFL++ with `afl-clang-lto` auto-extracts dictionaries via `AFL_LLVM_DICT2FILE=auto.dict`.

## Overcoming obstacles

When coverage plateaus, check for these blockers:

| Obstacle | Solution |
| ---------- | ---------- |
| Checksum/hash validation | Conditional bypass: `#ifndef FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION` (C/C++) or `if !cfg!(fuzzing)` (Rust) |
| Non-deterministic PRNG | Fixed seed under fuzzing build flag |
| Complex multi-stage validation | Keep cheap checks (magic bytes), skip expensive ones (crypto signatures) during fuzzing |
| Magic value comparisons | Add to dictionary; AFL++ CMPLOG (`-c0`) solves these automatically |

**Do** provide safe defaults when skipping validation to avoid false positives from violated assumptions.

**Do** measure coverage before and after each patch.

## Crash triage

1. **Reproduce:** Re-run the crash input: `./fuzz crash-<hash>` or `cargo +nightly fuzz run target fuzz/artifacts/target/crash-<hash>`
2. **Minimize:** `./fuzz -minimize_crash=1 -exact_artifact_path=min.bin crash-<hash>`
3. **Classify:** Read the sanitizer report — ASan (buffer overflow, use-after-free, double-free), UBSan (integer overflow, null deref), or plain signal (SEGV, ABRT)
4. **Deduplicate:** Group crashes by stack trace signature, not input content
5. **Fix and regress:** Add minimized crash input to the seed corpus as a regression test

---

## Rust: cargo-fuzz

> For Miri, sanitizer basics, and proptest, see `rust-testing-expert`.

### Setup

```bash
rustup install nightly
cargo install cargo-fuzz
cargo fuzz init              # creates fuzz/ directory
cargo fuzz add my_target     # adds a new target
```

Requires nightly. Code must be in `lib.rs` (not just `main.rs`).

### Minimal harness

```rust
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = my_crate::parse(data);
});
```

### Structure-aware fuzzing with `arbitrary`

```rust
use arbitrary::Arbitrary;

#[derive(Debug, Arbitrary)]
pub struct Config {
    pub width: u32,
    pub height: u32,
    pub name: String,
}
```

```rust
fuzz_target!(|config: my_crate::Config| {
    config.validate();
});
```

Add `arbitrary = { version = "1", features = ["derive"] }` to your library's `Cargo.toml`.

### Running

```bash
cargo +nightly fuzz run my_target                    # ASan enabled by default
cargo +nightly fuzz run my_target --sanitizer none   # 2x faster for safe Rust
cargo +nightly fuzz run my_target -- -dict=fuzz/my.dict -max_len=4096
```

### Safe vs unsafe decision

```bash
cargo install cargo-geiger
cargo geiger   # shows unsafe usage in your crate + dependencies
```

- Unsafe code present: keep ASan (default)
- Pure safe Rust: use `--sanitizer none` for 2x throughput

### Coverage

```bash
rustup toolchain install nightly --component llvm-tools-preview
cargo install cargo-binutils rustfilt
cargo +nightly fuzz coverage my_target
# Then generate HTML (see coverage section below)
```

---

## C/C++: libFuzzer and AFL++

### libFuzzer harness

```c
#include <stdint.h>
#include <stddef.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 4) return 0;
    target_parse(data, size);
    return 0;
}
```

**Compile:** `clang++ -fsanitize=fuzzer,address -g -O2 harness.cc target.cc -o fuzz`

**Run:** `./fuzz corpus/ -dict=format.dict -max_len=4096`

### FuzzedDataProvider (structured input)

```cpp
#include <fuzzer/FuzzedDataProvider.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    FuzzedDataProvider fdp(data, size);
    auto len = fdp.ConsumeIntegral<size_t>();
    auto name = fdp.ConsumeRandomLengthString(64);
    auto remaining = fdp.ConsumeRemainingBytes<uint8_t>();
    process(name.c_str(), remaining.data(), remaining.size());
    return 0;
}
```

### AFL++ persistent mode

```c
#include <unistd.h>

int main(int argc, char **argv) {
    #ifdef __AFL_HAVE_MANUAL_CONTROL
        __AFL_INIT();
    #endif
    unsigned char buf[MAX_SIZE];
    while (__AFL_LOOP(10000)) {
        ssize_t len = read(0, buf, sizeof(buf));
        if (len <= 0) break;
        target_function(buf, len);
    }
    return 0;
}
```

**Compile:** `afl-clang-fast++ -O2 -fsanitize=fuzzer harness.cc target.cc -o fuzz`

**Run:** `afl-fuzz -i seeds/ -o findings/ -- ./fuzz`

**Multi-core:** Start one `-M primary` and N `-S secondaryNN` instances. AFL++ scales linearly with physical cores.

### CMPLOG (magic value solver)

Build a CMPLOG-instrumented copy: `AFL_LLVM_CMPLOG=1 afl-clang-fast++ ...`

Run with: `afl-fuzz -c0 -S cmplog -i seeds -o state -- ./fuzz`

### Sanitizer flags

```bash
# libFuzzer
clang++ -fsanitize=fuzzer,address,undefined -g -O2 -U_FORTIFY_SOURCE ...

# AFL++
AFL_USE_ASAN=1 afl-clang-fast++ ...
```

ASan requires ~20TB virtual memory. Disable memory limits: `-rss_limit_mb=0` (libFuzzer) or `-m none` (AFL++).

---

## Go: native fuzzing (Go 1.18+)

Go has built-in coverage-guided fuzzing via `testing.F`.

### Harness

```go
// parser_fuzz_test.go
package mypackage

import "testing"

func FuzzParse(f *testing.F) {
    // Seed corpus
    f.Add([]byte(`{"valid": true}`))
    f.Add([]byte(`<xml/>`))
    f.Add([]byte{})

    f.Fuzz(func(t *testing.T, data []byte) {
        result, err := Parse(data)
        if err != nil {
            return // expected for invalid input
        }
        // Optional: check invariants on valid parse
        if result.Validate() != nil {
            t.Errorf("parsed but invalid: %v", result)
        }
    })
}
```

### Running Go fuzzing

```bash
go test -fuzz=FuzzParse -fuzztime=5m ./...
```

Crashes are saved to `testdata/fuzz/FuzzParse/` and automatically replayed as regression tests on subsequent `go test` runs.

### Key differences from external fuzzers

- **Integrated:** No separate tool install. Corpus lives in `testdata/fuzz/`.
- **Typed seeds:** `f.Add()` accepts typed arguments (`string`, `[]byte`, `int`, `float64`, etc.), not just raw bytes.
- **Automatic regression:** Crash inputs become permanent test cases.
- **No dictionary support:** Use `f.Add()` with representative inputs containing magic values instead.
- **Single-process:** No built-in multi-core. Run multiple `go test -fuzz` processes on different functions for parallelism.
- **No sanitizers:** Go's runtime provides its own race detector (`-race`) and bounds checking. Use `-race` during fuzzing for concurrent code.

---

## Coverage analysis (all languages)

Coverage reveals whether your harness reaches the code you care about. Measure coverage from the *corpus*, not from fuzzer runtime stats.

### Generating reports

**Rust:**

```bash
cargo +nightly fuzz coverage my_target
TARGET=$(rustc -vV | sed -n 's|host: ||p')
cargo +nightly cov -- show -Xdemangler=rustfilt \
  "target/$TARGET/coverage/$TARGET/release/my_target" \
  -instr-profile="fuzz/coverage/my_target/coverage.profdata" \
  -format=html -o fuzz_html/ src/lib.rs
```

**C/C++ (LLVM):**

```bash
clang++ -fprofile-instr-generate -fcoverage-mapping -O2 \
  -DNO_MAIN harness.cc target.cc execute-rt.cc -o fuzz_cov
LLVM_PROFILE_FILE=fuzz.profraw ./fuzz_cov corpus/
llvm-profdata merge -sparse fuzz.profraw -o fuzz.profdata
llvm-cov show ./fuzz_cov -instr-profile=fuzz.profdata \
  -format=html -output-dir=html/ -ignore-filename-regex='harness|execute-rt'
```

**Go:**

```bash
go test -fuzz=FuzzParse -fuzztime=1m -coverprofile=fuzz_cov.out ./...
go tool cover -html=fuzz_cov.out -o fuzz_cov.html
```

### Interpreting and acting on gaps

| Observation | Action |
| ------------- | -------- |
| Large uncovered blocks behind a check | Add the check's value to dictionary, or patch the obstacle |
| Function never called | Harness doesn't reach it — restructure harness or add a new target |
| Branch always taken one way | Corpus lacks inputs that trigger the other branch — add seed inputs |
| Coverage plateaued | Try CMPLOG (AFL++), add dictionary, increase `-max_len`, or run longer |

**Do** compare coverage across campaigns to track progress.

**Don't** use `-fsanitize=fuzzer` for coverage builds — it conflicts with profile instrumentation. Build a separate coverage binary.

**Don't** use `-O3` for coverage — it can eliminate code and produce misleading results.
