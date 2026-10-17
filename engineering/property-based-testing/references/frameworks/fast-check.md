# JavaScript and TypeScript adapter: fast-check

Inspect `package.json`, the lockfile, test setup, and nearby properties. Reuse the project's fast-check version and test connector when present. For new adoption, follow [library selection](../../SKILL.md#choose-the-library), then add `fast-check` as a development dependency in the package that owns the tests. Direct `fc.assert(...)` calls work with the existing runner; a connector such as `@fast-check/vitest` is optional, not a separate generation engine.

Official reference: [fast-check documentation](https://fast-check.dev/docs/introduction/getting-started/)

## Core shape

```typescript
import assert from 'node:assert/strict';
import fc from 'fast-check';

fc.assert(
  fc.property(fc.array(fc.integer()), (values) => {
    const result = sortValues(values);
    const expected = [...values].sort((left, right) => left - right);

    assert.deepEqual(result, expected);
  }),
);
```

An `Arbitrary` couples generation with shrinking. Compose arbitraries so a failure can shrink through the same structure that generated it.

## Domain construction

- Use `fc.record`, `fc.tuple`, arrays, dictionaries, and built-in domain arbitraries for independent structure.
- Use `.chain(...)` when later values depend on earlier ones; keep the dependency small enough to retain useful shrinking.
- Use `.map(...)` for constructive transformations whose simpler sources produce simpler outputs.
- Use `.filter(...)` or `fc.pre(...)` when accepted cases remain common. `fc.pre` cancels a run; `maxSkipsPerRun` bounds unproductive search.
- Treat generated values as immutable test inputs. Clone before passing them to mutating code so shrinking and failure reporting retain the original case.

Official reference: [Arbitraries](https://fast-check.dev/docs/core-blocks/arbitraries/) and [Properties](https://fast-check.dev/docs/core-blocks/properties/)

## Search evidence

Use `fc.statistics(...)` to classify generated values and inspect risk-bearing categories. Set `numRuns`, size, timeout, or interruption settings through existing project configuration first; override one property only when measured reach or runtime justifies it.

For async behavior, use `fc.asyncProperty`. For controlled promise interleavings, use `fc.scheduler()` and schedule the functions or promises whose ordering the contract owns.

Official reference: [Runners and statistics](https://fast-check.dev/docs/core-blocks/runners/) and [Scheduler](https://fast-check.dev/docs/advanced/race-conditions/)

## Stateful tests

Model-based tests use commands with a precondition and a `run(model, real)` operation. Generate command sequences with `fc.commands(...)` and execute them with the matching model runner. Keep the model independent and collect evidence that each command and important transition runs.

Model-based replay needs the assertion `seed` and `path`; command arbitraries also report a `replayPath`.

Official reference: [Model-based testing](https://fast-check.dev/docs/advanced/model-based-testing/)

## Replay

Capture the reported seed, path, counterexample, fast-check version, exact test command, and—when commands are used—replay path. Pass seed and path through the project's established connector or `fc.assert` parameters for diagnosis. Promote stable minimized cases to ordinary examples when they communicate the contract.

Official reference: [Reading test reports](https://fast-check.dev/docs/tutorials/quick-start/read-test-reports/)

## Completion criterion

A fast-check property is ready when its arbitrary reaches the claimed domain without mutating generated values, risk categories are visible, a planted failure shrinks clearly, seed/path replay works through the project connector, and the normal JavaScript or TypeScript test command passes.
