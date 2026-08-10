---
name: clear-writing
description: Write or revise durable human-facing prose with plain force. Use for docs, READMEs, API guides, runbooks, commit messages, PR descriptions, reports, error messages, UI copy, or explicit requests for clearer, shorter, sharper, more direct, or less AI-sounding prose.
---

# Clear Writing

Write prose with **plain force**: specific facts, strong verbs, short paths from subject to action, and no ceremonial filler.

## Editing Loop

For new prose, draft once, then edit. For existing prose, edit directly.

1. Identify the reader, purpose, and the action or understanding the prose should support.
2. Preserve information over shape. Keep supported facts, uncertainty, intent, established voice, domain distinctions, and technical literals. Leave unknowns unknown instead of adding plausible specifics.
3. Make the main claim explicit. If there is no main claim, write one before polishing.
4. Put actors before actions where possible. Prefer active voice unless passive voice keeps the right subject in focus.
5. Replace vague praise, empty hedging, and abstractions with concrete facts. Keep uncertainty that changes the meaning.
6. Omit needless words, throat-clearing, recap sentences, and generic transitions.
7. Read the result for clusters of AI tells: puffery, empty "-ing" phrases, promotional adjectives, ornate metaphors, excessive bolding, and conclusion boilerplate.
8. Return the revised prose first. Add notes only when the user asked for explanation or when a tradeoff matters.

Completion criterion: the revision preserves the source's information and uncertainty. Every sentence must state a fact, give an instruction, name a decision, or help the reader act or understand. If a sentence only sounds helpful, delete or replace it.

## Fast Checks

- **Active voice**: "The server rejected the token" beats "The token was rejected by the server."
- **Positive form**: "The request failed after 30 seconds" beats "The request did not complete successfully."
- **Concrete language**: "Cache entries expire after 10 minutes" beats "The system improves freshness."
- **Needless words**: "To configure auth, set `API_KEY`" beats "In order to configure authentication, you will need to set `API_KEY`."
- **Emphasis**: Put the strongest word or consequence at the end of the sentence.

## Examples

Before: "This commit implements the functionality for ensuring that user authentication is properly handled, showcasing robust error handling capabilities."

After: "Add user authentication with error handling."

Before: "It is important to note that the API might potentially return an error in certain situations."

After: "The API returns an error when the token expires."

## Reference Routing

Load only the reference needed for the branch:

| Branch | Read |
| --- | --- |
| Sentence structure, active voice, paragraphs, concision | [`03-elementary-principles-of-composition.md`](references/elements-of-style/03-elementary-principles-of-composition.md) |
| Grammar, punctuation, possessives, comma rules | [`02-elementary-rules-of-usage.md`](references/elements-of-style/02-elementary-rules-of-usage.md) |
| Headings, quotations, formatting conventions | [`04-a-few-matters-of-form.md`](references/elements-of-style/04-a-few-matters-of-form.md) |
| Word choice and commonly misused words | [`05-words-and-expressions-commonly-misused.md`](references/elements-of-style/05-words-and-expressions-commonly-misused.md) |
| Detecting AI-sounding prose in ordinary writing | [`ai-writing-patterns.md`](references/ai-writing-patterns.md) |
| Runbooks, procedures, troubleshooting, migrations, warnings, error messages, recovery instructions, or localization-ready technical text | [`operational-prose.md`](references/operational-prose.md) |
| Wikipedia articles, citations, markup, edit summaries, or AFC drafts | [`wikipedia-ai-artifacts.md`](references/wikipedia-ai-artifacts.md) |

Most edits need only [`03-elementary-principles-of-composition.md`](references/elements-of-style/03-elementary-principles-of-composition.md).

When context is tight, edit from the fast checks first. Load a reference only when the draft has a specific problem the fast checks do not settle.

## AI Tells

Replace these with specifics:

- Puffery: pivotal, crucial, vital, testament, enduring legacy
- Empty analysis: ensuring, showcasing, highlighting, underscoring, reflecting, fostering
- Promotional adjectives: groundbreaking, seamless, robust, cutting-edge, innovative
- Overused abstractions: leverage, landscape, realm, tapestry, multifaceted, nuanced
- Boilerplate endings: in summary, in conclusion, overall, future outlook
- Decorative formatting: emoji, excessive bullets, bold on ordinary words

Do not ban a word mechanically. If the word names a real thing, keep it. If it inflates weak content, replace it with the fact it is hiding.
