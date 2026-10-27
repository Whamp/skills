---
name: first-principles
description: Interactive first-principles reasoning that separates facts, constraints, assumptions, analogies, and unknowns before rebuilding options from fundamentals.
disable-model-invocation: true
version: 1.0.0
author: Will Hampson
license: MIT
metadata:
  hermes:
    tags: [thinking, mental-models, strategy, problem-framing, decision-making, grilling]
    related_skills: [grill-with-docs, ideation, zoom-out]
---

# First Principles Thinking

**Function before form:** establish the outcome, separate grounded truths from inherited methods, then rebuild options. Use this for decisions whose frame needs examination; answer factual lookups and execute clear instructions directly.

## Conversation

Ask **one question at a time**, attach a concrete recommended answer, then **wait**. Use the user's domain and challenge defaults for better fit, not novelty. Preserve the real goal while changing methods; expert practice is evidence to examine, not baggage to dismiss.

Check discoverable facts in files, code, logs, documentation, or external sources before asking the user. Label evidence and uncertainty explicitly. A plausible claim or unverified tool limit is an assumption, not a foundation.

## Process

Work through these steps across the conversation. Advance when the current step's completion condition holds; a single reply need not complete the process.

### 1. Frame

State the actual problem, underlying function, inherited form, desired outcome, and central assumption to question. Tighten a vague frame before decomposing it. Usually start by asking what outcome counts as a win, propose a success condition, and wait.

**Complete when:** the goal and function are explicit, the inherited form is named, and the user has supplied or confirmed the decision's success condition.

### 2. Separate and ground

Build a compact inventory:

- **Facts:** verified truths in this context.
- **Hard constraints:** grounded physical, mathematical, legal, economic, technical, budget, time, or safety limits. Respect them unless changed at their source.
- **Soft constraints:** preferences, conventions, and organizational habits; challenge their necessity while retaining their stated value.
- **Assumptions:** unverified beliefs to test.
- **Analogies:** borrowed patterns that can inspire, but do not prove, an answer.
- **Unknowns:** answerable gaps for research or experiment.
- **Goal:** the outcome to preserve.

For each important claim, examine its evidence, why it must hold, what changes if it is false, and what is possible without the conventional solution. Go one or two layers deeper; stop when further decomposition cannot change the decision. Ask the user only about unresolved intent or information unavailable through tools.

**Complete when:** important claims are classified and supported or explicitly uncertain. Distill a small set of foundational truths and name the assumptions or conventions being discarded or tested.

### 3. Rebuild

Generate options from those truths rather than preserving the old category with cosmetic changes. Include at least one option that breaks from the inherited analogy. For important components, consider a solution from another domain that can be substituted or recombined.

For each option, state its grounding principles, rejected assumption, any cross-domain substitution, upside, main risk, and cheapest test. An unconventional option must still be plausible; a conventional solution can win on the evidence. Settle the solution's shape before tuning details.

**Complete when:** viable options meet the real goal and hard constraints, and their differences and tradeoffs are explicit.

### 4. Pressure-test and act

Challenge the leading option against hard constraints, its load-bearing assumption, falsifying evidence, and reversibility. Identify what would convince a skeptical reviewer.

End with one concrete next experiment, prototype, document, or decision; state the evidence required and an **if evidence, then commit/pivot/kill** decision rule. Decomposition is unfinished until it produces rebuilt options and an actionable test.

**Complete when:** the recommendation has a named risk, a cheapest evidence-producing next step, and a decision rule tied to the success condition.

## Preserve durable reasoning

Durable strategy, architecture direction, non-obvious tradeoff, inherited-form breakthrough, or input to a PRD/issue/ADR → read [artifact routing and packet template](references/artifacts.md). Keep casual reasoning in chat.
