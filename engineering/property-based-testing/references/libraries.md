# PBT Libraries by Language

## Quick Reference

| Language | Library | Import/Setup |
|----------|---------|--------------|
| Python | Hypothesis | `from hypothesis import given, strategies as st` |
| JavaScript/TypeScript | fast-check | `import fc from 'fast-check'` |
| JavaScript/TypeScript | @fast-check/vitest | `import { it, fc } from '@fast-check/vitest'` |
| Rust | proptest | `use proptest::prelude::*` |
| Go | rapid | `import "pgregory.net/rapid"` |
| Java | jqwik | `@Property` annotations, `import net.jqwik.api.*` |
| Kotlin | Kotest | `io.kotest.property.*` |
| Scala | ScalaCheck | `import org.scalacheck._` |
| C# | FsCheck | `using FsCheck; using FsCheck.Xunit;` |
| Elixir | StreamData | `use ExUnitProperties` |
| Haskell | QuickCheck | `import Test.QuickCheck` |
| Clojure | test.check | `[clojure.test.check :as tc]` |
| Ruby | PropCheck | `require 'prop_check'` |
| C++ | RapidCheck | `#include <rapidcheck.h>` |

### Alternatives

| Language | Alternative | Notes |
|----------|-------------|-------|
| Haskell | Hedgehog | Integrated shrinking, no type classes |
| Rust | quickcheck | Simpler API, per-type shrinking |
| Go | gopter | ScalaCheck-style, more explicit generators |

## Smart Contract Testing (EVM/Solidity)

| Tool | Type | Description |
|------|------|-------------|
| Echidna | Fuzzer | Property-based fuzzer for EVM contracts |
| Medusa | Fuzzer | Next-gen fuzzer with parallel execution |

```solidity
// Echidna property example
function echidna_balance_invariant() public returns (bool) {
    return address(this).balance >= 0;
}
```

See [secure-contracts.com](https://secure-contracts.com) for tutorials.

## Installation

**Python**:
```bash
pip install hypothesis
# or: uv add --dev hypothesis
```

**JavaScript/TypeScript**:
```bash
npm install -D fast-check
# Recommended with vitest:
npm install -D @fast-check/vitest
```

**Rust** (add to Cargo.toml):
```toml
[dev-dependencies]
proptest = "1.0"
```

**Go**:
```bash
go get pgregory.net/rapid
```

**Java** (Maven):
```xml
<dependency>
  <groupId>net.jqwik</groupId>
  <artifactId>jqwik</artifactId>
  <version>1.9.3</version>
  <scope>test</scope>
</dependency>
```

**Kotlin** (Gradle):
```kotlin
testImplementation("io.kotest:kotest-property:5.9.0")
```

**Clojure** (deps.edn):
```clojure
{:deps {org.clojure/test.check {:mvn/version "1.1.2"}}}
```

**Haskell**:
```bash
cabal install QuickCheck
```

## Detecting Existing Usage

Search for PBT library imports in the codebase:

```bash
# Multi-language detection (comprehensive)
rg "from hypothesis import|fast-check|@fast-check|proptest|rapid\.Check|gopter|jqwik|@Property|kotest\.property|StreamData|ExUnitProperties|QuickCheck|test\.check|ScalaCheck|FsCheck|PropCheck|echidna_" \
  --type py --type js --type ts --type rust --type go --type java \
  --type-add 'sol:*.sol' --type-add 'kt:*.kt' --type-add 'ex:*.ex' --type-add 'exs:*.exs'
```

Individual language checks:

```bash
# Python
rg "from hypothesis import" --type py

# JavaScript/TypeScript
rg "from 'fast-check'|from '@fast-check" --type js --type ts

# Rust
rg "use proptest|use quickcheck" --type rust

# Go
rg "pgregory.net/rapid|leanovate/gopter" --type go

# Java/Kotlin
rg "@Property|kotest\.property" --type java --type-add 'kt:*.kt'

# Clojure
rg "test.check" --type clojure

# Solidity (Echidna)
rg "echidna_" --glob "*.sol"
```
