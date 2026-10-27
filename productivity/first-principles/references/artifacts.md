# Artifact routing

Save a reasoning packet when the reasoning is worth preserving. Use `FIRST-PRINCIPLES.md` for one major packet in a small project, or `docs/first-principles/<topic>.md` for multiple packets; add `docs/first-principles/INDEX.md` only when a map is useful.

Route the resolved insight to its appropriate home:

- `CONTEXT.md`: stable domain vocabulary.
- ADR: a durable, hard-to-reverse decision.
- First-principles packet: reasoning from fundamentals before or around a decision.
- Issue / Intent Contract: tactical implementation intent and evidence requirements.
- `NAPKIN.md`: long-term system memory in repositories that use it.

## Packet

Use the following structure, preserving verified facts and uncertainty:

```markdown
# First Principles: <Topic>

## Problem
<What we are deciding, building, or improving>

## Function
<Underlying outcome independent of current form>

## Inherited Form
<Default category, interface, process, or analogy>

## Facts
<Verified truths>

## Hard Constraints
<Grounded limits>

## Soft Constraints / Assumptions
<Preferences, conventions, and unverified beliefs, labeled separately>

## First Principles
<Small foundational set>

## Rebuilt Options
<Options derived from the foundation>

## Recommended Direction
<Best current answer and why>

## Biggest Remaining Risk
<Load-bearing assumption or failure mode>

## Cheapest Test
<Smallest experiment that produces useful evidence>

## Decision Rule
If <evidence>, then <commit/pivot/kill>.
```

**Complete when:** durable reasoning has the appropriate home, with its facts, uncertainty, recommendation, risk, test, and decision rule intact.
