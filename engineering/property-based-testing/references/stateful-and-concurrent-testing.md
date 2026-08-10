# Stateful and concurrent property testing

Use a state model when correctness depends on operation history. Use controlled schedules when correctness depends on interleaving.

## State-machine model

Define six parts together:

1. **Model state** — the smallest independent representation of expected behavior
2. **Real system** — a fresh or reliably reset instance under test
3. **Commands** — mutations, queries, lifecycle events, and expected failures
4. **Preconditions** — when each command is legal in the current model state
5. **Transitions** — how a successful command changes the model
6. **Postconditions and invariants** — observations compared after commands and across the sequence

Keep the model simpler than the real system. It should encode the contract, not reproduce caches, indexes, retries, or internal data structures.

## Generate legal sequences

Generate commands from the current model state. Reuse generated handles, keys, and objects through the framework's bundle, command, or state-machine abstraction. Select legal commands through their preconditions rather than drawing impossible commands inside the body and discarding them.

Include commands that expose lifecycle boundaries and interactions:

- create, update, query, and delete
- duplicate or conflicting operations
- empty and capacity states
- reset, close, reconnect, retry, and recovery
- invalid operations whose rollback is observable

Check command postconditions immediately, then check global invariants after each step. End-of-sequence checks alone can hide the operation that first corrupted state.

## Observe sequence coverage

Classify more than sequence length. Record:

- frequency of every command
- important adjacent command pairs
- transitions into empty, full, error, recovered, and terminal states
- key collisions, repeated handles, and stale references
- successful and rejected preconditions

A command present in the generator but absent from observed sequences is not covered.

## Shrink and isolate

Reset the real system for every generated test case and every shrink attempt. Keep cleanup deterministic and idempotent. Commands should carry only the data needed to replay them; shrinkers need to delete commands and simplify their arguments without leaving hidden external state.

A useful minimal counterexample identifies the shortest causal sequence, not merely the smallest individual values.

## Concurrent schedules

Establish the sequential model first. Then define the concurrent correctness relation explicitly: linearizability, serializability, at-most-once effects, ordering, idempotent retry, or another owned contract.

Control interleavings through the framework's scheduler, parallel-command support, deterministic executor, or a test seam around synchronization. Generate operations and schedule decisions; wall-clock sleeps provide neither reach nor replay.

Compare the concurrent history with a permitted sequential history or another precise model. Completion order, invocation order, and response order are different observations; assert only the ordering the contract owns.

Capture the schedule, seed, command sequence, and environment with a failure. A concurrency property without deterministic replay remains diagnostic evidence, not a stable regression test.

## Completion criterion

A stateful model is complete when every command has a precondition, transition, and observable postcondition; every important state and transition appears in collected evidence; each shrink attempt starts from isolation; failures reduce to a replayable causal sequence; and concurrent tests state and check a precise ordering model under a controlled schedule.
