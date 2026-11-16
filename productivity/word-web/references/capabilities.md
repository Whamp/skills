# Capability record

Tested on 2026-11-16 with a user-supplied personal OneDrive Word link in a T3
browser, as an unsigned guest. This is evidence for that access path, not a
promise for all Microsoft accounts or SharePoint policies. Private document
contents and the sharing grant are intentionally absent.

| Operation | Observed outcome |
| --- | --- |
| Open and read shared file | Live Word editor opened; title and current two-page document were readable. |
| Direct DOCX download | Sharing URL with `download=1` produced a completed DOCX; ZIP, body/table text and file hash were verified. |
| Word menu download | Opened a second Download a copy confirmation; no completed download appeared in the observation window. Direct link route succeeded. |
| Native Markdown export | File → Export → Download as Markdown generated a file, then a second Download button produced a completed `.md`. Body and table text survived; the original title was plain text and calendar bullet markers were absent. |
| Comments pane | Opened and reported zero comments. Download contained no comment parts. No nonempty anchored thread was available for testing. |
| PDF-with-comments export | Generated and downloaded a valid two-page PDF through the export menu and second Download button. Current file had zero comments, so preservation of actual comment annotations remains untested. |
| Viewing mode | Mode menu switched from Editing to Viewing; editing controls became disabled. Document remained readable. |
| Create a copy online | Returned “Copy could not be created” and “There was a problem creating a copy of this file.” Cause unknown; no disposable cloud copy was created. |
| Editing/Reviewing controls | Both modes were offered. Saved text edits, tracked suggestions, comment posting/replies and resolve/reopen were not tested on the original document. |
| Document-session connector | No connected session was listed; browser and downloaded DOCX were the functional path. |

## Browser-specific findings

Word rendered inside an iframe. Top-level `body.innerText` was empty despite a
readable document, and direct `iframe.contentDocument` was unavailable. Those
results do not establish an empty file. Browser screenshots and accessibility
inspection worked; the DOCX export supplied complete structured text.

In T3, use the preview browser when that is the user's browser surface. Inspect
its current tool schemas rather than copying session IDs or element references.
A bounded snapshot can be consumed by ribbon controls before the document body;
use the export for complete text. Take a fresh snapshot after navigation or UI
changes before reusing accessibility references.

## Extending the evidence

Run a new comment/edit round trip only on a permitted test copy. Record account
or guest context, date, saved-state/reload result, export coverage and cleanup.
Keep enabled controls separate from tested writes. A copy-creation error is a
specific limit, not evidence that all operations require sign-in.
