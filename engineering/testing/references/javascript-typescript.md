# JavaScript and TypeScript testing

Use the repository's existing runner, assertions, file layout, and setup hooks. Add a dependency only through the project's dependency policy. Choose the execution environment before choosing helpers.

## Choose the environment

- **Node** — pure logic, server code, and platform APIs that run in Node. This is Vitest's default environment.
- **DOM emulator** — component behavior that needs a DOM but not browser layout or browser-specific implementation. Vitest supports `jsdom` and `happy-dom`; their APIs and fidelity differ.
- **Real browser** — focus, layout, CSS, screenshots, real event behavior, or browser API compatibility. Vitest Browser Mode is a separate test project, not a Node test environment.
- **End-to-end browser** — a deployed or cross-boundary user journey. Use [end-to-end browser testing](e2e.md), not a component test stretched across the system.

A faster environment is wrong when it cannot express the risk. Record what the selected environment emulates or omits.

## Test components as users

With Testing Library, query by accessible role and name first, then label or visible text. Use a test ID when no user-facing query expresses a stable contract. Prefer `findBy` for an element that should appear asynchronously, `getBy` for an element that should exist now, and `queryBy` for absence.

Drive interactions through the project's user-event or browser helper. Assert accessible or visible outcomes rather than component state, hook calls, CSS structure, or framework internals.

## Control state and boundaries

Await every promise whose result affects the assertion. A test that finishes before its callback or rejection runs is green without evidence.

Reset only state the test changes:

- restore spies and replaced implementations
- unstub environment variables and globals
- restore real timers and system time
- clear singleton, module, or storage state through the repository's supported seam

Use fake timers only when time is the boundary under test; advance them through the runner's documented API and flush the relevant async work. Use `vi.setSystemTime` when the contract depends on the current date, then restore it.

Test owned collaborators together when their integration is the claim. Replace an external HTTP boundary through the project's existing MSW handlers or transport seam. Keep request matching and response payloads limited to behavior the client consumes.

## Use snapshots deliberately

Use an explicit assertion for a small value or contract field. Use a focused snapshot when the serialized structure itself is the reviewed artifact. Use a browser screenshot when visual rendering is the contract.

Review snapshot changes as code changes. Normalize only nondeterministic fields that are outside the contract. A large snapshot that no reviewer can explain is not an oracle.

## Route generated search

For broad values, asynchronous schedules, or stateful command sequences, load `property-based-testing` and its fast-check adapter. Keep named examples that document important scenarios; generated search supplements them.

## Primary references

- [Vitest test environments](https://vitest.dev/guide/environment.html)
- [Vitest Browser Mode](https://vitest.dev/guide/browser/)
- [Vitest mocking](https://vitest.dev/guide/mocking.html)
- [Vitest `vi` utilities](https://vitest.dev/api/vi.html)
- [Testing Library queries](https://testing-library.com/docs/queries/about/)
- [Mock Service Worker](https://mswjs.io/docs/)
