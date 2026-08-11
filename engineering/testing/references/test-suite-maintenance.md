# Test suite maintenance

Review a test by the evidence it contributes, not by style or score alone. Start with one sentence:

> This test protects **[contract]** from **[failure]** through **[observation]**.

If a blank cannot be filled from the specification, code, history, or failure record, investigate before preserving or deleting the test.

## Diagnose the weakness

| Finding | Evidence to gather | Preferred repair |
| --- | --- | --- |
| Wrong or obsolete contract | Current specification, callers, and product decision | Update the contract and test together, or remove the obsolete test. |
| Insensitive oracle | Counterfeit implementation still passes | Assert the missing public outcome from an independent source. |
| Tautological expectation | Test repeats the production algorithm | Replace it with a worked literal, reference model, invariant, or independent implementation. |
| Implementation coupling | Internal refactor breaks the test while behavior stays stable | Move observation to the public seam; remove private call counts and choreography. |
| Flakiness | Repeated failures vary with seed, order, worker, time, or environment | Reproduce, classify, and fix the underlying race, leaked state, unstable contract, or infrastructure fault. |
| Excess setup | Fixture fields or helpers do not affect the contract | Narrow data and split helpers around named domain operations. |
| Suspected duplication | Tests share coverage or kill the same current mutants | Compare contracts, historical regressions, setup, and diagnostics before removing either. |

A smell is a search lead, not a deletion warrant. Refactoring may improve coupling, cohesion, and readability without increasing fault detection, and careless cleanup can introduce new smells or weaken coverage.

## Use coverage and mutation as probes

Coverage shows that execution reached code; it does not show that the oracle could detect a defect. Inspect uncovered risk-bearing branches, error paths, and boundaries, then add a test only when a missing contract justifies one.

Mutation testing is most useful when it presents a small number of actionable survivors in changed or high-risk code. For each survivor, ask whether it represents a plausible defect and whether an existing public observation should detect it. Add or strengthen a test for the behavior, not for the mutation operator. Do not chase a maximal mutation score or interpret a small score change without accounting for equivalent mutants, filtering, runtime, and flakes.

Flaky tests can make mutation outcomes unknown or inconsistent. Stabilize or classify them before comparing scores.

## Decide: keep, refactor, quarantine, or remove

**Keep** a test that contributes unique contract, regression, boundary, or diagnostic evidence at acceptable cost.

**Refactor** when the evidence is valuable but its setup, oracle, coupling, or runtime obscures that value. Preserve discrimination by running the refactored test against the original counterfeit, pre-fix revision, or relevant mutants.

**Quarantine** only when an unhealthy test blocks trusted feedback and cannot be repaired immediately. Record an issue, owner, reason, deadline, and exit condition. Keep it running in a suitable local or scheduled lane when possible. Quarantine ends in repair, replacement, or deliberate removal.

**Remove** only when all applicable conditions hold:

1. the protected contract is obsolete, or another test demonstrably protects the same risk through an equal or stronger public observation
2. the test contributes no unique setup, boundary, regression, or diagnostic signal
3. the replacement fails on the old defect or named counterfeit when that evidence is reproducible
4. the relevant suite remains green and its runtime or maintenance benefit is measured
5. references, fixtures, quarantine records, and ownership metadata are updated with the removal

Do not delete a test solely because another test covers the same lines or kills the same current mutants. Reduction metrics on one revision do not reliably predict which future failures a test will detect.

## Flake investigation

1. Capture the exact test, seed, order, worker count, retry, environment, and first failure.
2. Reproduce with repetition and the relevant parallelism; inspect original logs before changing waits.
3. Classify application race, test race, leaked state, order dependence, time/randomness, external dependency, resource contention, or infrastructure failure.
4. Fix the cause and prove the test still goes red for its protected defect.
5. Stress the repair, then remove quarantine and retries that only masked the problem.

Retries classify instability; they do not cure it.

## Research basis

- [SWT-Bench](https://arxiv.org/abs/2406.12952) validates bug reproduction through fail-before and pass-after behavior.
- [Practical Mutation Testing at Scale](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/) supports incremental, filtered, actionable mutants during code review.
- [Does mutation testing improve testing practices?](https://arxiv.org/abs/2103.07189) studies actionable mutants and their relationship to real faults.
- [GitLab's quarantine process](https://handbook.gitlab.com/handbook/engineering/testing/quarantine-process/) requires tracking, ownership, and resolution.
- [Evaluating Test-Suite Reduction in Real Software Evolution](https://doi.org/10.1145/3213846.3213875) found current reduction metrics can miss future failed-build detection.
- [Test code refactoring unveiled](https://doi.org/10.1007/s10664-024-10577-y) found maintainability improvements without a significant code- or mutation-coverage improvement.
