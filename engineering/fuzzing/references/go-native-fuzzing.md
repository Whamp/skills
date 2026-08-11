# Go native fuzzing

Go includes coverage-guided fuzzing in the standard toolchain. A fuzz test lives in a `_test.go` file, is named `FuzzXxx`, accepts only `*testing.F`, and contains exactly one `f.Fuzz` target.

## Write the target

```go
func FuzzParseDocument(f *testing.F) {
    f.Add([]byte(`{"version":1}`))
    f.Add([]byte{})

    f.Fuzz(func(t *testing.T, data []byte) {
        document, err := ParseDocument(data)
        if err != nil {
            return
        }
        if err := document.Validate(); err != nil {
            t.Fatalf("successful parse produced invalid document: %v", err)
        }
    })
}
```

The target's first argument is `*testing.T`; remaining fuzzing arguments must use Go's supported primitive types. Every `f.Add` seed and corpus file must match those types and their order exactly.

Keep the target fast, deterministic, and independent of global state. Go invokes it in nondeterministic order across parallel workers. Use a semantic assertion after successful parsing when panic detection alone is too weak.

## Run and replay

Ordinary `go test` runs the seed corpus as regression cases. Active fuzzing first runs the package's other tests and gathers baseline coverage, then starts workers:

```bash
go test -fuzz=FuzzParseDocument -fuzztime=5m ./path/to/package
```

The `-fuzz` regex must match one fuzz test. `-parallel` controls fuzzing processes and defaults to `$GOMAXPROCS`; do not launch manual copies under the assumption that Go fuzzing is single-process.

On failure, Go minimizes the input and writes it under `testdata/fuzz/FuzzName/`. Replay the exact case with the command printed in the failure output, then keep the minimized file so ordinary `go test` exercises it.

The engine's generated coverage corpus lives in the Go build cache and is used during fuzzing; user seeds and saved failures under `testdata/fuzz` are the durable project corpus. Use `f.Add` for small readable seeds and the corpus directory for larger byte inputs.

Run active fuzzing on a platform with supported coverage instrumentation. Inspect the current `go help testflag` and package documentation for budgets and minimization settings rather than caching every flag in project guidance.

## Primary references

- [Go fuzzing](https://go.dev/doc/security/fuzz/)
- [Go `testing` package: fuzzing](https://pkg.go.dev/testing#hdr-Fuzzing)
- [Go fuzzing tutorial](https://go.dev/doc/tutorial/fuzz)
