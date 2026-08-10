# Other property-testing frameworks

Prefer a property-testing dependency and conventions already present in the repository. Inspect the manifest, lockfile, test configuration, imports, and nearby tests; use current official documentation for generator, shrink, filter, replay, and state-machine semantics.

| Ecosystem | Common framework | Official reference |
| --- | --- | --- |
| Haskell | QuickCheck | [Hackage](https://hackage.haskell.org/package/QuickCheck) |
| Haskell | Hedgehog | [Hackage](https://hackage.haskell.org/package/hedgehog) |
| C# and F# | FsCheck | [FsCheck docs](https://fscheck.github.io/FsCheck/) |
| Scala | ScalaCheck | [ScalaCheck](https://scalacheck.org/) |
| Kotlin | Kotest property testing | [Kotest docs](https://kotest.io/docs/proptest/property-based-testing.html) |
| Elixir | StreamData | [HexDocs](https://stream-data.hexdocs.pm/StreamData.html) |
| Clojure | test.check | [test.check](https://github.com/clojure/test.check) |
| Ruby | PropCheck | [PropCheck](https://github.com/Qqwy/ruby-prop_check) |
| C++ | RapidCheck | [RapidCheck](https://github.com/emil-e/rapidcheck) |
| EVM/Solidity | Echidna | [Building Secure Contracts](https://secure-contracts.com/program-analysis/echidna/index.html) |

When no framework is installed, choose only after confirming the repository's runtime, test runner, dependency policy, maintenance expectations, and need for stateful or concurrent search. Present the leverage sentence from the main workflow before changing the manifest.

Framework terminology differs:

- A QuickCheck-style `Arbitrary` instance may couple default generation and per-type shrinking.
- Hedgehog-family and integrated-shrinking frameworks derive shrinking from generator structure or internal choices.
- Native fuzzers may provide coverage-guided search and corpus replay while the test still supplies the property oracle.
- Smart-contract invariant fuzzers preserve state across generated transaction sequences unless configured statelessly.

Verify these semantics for the installed version instead of translating APIs mechanically from another adapter.

## Completion criterion

An adapter choice is complete when the existing or proposed framework fits the repository's test runner, its generation and shrinking semantics are confirmed from current official docs, replay works in a minimal project-native property, and no dependency version or command is copied from this reference instead of the environment.
