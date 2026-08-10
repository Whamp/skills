---
name: e2e-testing
description: Design and operate Playwright end-to-end tests for critical user journeys, boundary integration, failure artifacts, and flake-resistant CI.
disable-model-invocation: true
---

# End-to-End Testing

Use Playwright to prove that a real user journey works across the boundaries most likely to fail together. Keep the suite small enough to trust and fast enough to run where failures still influence development.

## 1. Name the journey and risk

State the behavior in user language before writing browser steps:

```text
Journey: <who does what and reaches which observable outcome>
Risk: <integration or regression this browser test can expose>
Boundaries: <browser, API, auth, database, queue, third party>
Existing coverage: <what unit or integration tests already prove>
```

Choose end-to-end coverage when the risk lives in wiring, browser behavior, deployed configuration, or a sequence spanning components. Prefer a narrower test when one component can prove the same contract.

Complete when the test has one named journey, one failure it can discriminate, and a reason browser-level coverage is necessary.

## 2. Establish the test contract

Assert stable outcomes visible to the user or at a public boundary:

- successful navigation or durable state change
- rendered content or accessible state
- persisted data observed through the UI or a supported API
- a specific recovery path after a realistic failure

Use role, label, text, and explicit test-id locators in that order of semantic value. Treat CSS structure, generated classes, timing, and implementation-only network details as unstable unless they are the contract under test.

Keep assertions close to the action that makes them true. Replace sleeps with Playwright's locator assertions, URL assertions, response waits, or application-specific readiness signals.

Complete when each assertion names a contract and fails if the intended user outcome is removed or counterfeited.

## 3. Control state and dependencies

Make each test independently repeatable:

- create unique data per test or worker
- authenticate through a reusable fixture or storage state when login itself is outside the journey
- clean up durable records, or generate isolated records that expire safely
- avoid order dependence and shared mutable accounts
- make parallel workers safe before enabling parallel execution

Keep real the boundaries whose integration risk motivates the test. Replace only dependencies that are unavailable, destructive, expensive, or intentionally fault-injected. Route replacements through Playwright network controls or the application's supported test seam, and state what realism was traded away.

Complete when the test passes alone, in a different order, and under the suite's intended parallelism without relying on residue from another test.

## 4. Build a deep test interface

Put recurring setup and domain actions behind fixtures or focused helpers. A helper should express a meaningful operation such as `createPaidAccount` or `checkoutCart`, not merely rename `page.click`.

Use page objects when they hide substantial selector, navigation, or synchronization detail shared by several tests. Keep a journey readable at the domain level:

```ts
import { expect, test } from "./fixtures";

test("an editor publishes a draft", async ({ draft, editorPage, page }) => {
  await editorPage.openDraft(draft.id);
  await editorPage.publish();

  await expect(page.getByRole("status")).toHaveText("Published");
  await expect(page).toHaveURL(/\/articles\//);
});
```

Follow the repository's existing fixture, locator, and file-layout conventions before introducing a new abstraction.

Complete when repeated mechanics have one owner while the test still tells the journey without opening helper implementations.

## 5. Exercise failure and discrimination

Before trusting the test, demonstrate that it goes red for the targeted defect. Use the cheapest safe counterfeit:

- temporarily disable the state transition
- return a realistic error from one boundary
- remove the rendered outcome
- redirect to the wrong destination
- run against the known pre-fix revision

Add explicit coverage for a failure path only when recovery behavior matters to users or operations. Avoid duplicating every validation permutation already covered below the browser layer.

Complete when evidence shows the test fails for the named regression and passes after the correct behavior is restored.

## 6. Operate the suite

Use retries to measure instability, not conceal it. Preserve Playwright traces, screenshots, video, console output, and relevant server logs on the first retry or final failure according to the project's CI budget.

When a test flakes:

1. reproduce with its recorded seed, worker count, project, and repeat settings
2. inspect the trace before changing waits
3. classify the cause as application race, test race, leaked state, environment failure, or unstable contract
4. fix the cause and stress the test with repeated and parallel runs
5. quarantine only with an owner, issue, and removal condition

Tune projects and browser coverage to actual compatibility risk. Run a tight critical path on every change; schedule broader browser or environment matrices when their cost would slow the primary feedback loop.

Complete when failures leave actionable artifacts, retries do not turn persistent defects green, and the suite fits a measured CI budget.

## Review Checklist

- [ ] Every test protects a named critical journey or integration risk.
- [ ] Locators and assertions express user-visible contracts.
- [ ] State is isolated and parallel-safe.
- [ ] Fixtures and page objects hide substantial repeated mechanics.
- [ ] Real and replaced boundaries are intentional and documented.
- [ ] At least one red result proves each new test discriminates its target defect.
- [ ] Failure artifacts are retained and sufficient for diagnosis.
- [ ] Flakes have causes, owners, and removal conditions rather than silent retries.
