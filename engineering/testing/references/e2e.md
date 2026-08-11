# End-to-end browser testing

Use a browser test when the risk lives in a user journey, browser behavior, deployment configuration, or wiring across components. Prefer a narrower test when one component can prove the same contract.

## Name the journey

Record the reason for browser-level evidence:

```text
Journey: <who does what and reaches which observable outcome>
Risk: <integration or regression this browser test can expose>
Boundaries: <browser, API, auth, database, queue, third party>
Existing evidence: <what narrower tests already prove>
```

Keep the suite centered on critical journeys and boundary failures rather than repeating every validation case below the browser layer.

**Complete when:** the journey, risk, and browser-only reason are explicit.

## Assert as a user

With Playwright, prefer role, label, text, and intentional test-id locators over CSS or XPath structure. Use locator assertions, URL assertions, response waits, or application readiness signals instead of fixed sleeps.

Assert durable outcomes:

- visible or accessible state
- successful navigation
- persisted data observed through the UI or a supported public API
- a specific recovery path after a realistic failure

Keep each assertion near the action that makes it true. Network calls and DOM structure are assertions only when they are themselves the contract.

**Complete when:** every assertion describes an outcome a user or public client can observe.

## Isolate state and boundaries

Create unique data per test or worker. Reuse authenticated storage state or a fixture when login is outside the journey. Clean up durable records, or use isolated records with a safe expiry. Make tests independent of order and shared accounts before adding parallel workers.

Keep real the boundaries that motivate the test. Replace only a dependency that is unavailable, destructive, expensive, or intentionally fault-injected. Route replacements through Playwright network controls or a supported application seam, and record the realism lost.

**Complete when:** the test passes alone, in a changed order, and under its intended parallelism without residue from another test.

## Hide mechanics, not behavior

Put repeated setup and domain actions behind fixtures or focused helpers. A helper should name a meaningful operation such as `createPaidAccount` or `publishDraft`, not rename a click.

Use a page object only when it hides substantial selector, navigation, or synchronization detail shared across tests. Keep the journey readable without opening helper implementations.

**Complete when:** repeated mechanics have one owner and the test body still tells the user story.

## Prove and operate

Use the main testing process to show the journey goes red for its named counterfeit. On CI failure, preserve the Playwright trace plus the screenshots, video, console output, network evidence, and server logs justified by the project's budget.

Treat retries as classification: a test that passes on retry is flaky, not healthy. Reproduce it with the recorded project, seed, worker count, and repeat settings; inspect the trace; classify application race, test race, leaked state, environment failure, or unstable contract; then stress the fix.

Quarantine only through the tracked process in [test suite maintenance](test-suite-maintenance.md).

## Primary references

- [Playwright best practices](https://playwright.dev/docs/best-practices)
- [Playwright auto-retrying assertions](https://playwright.dev/docs/test-assertions)
- [Playwright trace viewer](https://playwright.dev/docs/trace-viewer)
