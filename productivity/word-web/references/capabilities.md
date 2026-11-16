# Capability record

Tested on 2026-11-16 with a user-supplied personal OneDrive Word link in a T3
browser, as an unsigned guest. This is evidence for that access path, not a
promise for all Microsoft accounts or SharePoint policies. Private document
contents and the sharing grant are intentionally absent.

| Operation | Observed outcome |
| --- | --- |
| Open and read shared file | Live Word editor opened; title and current two-page document were readable. |
| Direct DOCX download | Sharing URL with `download=1` produced a valid DOCX with body/table text. While live comments existed, this route still returned the earlier comment-free bytes. Read the live pane for current review coverage. |
| Word menu download | Opened a second Download a copy confirmation; no completed download appeared in the observation window. Direct link route succeeded. |
| Native Markdown export | File → Export → Download as Markdown generated a file, then a second Download button produced a completed `.md`. Body and table text survived; the original title was plain text and calendar bullet markers were absent. |
| Live comments and replies | A labelled guest test comment anchored to the selected title word was posted and replied to. Both remained visible after reloading the sharing link. |
| PDF-with-comments export | Generated and downloaded a PDF containing the actual test comment and reply. Plain-text inspection found both markers. |
| Resolve and reopen | The test thread resolved, appeared as Resolved in the comments pane, and reopened with its reply intact. |
| Remove test thread | Deleted only the test thread. After reloading, the comments pane showed 0 items and “There are no comments in this file.” A fresh Markdown export retained every original paragraph and table-cell text. |
| Viewing mode | Mode menu switched from Editing to Viewing; editing controls became disabled. Document remained readable. |
| Create a copy online | Returned “Copy could not be created” and “There was a problem creating a copy of this file.” Cause unknown; no disposable cloud copy was created. |
| Body edits and tracked suggestions | Editing and Reviewing modes were offered. Body edits and tracked suggestions were not exercised on the sent document. |
| Document-session connector | No connected session was listed; browser and downloaded DOCX were the functional path. |

## Browser-specific findings

Word rendered inside an iframe. Top-level `body.innerText` was empty despite a
readable document, and direct `iframe.contentDocument` was unavailable. Those
results do not establish an empty file. Browser screenshots and accessibility
inspection worked; the DOCX export supplied complete structured text.

In T3, use the preview browser when that is the user's browser surface. Inspect
its current tool schemas rather than copying session IDs or element references.
A bounded snapshot can be consumed by ribbon controls before the document body.
Selecting the compact Help ribbon exposed document paragraphs and the comment
textbox in the accessibility tree. Use current textbox references for typing;
a focus-only type action was rejected as lacking an editable target.
Use the export for complete text, and the live pane for current comments. Take a fresh snapshot after navigation or UI
changes before reusing accessibility references.

## Extending the evidence

Use a permitted test copy for body edits, or an expressly authorized, labelled
comment-only test on the original. Record account or guest context, date,
saved-state/reload result, export coverage and cleanup.
Keep enabled controls separate from tested writes. A copy-creation error is a
specific limit, not evidence that all operations require sign-in.
