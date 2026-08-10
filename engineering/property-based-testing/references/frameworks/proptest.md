# Rust adapter: proptest

Use the proptest version, feature flags, configuration, and regression-file conventions already present in `Cargo.toml`, the lockfile, and nearby tests.

Official reference: [The Proptest Book](https://proptest-rs.github.io/proptest/)

## Core shape

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn sort_matches_the_standard_oracle(
        values in prop::collection::vec(any::<i32>(), 0..100)
    ) {
        let mut expected = values.clone();
        expected.sort();

        let result = sort_values(values);

        prop_assert_eq!(result, expected);
    }
}
```

The range in this example is a local execution budget, not a universal domain recommendation. Match bounds to the contract and measured project cost.

A `Strategy` defines both generation and a per-value `ValueTree` for shrinking. Proptest is not QuickCheck-style per-type shrinking.

## Domain construction

- Use ranges, regular-expression strategies, collection strategies, and `any::<T>()` for direct domains.
- Use `prop_compose!` to name reusable compositions.
- Use `prop_flat_map` when one generated value constrains another, such as a collection and valid index.
- Use `prop_map` for constructive transformations that retain a useful simplicity relation.
- Use `prop_filter` or `prop_assume!` when accepted values remain common. Rejected shrink candidates can stop further simplification, so prefer construction for sparse constraints.

Official reference: [Strategy basics](https://proptest-rs.github.io/proptest/proptest/tutorial/strategy-basics.html), [Higher-order strategies](https://proptest-rs.github.io/proptest/proptest/tutorial/higher-order.html), and [Filtering](https://proptest-rs.github.io/proptest/proptest/tutorial/filtering.html)

## Shrinking and replay

Exercise a planted failure and inspect the minimal failing case. Transformations can change what “simpler” means; a string-to-number mapping, for example, may shrink according to the source representation rather than the semantic number.

Respect the project's failure persistence configuration and tracked regression files. Capture the minimal case, source file, test name, seed or persistence entry, exact command, and proptest version. Keep regression entries that still reproduce an owned contract; remove stale entries only with evidence that the general property preserves the case.

Official reference: [Shrinking basics](https://proptest-rs.github.io/proptest/proptest/tutorial/shrinking-basics.html) and [Test runner](https://proptest-rs.github.io/proptest/proptest/tutorial/test-runner.html)

## Stateful tests

When the installed proptest ecosystem exposes state-machine support, follow its current command/transition API and the conceptual model in [stateful and concurrent testing](../stateful-and-concurrent-testing.md). Confirm the exact API from the installed version because state-machine surfaces can evolve independently of the core macros.

## Completion criterion

A proptest property is ready when its strategy and `ValueTree` preserve the claimed domain, sparse constraints are constructed productively, a planted failure shrinks to an intelligible regression, persistence replay works, and the relevant Cargo test command passes.
