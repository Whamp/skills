# C and C++ fuzzing with libFuzzer and AFL++

Use the repository's existing engine and build system when possible. Both engines depend on instrumentation details; inspect the installed compiler and fuzzer help before copying a command into CI.

## libFuzzer

Expose a narrow, deterministic entry point:

```cpp
#include <cstddef>
#include <cstdint>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    parse_document(data, size);
    return 0;
}
```

Build with Clang's fuzzer runtime and the sanitizers justified by the target. A common source-build shape is:

```bash
clang++ -g -O1 -fsanitize=fuzzer,address,undefined \
  fuzz_parse.cc parser.cc -o fuzz_parse
```

Run with the writable corpus first. Keep flags bounded and discover them from the built binary:

```bash
./fuzz_parse -help=1
./fuzz_parse corpus/
```

Use a focused dictionary when stable tokens block deeper parsing:

```bash
./fuzz_parse -dict=document.dict corpus/
```

Minimize a corpus while preserving discovered features:

```bash
mkdir minimized
./fuzz_parse -merge=1 minimized corpus
```

Use `-minimize_crash=1` with a bounded run or time budget for a failing input. Keep the exact built binary and options available until triage is complete.

Use `FuzzedDataProvider` when one byte stream must deterministically supply several typed fields. Its method order is part of the input mapping; changing that order invalidates corpus meaning. For strongly structured formats, consider a custom mutator that parses, mutates, and serializes the structure while still calling `LLVMFuzzerMutate` where useful.

## AFL++

For source builds, prefer AFL++'s current compiler wrappers. Current guidance prioritizes LTO mode (`afl-clang-lto` or `afl-clang-lto++`), then LLVM mode (`afl-clang-fast` or `afl-clang-fast++`), subject to compiler and project support. Do not combine AFL++ harnesses with libFuzzer's `-fsanitize=fuzzer` runtime.

For a target that reads a file path represented by `@@`:

```bash
afl-fuzz -i seeds -o findings -- ./target @@
```

For stdin input, omit `@@`. Minimize coverage-duplicate corpus entries with the current `afl-cmin` interface:

```bash
afl-cmin -i findings/default/queue -o minimized -- ./target @@
```

Load a dictionary with `-x <dictionary>` when tokens or magic bytes are a measured barrier. AFL++ LTO mode can generate an autodictionary; LLVM mode can emit one through its documented environment variables. Inspect the current documentation before retaining those build settings.

Scale one campaign through AFL++'s synchronized main and secondary instances, all with unique IDs and the same output directory:

```bash
afl-fuzz -i seeds -o findings -M main-host -- ./target @@
afl-fuzz -i seeds -o findings -S worker-01 -- ./target @@
```

Add workers to available measured capacity; do not claim linear scaling. Use different schedules, dictionaries, or instrumentation only when the variation has a reason.

Persistent mode can remove process startup and deliver large throughput gains, but every iteration must restore relevant state. If instability appears only in persistent mode, run non-persistent until the leak is fixed. Follow the installed AFL++ persistent-mode template rather than copying a generic loop that may mishandle input delivery or deferred initialization.

Use CMPLOG, comparison splitting, and instrumentation allowlists as targeted responses to observed comparison or coverage barriers. They are not automatic correctness improvements.

## Primary references

- [LLVM libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html)
- [Google structure-aware fuzzing](https://github.com/google/fuzzing/blob/master/docs/structure-aware-fuzzing.md)
- [AFL++ fuzzing in depth](https://aflplus.plus/docs/fuzzing_in_depth/)
- [AFL++ best practices](https://aflplus.plus/docs/best_practices/)
- [AFL++ parallel fuzzing](https://aflplus.plus/docs/parallel_fuzzing/)
