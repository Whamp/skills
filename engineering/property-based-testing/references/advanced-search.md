# Advanced search

Use an advanced search mode only after the ordinary generator, category evidence, and named counterfeit show a specific reach problem.

## Match the bottleneck

| Bottleneck | Search mode | Evidence of improvement |
| --- | --- | --- |
| Valid inputs are sparse | Correct-by-construction or specification-derived generator | Higher valid-case rate with the same domain and useful shrinking |
| Failure has a numeric distance | Targeted property testing | Objective approaches the failure boundary and kills the counterfeit faster |
| Domain is small and finite | Exhaustive or enumerative generation | Every value or bounded structure is checked |
| Unknown branches or behaviors matter | Coverage-guided backend or property fuzzing | New relevant behavior is reached under the same budget |
| Interactions among categories are missing | Coverage requirements or combinatorial descriptions | Named category combinations appear |
| Stateful bug needs a rare history | Weighted commands, model-aware generation, or longer sequence search | Causal transition appears and still shrinks |

## Targeted search

Choose an objective that correlates with falsification, such as allocation size, depth, numeric error, collision count, imbalance, or distance to a threshold. Label distinct objectives separately; one scalar that mixes unrelated risks gives the search an ambiguous direction.

Keep the assertion unchanged. The objective guides where to search, while the property still decides pass or fail.

## Exhaustive small scopes

Prefer enumeration when the bounded domain is tractable and the boundary is meaningful: protocol flags, small state machines, short token streams, enum combinations, or structures up to a fixed depth. State the bound in the property name or test configuration so exhaustive evidence is not mistaken for an unbounded proof.

## Coverage-guided search

Use runtime feedback when the important behaviors are not known well enough to encode as categories. Preserve the property oracle, seed or corpus, sanitizer configuration, and minimized reproducer. Coverage growth is search evidence; the property remains the correctness oracle.

## Compare fairly

Run the baseline and advanced search against the same named counterfeit and time budget. Keep the advanced mode only when it improves relevant category reach, time-to-failure, or counterexample quality enough to justify its complexity.

## Completion criterion

Escalation is complete when the original reach bottleneck is measured, the chosen mode addresses that bottleneck, and a same-budget comparison shows better relevant reach or faster discrimination without weakening replay or shrinking.
