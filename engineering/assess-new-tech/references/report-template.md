# Assessment report template

Fill every section. Replace each placeholder in angle brackets. Keep the recommendation and grades at the top, so a reader can decide from the first screen.

```markdown
# Assessment: <technology> <exact version>

**Recommendation: <Adopt | Trial | Hold | Reject>.** <One or two sentences: why, and what would change the answer.>

## Grades

Scale: 1 to 5, where 5 is best for adoption.

| Criterion | Grade | Evidence |
| --- | --- | --- |
| API nuance | <n> | <concepts used, options compared, friction-log entries> |
| Type safety | <n> | <deliberate mistakes and whether the type check caught each; escapes needed> |
| Testability | <n> | <test setup, mocking, speed> |
| Cyclomatic complexity | <n> | <tool>: <before> → <after>; <branching moved into configuration> |
| Docs quality | <n> | <coverage, doc errors found, agent-loadable docs> |
| Deployment changes | <n> | <dependencies, size change, build or infrastructure changes, rollback> |

<Where an independent reviewer disagreed with a grade, and how it was settled.>

## The technology

<Core claim in two sentences. Maturity: release status, cadence, maintainers, license, blocking issues. Breaking changes from the version in use, if any.>

## The problem chosen

<The site, why it is the gnarliest problem that fits, and the rejected candidates with reasons.>

## Verification

| Check | Command | Baseline | Proof of concept |
| --- | --- | --- | --- |
| <build, type check, lint, tests, parity, manual run> | `<command>` | <result> | <result> |

## Friction log

- <What went wrong> → <what resolved it>

## Strongest argument against

<The best case against the recommendation.>

## Sources

- <Primary source links>
```
