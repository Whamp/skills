# Go adapter: rapid

Inspect `go.mod`, `go.sum`, and nearby tests. Reuse the project's rapid version, test flags, failure-file conventions, and helper generators when present. For new adoption, follow [library selection](../../SKILL.md#choose-the-library), then add `pgregory.net/rapid` in the module that owns the tests and import it from `*_test.go` files. Go has no separate dev-dependency section; record changes in `go.mod` and `go.sum` and run properties through `go test`.

Check the project's license policy: Rapid uses [MPL-2.0](https://github.com/flyingmutant/rapid#license). If it is incompatible, propose another suitable library. Native Go fuzzing is a coverage-guided companion, not an automatic replacement for structured property tests.

Official reference: [rapid package documentation](https://pkg.go.dev/pgregory.net/rapid)

## Core shape

```go
package sorting

import (
    "reflect"
    "sort"
    "testing"

    "pgregory.net/rapid"
)

func TestSortMatchesStandardOracle(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        values := rapid.SliceOf(rapid.Int()).Draw(t, "values")

        expected := append([]int(nil), values...)
        sort.Ints(expected)
        result := SortValues(values)

        if !reflect.DeepEqual(result, expected) {
            t.Fatalf("SortValues(%v) = %v, want %v", values, result, expected)
        }
    })
}
```

Clone generated slices, maps, and pointers when the system may mutate them; failure reporting and minimization need the original generated case.

## Domain construction

Rapid's imperative `Draw` API makes dependencies explicit: draw an outer value, then use it to configure later generators. Use named draws consistently so failure output and replay remain legible. Construct sparse constraints directly; reserve skipped cases for state-dependent actions that are temporarily illegal.

Rapid biases generation toward small values and edge cases and minimizes failures automatically. Keep contractual and measured bounds in the generator rather than assuming realistic production frequencies are the right search distribution.

## Stateful tests

Use `t.Repeat` for random action sequences. Keep a separate model, register named actions, and use `t.Skip` for an action whose precondition is false in the current model state. Check postconditions in the action and global invariants through the state-machine hook or after each relevant action.

Classify action frequencies and important state transitions in test logs or explicit counters when reach is uncertain.

Official reference: [rapid state-machine example](https://github.com/flyingmutant/rapid/blob/master/example_statemachine_test.go)

## Replay

Rapid persists and reruns minimized failures by default. Capture the generated fail file or reported seed, exact `go test` command, rapid version, and any `-rapid.*` flags. Use the reported `-rapid.failfile` or `-rapid.seed` form for diagnosis, then retain the general property and any useful explicit regression.

## Completion criterion

A rapid property is ready when dependent draws match the contract, mutable inputs are isolated, important actions and states occur, a planted failure minimizes and replays through the failure file or seed, and the relevant `go test` command passes.
