---
name: first-principles
description: Use when the user explicitly wants first-principles thinking, wants to escape inherited assumptions, or asks to decompose a strategy/product/design/problem from fundamentals. Runs an interactive one-question-at-a-time grill that separates facts, assumptions, constraints, analogies, and unknowns, then rebuilds options from irreducible truths.
version: 1.0.0
author: Will Hampson
license: MIT
metadata:
  hermes:
    tags: [thinking, mental-models, strategy, problem-framing, decision-making, grilling]
    related_skills: [grill-with-docs, ideation, zoom-out]
---

# First Principles Thinking

## Overview

First-principles thinking is a way to stop reasoning from analogy and start reasoning from the underlying truths of the situation. The move is simple but uncomfortable: break the problem apart, separate what is actually known from what is merely inherited, then rebuild from the pieces.

Do **not** turn this into philosophical cosplay. The goal is not to reduce every problem to atoms. Going one or two levels deeper than most people is often enough. The useful question is not “what is the ultimate metaphysical truth?” It is: **what must be true here, what are we assuming, and what can we build if we stop copying the default shape?**

The sharpest practical move is **function before form**. Do not ask “how do we make a better version of the existing thing?” until you have asked “what function is this supposed to perform?” First-principles work changes the trajectory when the inherited form is wrong; continuous improvement is for when the existing frame is basically right.

This skill is interactive, sharp, one question at a time, with a recommended answer attached. It is for strategy, product design, architecture, learning, business decisions, and any situation where the user suspects the current frame is inherited rather than chosen.

## When to Use

Use this skill when the user explicitly says things like:

- “Use first principles.”
- “Help me think from first principles.”
- “I think we’re making assumptions.”
- “Break this down to fundamentals.”
- “What are we taking for granted?”
- “I want to reason this through instead of copying the normal way.”
- “Grill me on this idea from first principles.”

Also use it when the task is a strategy/product/design decision and the user is trapped in analogy-language: “everyone does it this way,” “the standard approach is,” “we need a dashboard/app/process because that’s what this category has,” etc.

Do **not** use it for:

- Quick factual lookups.
- Straight execution tasks where the intent is already clear.
- Cases where code/docs can answer the question directly. Read the source first, then grill only the remaining intent gaps.

## Core Principle

A first principle is an irreducible truth **within the problem context**: something you can treat as foundational for this decision because it is physically, mathematically, legally, economically, technically, or empirically grounded.

A first principle is **not**:

- A best practice.
- A tradition.
- A market convention.
- A tool limitation you have not verified.
- A preference dressed up as truth.
- A thing competitors do.
- A thing “users expect” without evidence.

The useful distinction:

| Category | Meaning | How to handle it |
|---|---|---|
| Fact | Verified true in this context | Build on it |
| Hard constraint | Physics, law, API limit, budget, time, safety | Respect it unless changed upstream |
| Soft constraint | Convention, preference, org habit, local norm | Challenge it |
| Assumption | Belief not yet verified | Mark and test it |
| Analogy | Borrowed pattern from another domain/product/company | Useful inspiration, not proof |
| Unknown | Answerable but not yet known | Research or experiment |
| Goal | Desired outcome | Preserve it while changing methods |

## Operating Mode

### 0. Start with the actual problem

Before decomposing anything, restate the problem in plain language:

```text
We are trying to decide/build/fix/improve: <problem>.
The function we actually need is: <underlying job/outcome>.
The inherited/default form seems to be: <current category/interface/process/analogy>.
The outcome we actually care about is: <goal>.
```

If the user gave a vague frame, tighten it before grilling. Bad: “Let’s identify the atomic unit.” Better: “We’re trying to decide whether this app needs a dashboard, or whether the real need is faster parent/director coordination.”

### 1. Split the problem into buckets

Create an assumption inventory:

```text
Facts:
- ...

Hard constraints:
- ...

Soft constraints / conventions:
- ...

Assumptions:
- ...

Analogies we may be copying:
- ...

Unknowns we can verify:
- ...

Goal / success condition:
- ...
```

If a bucket can be filled by reading files, docs, logs, code, papers, product pages, or current data, do that before asking the user. **Do not** outsource discoverable facts to the human.

### 2. Push each item down one level

For every important claim, ask:

- Why must this be true?
- What evidence proves it?
- Is this a law, a platform limit, a budget limit, a user need, or just habit?
- If this were false, what would change?
- What would we do if we could not use the conventional solution?

Use the “one or two layers deeper” rule. Stop once going deeper stops changing the decision.

### 3. Identify the first-principles set

Distill the smallest useful foundation:

```text
First principles for this problem:
1. <truth we can build on>
2. <truth we can build on>
3. <truth we can build on>

Not first principles:
- <assumption/convention we are discarding or testing>
```

Keep the set small. Five strong primitives beat twenty mushy ones.

### 4. Rebuild from the primitives

Generate options from the truths, not from the old solution category. For each important component, ask whether another domain has already solved that subproblem better. Innovation often comes from substituting one inherited part with a better part from somewhere else.

For each option:

```text
Option: <name>
Built from principles: <which truths make it viable>
Breaks from analogy: <what inherited pattern it rejects>
Substitutes/recombines: <component borrowed from another domain, if any>
Main upside: <why it might be better>
Main risk: <what could fail>
Cheapest test: <smallest evidence-producing next step>
```

Favor weird-but-plausible options. First-principles work is pointless if all roads lead back to “copy the incumbent with nicer styling.”

### 5. Pressure-test the rebuilt answer

Challenge the top option:

- What hard constraint could kill it?
- What assumption is most load-bearing?
- What would make this obviously wrong?
- What is the fastest way to find out?
- Is the solution reversible?
- What evidence would convince a skeptical reviewer?

### 6. End with the next experiment

A good session ends with an action, not just clarity.

```text
Recommended next move:
- <one concrete experiment / doc / prototype / decision>

Evidence required:
- <what would prove/disprove the core assumption>

Decision rule:
- If <evidence>, then <commit/pivot/kill>.
```

## Optional Output Artifact

Create a `FIRST-PRINCIPLES.md` only when the session produces reasoning worth preserving: a product strategy decision, architecture direction, non-obvious tradeoff, inherited-form breakthrough, or input to a PRD/issue/ADR.

Do **not** create one for casual thinking. That becomes note-sprawl.

Preferred paths:

```text
FIRST-PRINCIPLES.md                  # one major reasoning packet in a small repo/project
docs/first-principles/<topic>.md     # multiple packets
docs/first-principles/INDEX.md       # optional map when multiple packets exist
```

Artifact boundaries:

- `CONTEXT.md` → stable domain vocabulary, not reasoning scratchwork.
- ADR → durable hard-to-reverse decision.
- `FIRST-PRINCIPLES.md` → reasoning from fundamentals before or around a decision.
- Issue / Intent Contract → tactical implementation intent and evidence requirements.
- `NAPKIN.md` → long-term system memory if the repo uses it.

## Conversational Rules

1. **Ask one question at a time.** Never batch numbered grill questions.
2. **Attach a recommendation to every question.** The user should react to your proposed answer, not stare at a blank page.
3. **Separate facts from assumptions loudly.** Do not let plausible claims slide into the foundation.
4. **Use tools for knowable facts.** If the answer is in code, docs, logs, or web sources, go look.
5. **Translate abstractions into the user’s domain.** Strategy people do not need ontology theater.
6. **Challenge defaults without being contrarian for sport.** Best practices are often compressed experience; test them, don’t sneer at them.
7. **Preserve the real goal while attacking the inherited method.** The point is not novelty. The point is better fit.

## First Question Template

Start most sessions like this:

```text
First-principles frame:
We are trying to <actual goal>.
The function we need is <underlying job/outcome>.
The inherited/default form appears to be <status quo>.
The thing we should not assume yet is <suspect assumption>.

Question 1:
What outcome must be true for this to count as a win?

My recommended answer:
<short, concrete success condition>
```

Then wait.

## Output Templates

### Assumption Inventory

```text
Facts:
- ...

Hard constraints:
- ...

Soft constraints / conventions:
- ...

Assumptions:
- ...

Analogies:
- ...

Unknowns to verify:
- ...
```

### First-Principles Packet

Use this as the body of `FIRST-PRINCIPLES.md` when the reasoning is worth preserving.

```text
# First Principles: <Topic>

## Problem
- <what we are trying to decide/build/improve>

## Function
- <underlying job/outcome independent of current form>

## Inherited Form
- <default category/interface/process we may be copying>

## Facts
- <verified truths>

## Hard Constraints
- <physics/law/budget/API/safety/time constraints>

## Soft Constraints / Assumptions
- <habits/preferences/conventions/unverified beliefs>

## First Principles
1. <truth we can build on>
2. <truth we can build on>
3. <truth we can build on>

## Rebuilt Options
- <options generated from principles, not inherited form>

## Recommended Direction
- <best current answer and why>

## Biggest Remaining Risk
- <load-bearing assumption or failure mode>

## Cheapest Test
- <smallest experiment that produces useful evidence>

## Decision Rule
- If <evidence>, then <commit/pivot/kill>.
```

### Rebuild Options Table

| Option | Built from principles | Rejects assumption | Substitutes/recombines | Upside | Risk | Cheapest test |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

## Useful Question Bank

Use these one at a time, not as a dump.

### Framing

- What are we actually trying to make true?
- What function are we trying to perform, independent of the current form?
- What current form/category/interface are we accidentally preserving?
- What would a win look like if we ignored the normal solution category?
- Are we solving the user’s problem, or reproducing the industry’s interface?
- What is the smallest version of the outcome that matters?

### Decomposition

- What parts of this are physical, legal, mathematical, economic, technical, or social?
- Which constraints are truly external, and which are self-imposed?
- What is the raw material here? Time, attention, trust, money, data, compute, relationships?
- What is the unit of value being transformed?

### Assumptions

- What are we assuming because everyone else does it this way?
- What has to be true for the current plan to work?
- Which assumption would embarrass us if false?
- What are we treating as expensive because the market bundles it that way?

### Rebuild

- If we could not use the standard solution, what would we do?
- What would this look like if built around the bottleneck instead of the category label?
- What option becomes possible once we remove the inherited constraint?
- What other domain has already solved this subproblem?
- What component could we substitute or recombine from outside the current category?
- What is the cheapest thing that produces the desired outcome?

### Evidence

- What would prove this principle is real in this context?
- What is the fastest falsifying test?
- What observation would make us abandon this plan?
- What evidence would make this safe to hand to an implementation agent?

## Common Pitfalls

1. **Going too atomic.** You usually do not need physics, chemistry, or metaphysics. Go only as deep as changes the decision.

2. **Smuggling assumptions into the foundation.** “Users need a dashboard” is not a first principle. “Directors need to know which parent conversations need attention” might be.

3. **Confusing analogy with evidence.** Competitor behavior can inspire hypotheses. It does not prove what should be built.

4. **Ignoring accumulated wisdom.** First-principles thinking is not “throw away everything experts know.” It is “understand which expert rules are grounded and which are historical baggage.”

5. **Stopping at critique.** Decomposition without rebuilding is just clever negativity. Always rebuild options.

6. **Asking the user to answer discoverable facts.** If docs, code, data, or web sources can answer it, inspect them first.

7. **Prematurely optimizing.** First principles should clarify the shape of the solution before tuning details.

8. **Projecting the current form forward.** “Flying cars” is the trap: preserving the car shape while wanting the function of flight. Ask for the desired function, then let the form disappear.

9. **Treating preferences as truths.** Preferences matter, but label them as preferences.

10. **Batching the grill.** One question. Recommended answer. Wait.

11. **Novelty addiction.** A conventional solution rebuilt from real primitives may still be best. That is fine. The win is knowing why.

## Verification Checklist

Before ending a first-principles session, verify:

- [ ] The actual goal and underlying function are stated plainly.
- [ ] The inherited form/category is identified instead of silently preserved.
- [ ] Facts, hard constraints, soft constraints, assumptions, analogies, and unknowns are separated.
- [ ] Discoverable facts were checked with tools where possible.
- [ ] The first-principles set is small and actually foundational.
- [ ] At least one rebuilt option breaks from the inherited analogy.
- [ ] The recommended option has a risk and cheapest test.
- [ ] A `FIRST-PRINCIPLES.md` packet was created only if the reasoning is durable enough to preserve.
- [ ] Any resolved insight was routed to the right artifact: `CONTEXT.md`, ADR, `FIRST-PRINCIPLES.md`, issue/Intent Contract, or `NAPKIN.md`.
- [ ] The session ends with a next experiment or decision rule.
