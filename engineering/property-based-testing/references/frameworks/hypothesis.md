# Python adapter: Hypothesis

Use the Hypothesis version, pytest configuration, profiles, and shared strategies already present in the repository. Inspect `pyproject.toml`, the lockfile, `conftest.py`, and nearby tests before adding settings.

Official reference: [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/)

## Core shape

```python
from collections import Counter

from hypothesis import given, strategies as st


@given(st.lists(st.integers()))
def test_sort_is_ordered_and_preserves_values(values):
    result = sort_values(values)

    assert all(left <= right for left, right in zip(result, result[1:]))
    assert Counter(result) == Counter(values)
```

Keep assertions inside the generated test so Hypothesis can associate them with the drawn case and shrink the failure.

## Domain construction

- Use built-in strategies and `st.from_type()` where they express the full domain.
- Use `st.builds()` for independent fields and `@st.composite` when later draws depend on earlier values.
- Use `st.recursive()` for recursive structures with a deliberate leaf budget.
- Use `.filter(predicate)` for a clear local predicate; Hypothesis can optimize some filters.
- Use `assume(condition)` for a test-level precondition discovered after drawing. An early return counts as a passing case, so it hides the assertion rather than rejecting the case.
- Prefer a reusable composite strategy over `st.data()` when the dependency can be expressed before the test body; composite values report and shrink more clearly.

Hypothesis distinguishes the strategy **domain** from its engine-controlled **distribution**. Keep the supported domain broad. Use bounds only for the contract or measured cost rather than trying to hand-tune realistic frequencies.

Domain guidance: [Domain and distribution](https://hypothesis.readthedocs.io/en/latest/explanation/domain.html) and [Adapting strategies](https://hypothesis.readthedocs.io/en/latest/tutorial/adapting-strategies.html)

## Search evidence

- `event(label)` records risk-bearing categories in test statistics.
- `target(score, label=...)` guides search toward a numeric objective correlated with failure.
- `@example(...)` records a named explicit case. Explicit cases do not shrink; use them for durable boundaries and regressions rather than routine coverage decoration.
- The example database replays prior failures automatically when enabled by the project configuration.

## Stateful tests

`RuleBasedStateMachine` provides `@initialize`, `@rule`, `@precondition`, and `@invariant`. `Bundle` carries generated objects between rules; `consumes()` models removal. Put rule eligibility in `@precondition` so the machine selects legal actions instead of discarding inside a rule.

Official reference: [Stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html)

## Replay and settings

Capture the falsifying example, active profile, command, and Hypothesis version. Prefer automatic database replay or a stable `@example` for permanent regressions. `@reproduce_failure` is a temporary debugging aid tied to the Hypothesis version that created its blob.

Start with project settings. Change `max_examples`, deadlines, phases, or stateful step counts only from measured cost or reach. A registered profile takes effect only through the project's explicit loading mechanism or pytest integration; inspect that mechanism rather than assuming an environment variable alone activates it.

Official reference: [Replaying failures](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html) and [Settings](https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.settings)

## Completion criterion

A Hypothesis test is ready when its strategy domain matches the contract, assumptions remain productive, risk categories appear in statistics, a planted failure shrinks clearly, replay works under the project profile, and the normal pytest command passes.
