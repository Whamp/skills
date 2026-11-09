# Opener examples

## Bad and good drafts

Bad, for a PR already titled "Retry expired sessions":

```markdown
## Summary

This PR implements expired-session retries.

- Refresh credentials.
- Retry requests.
- Add tests.
```

The heading, preamble, title repetition, and bullet dump delay the reason to care.

Good:

> Requests failed when a session expired mid-upload. The client now refreshes the session and retries the upload once.

Bad:

```markdown
The settings screen has been updated.

There is now an error message.

The validation logic has also changed.
```

Multiple paragraphs and vague implementation notes hide the user-visible result.

Good:

> Invalid email addresses could be saved without feedback. Settings now explains the error beside the email field and keeps the last valid address.

## Simon Willison's real examples

The following five openers are quoted verbatim from Simon Willison's [Hide your slop PR descriptions behind details-summary](https://simonwillison.net/2026/Nov/9/details-summary/), 9 November 2026. They illustrate his editorial choices; the parenthetical notes describe what followed and are outside the quotations.

- [datasette PR #3052: Redesign row page as a vertical list of fields](https://github.com/simonw/datasette/pull/3052) — "The row page showed its single row as a one-row table. For wide tables, like a 46-column GitHub `repos` table, that scrolled far off to the right and left most of the page blank." (then a screenshot)
- [datasette PR #3043: Pagination bar showing which rows are on the current page](https://github.com/simonw/datasette/pull/3043) — "Table pages that span more than one page now make it obvious where you are, and offer navigation at the top of the page as well as the bottom." (plus screenshot)
- [datasette PR #3042: Load edit-tools.js on demand via a small loader](https://github.com/simonw/datasette/pull/3042) — "`edit-tools.js` (~220KB) was loaded on every table, row and database page, even for users who couldn’t edit anything. Now only load it for users who can edit when they first interact with an edit feature (including mouse over an edit link)."
- [datasette-agent PR #51: register_agent_reference_types plugin hook](https://github.com/datasette/datasette-agent/pull/51) — "Lets plugins add their own kinds of item to the `#` tagging in the chat composer using a new `register_agent_reference_types(datasette)` plugin hook."
- [llm PR #1838: Add llm openai endpoint add/list/remove/path commands](https://github.com/simonw/llm/pull/1838) — "Adds commands for managing the records in `extra-openai-models.yaml`, so OpenAI-compatible endpoints can be saved from the command line instead of by hand-editing YAML." (then copied `--help` output)
