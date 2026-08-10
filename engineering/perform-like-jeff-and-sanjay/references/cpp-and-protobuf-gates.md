# C++ and protobuf gates

Use the C++ sections only for C++ targets and the Protocol Buffers section only for protobuf targets. Ground each concrete facility in the portable mechanism selected from [technique gates](technique-gates.md), the target toolchain, and the measured workload.

## C++ representations and containers

### Flat hash tables

- **Mechanism:** contiguous control/entry storage reduces node allocations and pointer chasing; grouped metadata may permit SIMD matching.
- **Gate:** unordered lookup fits the API, hashing discriminates real keys, and address/iterator stability is unnecessary.
- **Loses when:** stable references or ordering are required, values are expensive to relocate, inputs trigger poor hashes, or the language's existing map already uses a comparable representation.
- **Conditional example:** `absl::flat_hash_map` or `absl::flat_hash_set` may beat node-based C++ maps. This does not transfer mechanically to Python dictionaries, Go maps, or other runtimes.

### B-trees

- **Mechanism:** several ordered entries share one node, reducing pointer overhead and improving locality.
- **Gate:** ordered associative semantics are required and node stability is not.
- **Loses when:** entries are very large, mutation/movement dominates, or unordered lookup better matches the workload.
- **Conditional example:** `absl::btree_map` and `absl::btree_set`.

### Inlined small collections

- **Mechanism:** store a measured small cardinality inside the owner and allocate only on overflow.
- **Gate:** most instances fit the chosen inline capacity.
- **Loses when:** element size or owner population makes inline backing expensive, or overflow is common.
- **Conditional examples:** `absl::InlinedVector`, an inlined bit vector, or a small-map/set implementation. Choose capacity from a distribution, not from an example.

### Compact metadata, dense arrays, bitsets, and intrusive links

- **Mechanism:** constrain size/capacity metadata, index bounded domains directly, pack booleans, or embed collection links in owned elements.
- **Gate:** bounds, ownership, and collection semantics are explicit.
- **Loses when:** bounds can grow, domains are sparse, element lifetime is external, or the original structure supplied ordering/uniqueness not preserved by the replacement.
- **Conditional examples:** a 32-bit-size vector, `std::array`/`std::vector`, bitsets, and intrusive lists. System-scale savings depend on object population.

## C++ ownership and lifecycle

### Views and function references

- **Mechanism:** pass non-owning ranges, strings, or callables without copying or allocating.
- **Gate:** the callee neither retains nor takes ownership and the backing object outlives the call.
- **Loses when:** asynchronous or stored use outlives the owner, mutation invalidates the view, or ownership transfer is the real contract.
- **Conditional examples:** `std::string_view`, `std::span`, `absl::Span`, and `absl::FunctionRef`.

### `reserve` versus `resize`

- **Mechanism:** allocate backing storage once; `reserve` changes capacity, while `resize` also constructs elements.
- **Gate:** expected size is known and the fill strategy matches element construction cost.
- **Loses when:** either call is repeated one element at a time, capacity is grossly overestimated, or `resize` constructs expensive values only to overwrite them.
- **Rule:** prefer one `reserve` plus `push_back`/`emplace_back` for expensive construction; use one `resize` when direct indexed filling of constructed slots is cheaper and valid.

### Moves, pointers, indices, and scratch-backed results

- **Mechanism:** consume ownership with `std::move`, borrow stable objects, sort compact handles, or return a view into caller scratch.
- **Gate:** source use, owner lifetime, relocation, and aliasing are known.
- **Loses when:** the moved-from value is needed, a container reallocates, or the scratch is mutated before the consumer finishes.
- **Rule:** expose the lifetime in the API and tests; a view is not an owned result.

### Stable versus unstable algorithms

- **Mechanism:** choose an algorithm that avoids temporary copies or extra storage.
- **Gate:** the removed semantic property is unnecessary or reproduced explicitly.
- **Loses when:** callers observe equal-element order.
- **Conditional example:** replacing `std::stable_sort` with `std::sort` is valid only when stability is irrelevant or a secondary key defines the full order.

### Arenas and stack storage

- **Mechanism:** bulk-allocate similarly lived subobjects or avoid heap allocation for small scope-bounded objects.
- **Gate:** lifetimes align and stack/object size remains safe.
- **Loses when:** short-lived objects enter a long-lived arena, arenas retain high-water memory, or stack frames become large.
- **Rule:** pair the allocation choice with lifetime and peak-retention measurements.

## C++ code size and compiler controls

### Inlining and out-of-line fallbacks

- **Mechanism:** inline only a tiny dominant path; share uncommon, allocation, formatting, registration, and failure behavior once.
- **Gate:** call-site duplication or instruction-cache pressure is measured, or the common path is proven call-sensitive.
- **Loses when:** a call is added to the dominant tight path without offsetting footprint gains.
- **Conditional tools:** ordinary function boundaries plus narrowly used compiler `inline`/`noinline` attributes. Attributes are last-resort evidence tools, not policy.

### Template deduplication

- **Mechanism:** move argument-independent work to a non-template base/helper or replace a low-value template dimension with a runtime parameter.
- **Gate:** many instantiations emit materially similar machine code.
- **Loses when:** compile-time specialization unlocks a meaningful algorithm or removes a dominant branch.
- **Verify:** inspect instantiation counts, symbols, binary bytes, runtime, and build/link time.

### Raw pointers, locals, manual unrolling, and SIMD

- **Mechanism:** expose aliasing and loop structure or process several values per instruction.
- **Gate:** profiles and annotated assembly prove the compiler miss; alignment, bounds, and architecture support are explicit.
- **Loses when:** safety, portability, code size, or a newer compiler's optimization becomes worse.
- **Rule:** keep scalar fallback and correctness tests; compare generated code before and after.

### RAII critical sections

- **Mechanism:** declaration order controls whether destructors execute before or after a lock guard releases the mutex.
- **Gate:** destruction outside the lock is thread-safe and does not violate atomicity.
- **Loses when:** the object depends on protected state after unlock.
- **Rule:** measure the effective critical section, including callees and destructors, rather than lexical braces alone.

### Cache-line alignment

- **Mechanism:** `alignas` or padding isolates independently mutated fields.
- **Gate:** coherence evidence identifies false sharing.
- **Loses when:** every object becomes much larger or frequently co-read fields split across lines.
- **Rule:** use target-platform cache-line information and measure memory plus contention.

### Rich status wrappers and production checks

- **Mechanism:** keep rare failure construction out of a hot success path, or use a compact closed result when rich errors are unnecessary.
- **Gate:** the path is proven hot and callers do not need recoverable detail; any impossible failure is enforced by construction.
- **Loses when:** diagnostics, compatibility, or production safety weakens.
- **Conditional examples:** `absl::Status`/`StatusOr`, exception-like result wrappers, and debug assertions. Changing an always-on check to a debug-only check is a semantic change, not a routine optimization.

## Protocol Buffers

### Use protobuf at a real serialization boundary

- **Mechanism:** native contiguous records avoid generated code, tags, accessor layers, object trees, and per-submessage allocation when serialization is unnecessary.
- **Gate:** the data does not need wire compatibility, persistence, reflection-like behavior, or protobuf interchange at that point.
- **Loses when:** replacement creates repeated conversion or duplicates a required schema boundary.
- **Rule:** keep protobuf at genuine edges; choose an in-memory domain representation from the access pattern.

### Flatten message hierarchy selectively

- **Mechanism:** remove wrapper submessages, tags, lengths, allocations, and tree traversal.
- **Gate:** hierarchy adds no needed semantic grouping or evolution boundary.
- **Loses when:** flattening damages schema clarity, ownership, or compatibility.
- **Rule:** preserve existing field identities; do not renumber deployed fields for performance.

### Assign field numbers and integer encodings from distributions

- **Mechanism:** low field numbers shorten tags; varint, zigzag, and fixed-width encodings trade wire bytes against decode work.
- **Gate:** designing a new/evolvable schema with measured sign and magnitude distributions.
- **Loses when:** existing field numbers change, small values move to wasteful fixed width, or large/negative values use expensive varints.
- **Rule:** reserve low numbers for frequent fields in new schemas. Benchmark wire size and encode/decode CPU.

### Pack repeated numeric fields

- **Mechanism:** one length plus values avoids a tag per element; fixed-width payload size can permit one allocation.
- **Gate:** repeated numeric primitives and compatible schema/runtime behavior.
- **Loses when:** compatibility expectations differ or varint element count still forces growth.
- **Conditional detail:** proto2 requires packed annotation; proto3 commonly defaults repeated numeric primitives to packed. Verify the target runtime and edition.

### Distinguish text from bytes

- **Mechanism:** `bytes` represents opaque binary data and avoids text-specific validation or semantics.
- **Gate:** the field is truly non-text.
- **Loses when:** callers rely on UTF-8/text behavior or schema meaning becomes false.
- **Rule:** model semantics first; performance follows the truthful type.

### Alias or segment large fields

- **Mechanism:** a view aliases serialized backing storage; a cord/rope-like representation shares and appends segments.
- **Gate:** backing lifetime is enforceable and field size/access patterns favor the representation.
- **Loses when:** views outlive input, random/contiguous access is common, fields are small, or reference-count/tree overhead dominates.
- **Conditional examples:** protobuf C++ view fields and `absl::Cord`. Benchmark the exact runtime and annotation support.

### Use protobuf arenas and object reuse

- **Mechanism:** allocate nested messages, strings, and repeated fields from shared chunks; reuse capacity across loop iterations.
- **Gate:** object lifetimes align and reset semantics are correct.
- **Loses when:** bulk lifetime retains too much memory or a reused message keeps a pathological maximum capacity.
- **Rule:** clear logical state, measure retained capacity, and periodically reconstruct only when evidence supports it.

### Keep cold messages serialized or parse a projection

- **Mechanism:** defer full materialization or parse only wire-compatible fields needed by the consumer.
- **Gate:** messages are long-lived and infrequently accessed, or the consumer needs a small stable subset.
- **Loses when:** frequent access repeatedly parses data, mutation is common, or unknown-field preservation is required.
- **Rule:** state whether parsing is avoided or deferred; discard unknown fields only when their preservation is unnecessary.

### Replace protobuf maps conditionally

- **Mechanism:** represent entries on the wire, then build a native runtime index suited to the operation mix.
- **Gate:** hot runtime lookup justifies conversion and protobuf map syntax/semantics are not required.
- **Loses when:** conversion duplicates large data, messages are used once, or map interoperability is valuable.
- **Rule:** measure conversion plus steady-state access; protobuf maps are not categorically forbidden.

### Split schema files only for verified footprint behavior

- **Mechanism:** smaller generated units may prevent unrelated message code from entering a binary.
- **Gate:** the target compiler/linker/package behavior demonstrably retains whole generated units.
- **Loses when:** splitting adds dependency or schema-management complexity without changing linked output.
- **Rule:** inspect generated symbols and link maps; do not assume one toolchain's behavior is universal.
