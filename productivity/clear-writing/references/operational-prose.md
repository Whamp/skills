# Operational prose

Use this reference when a reader must execute technical text correctly on one read. It adapts controlled-language techniques from ASD-STE100 for software operations. It does not claim ASD-STE100 compliance.

## Classify each passage

| Passage | Purpose | Default form |
| --- | --- | --- |
| Procedure | Tell the reader what to do | Imperative steps |
| Explanation | Describe a state, behavior, cause, or result | Declarative paragraphs |

A document can contain both. Keep explanatory notes separate from executable steps so the reader can distinguish information from action.

## Preserve operational truth

Apply the core skill's **preserve information over shape** rule before these structural rules. Clarity does not permit invented prerequisites, causes, outcomes, measurements, or implementation details.

Keep code, identifiers, commands, flags, file paths, configuration keys, product names, quoted errors, and log lines exact.

## Write executable procedures

- Start each step with an imperative verb: "Run the migration."
- Give each step one action. Combine actions only when they must occur at the same time.
- Put a required condition before the command when the reader must know it before acting.
- Present steps in execution order.
- State the expected result separately when it helps the reader decide whether to continue.
- Use complete grammar. Concision must not produce telegraphic fragments.

Before:

> Increase the timeout if the network is slow.

After:

> If the network is slow, increase the timeout.

Before:

> Back up the database, run the migration, and restart the service.

After:

> 1. Back up the database.
> 2. Run the migration.
> 3. Restart the service.

## Explain operations

- Keep one topic in each paragraph.
- Introduce one main fact at a time.
- Name the actor and action when they matter.
- Connect causes, effects, and dependencies explicitly.
- Use passive voice when the actor is unknown or when another subject must stay in focus.
- Use the tense that preserves the actual sequence and state.

Do not turn an explanation into a procedure merely because it appears beside one.

## State requirements and uncertainty precisely

Choose modal verbs for their meaning:

- **must**: a requirement
- **can**: a capability or permission
- **should**: a recommendation
- **may**, **might**, or **could**: genuine uncertainty or possibility
- **will**: a future result supported by the procedure or system contract

State what is unknown when the evidence cannot support a narrower claim. Never promote uncertainty into fact to make a sentence sound firmer.

## Put warnings before dangerous operations

Place a warning immediately before the operation it governs. Start the warning with the command or required condition, then state the concrete consequence.

> CAUTION: Do not run this migration against production. It deletes rows that are absent from the source.

Use an established warning level when the project defines one. Otherwise, state the danger directly without inventing a severity label.

## Make errors actionable

Give the reader three pieces of information when they are known:

1. What failed
2. Why it failed
3. What to do next

Do not guess at a cause. Preserve quoted errors and log text exactly.

Before:

> Something went wrong. Please try again later.

After:

> Upload failed because the service account lacks write access. Grant write access, then retry the upload.

## Keep terminology stable

Use one term for one concept and one meaning for each term. Preserve established distinctions such as `check`, `validate`, and `verify` when they name different operations. Remove synonym rotation only when several words refer to the same concept.

Review noun stacks longer than three words. Rewrite them when a preposition makes the relationship clearer:

> connection pool timeout configuration value

becomes:

> timeout value for the connection pool

Keep domain terms when they are the shortest precise words. Define an unfamiliar term once when the reader needs the definition.

## Use length limits as review signals

Review procedural sentences longer than 20 words and descriptive sentences longer than 25 words. Split them when the split preserves the logical relationship and improves execution. These are diagnostic thresholds, not general hard limits.

Use a vertical list when it makes a sequence, set of alternatives, or group of conditions easier to scan. Keep natural sentence rhythm in explanations instead of forcing every sentence to the same length.

## Completion check

Before delivery, confirm that:

- Every prerequisite precedes the step it governs.
- Every step has one executable action or a justified simultaneous pair.
- Warnings precede dangerous operations and name the consequence.
- Requirements, permissions, recommendations, and uncertainty use their intended meanings.
- Technical literals remain exact.
- Long sentences received deliberate review.
- No unsupported operational detail entered the draft.

## Strict ASD-STE100 requests

Apply strict ASD-STE100 only when the user explicitly requests it. Full vocabulary control requires the official dictionary and a compliance review. Describe ordinary use of this reference as STE-inspired operational prose, not certified ASD-STE100.

Official standard: <https://www.asd-ste100.org/>
