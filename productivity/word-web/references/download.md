# Download and inspect

## Obtain the file

1. Start from the supplied sharing URL. Preserve its existing parameters and
   fragment. Set the query parameter `download=1`, then navigate with the browser.
   For example, a URL already containing `?e=...` takes `&download=1`; use `?`
   when no query exists. Treat this as a tested OneDrive route, not a guarantee
   for every SharePoint tenant or access policy.
2. Check completed browser downloads. In T3, a navigation error saying the file
   cannot be displayed and was downloaded instead means to inspect
   `preview_status.downloads`. Its completed path and bytes are the evidence.
3. If direct download fails, try Word's File → Create a Copy → Download a copy.
   A second confirmation may appear. Distinguish an explicit denial, an error,
   an unfinished download and a successful file. Use the authenticated session
   or supported connector when the document requires it.

**Done:** a local DOCX opens as a ZIP, contains `word/document.xml`, and matches the
intended title/text; otherwise retain the precise access/export failure. Check
HTTP or HTML errors before interpreting a response as the document.

## Other export formats

For a text reading derivative, Word may offer File → Export → Download as
Markdown. After conversion, click Download in the “Your document is ready”
dialog and verify the completed file. This worked in the recorded test, but
heading and list representation differed from the Word layout. Use DOCX when
formatting, comments or tracked changes matter. PDF and PDF-with-comments may
also be offered; verify the actual exported content before claiming coverage.

## Inspect the checkpoint

Copy the completed browser download to a durable task path before closing its
tab: browser-managed download paths disappeared when the test tab closed.
Preserve those original bytes and SHA-256 before deriving text or editing. Use the
available Word-document tooling rather than rebuilding its package unnecessarily.
The useful parts are:

| Evidence | Where to inspect |
| --- | --- |
| Paragraphs and inline formatting | `word/document.xml` |
| Table cells and their order | `w:tbl` / `w:tr` / `w:tc` in the document body |
| Comment text and authors | `word/comments.xml`, when present |
| Anchored passage | Matching comment IDs in `w:commentRangeStart`, `w:commentRangeEnd` and `w:commentReference` |
| Insertions/deletions | `w:ins`, `w:del` and `w:delText` |
| Thread or resolution metadata | Additional comments/people parts and relationships when present |
| Headers, footers and other text | Their related package parts; body paragraphs alone are incomplete |

A live posted comment and reply survived reload in the recorded test while a
fresh direct DOCX download still had no comment parts or anchors. For review,
inspect the live pane even when the package reports zero comments; the direct
file route is not proof of complete cloud-comment coverage.

Read the comment and its anchored passage together. A paragraph-only extractor
can miss tables; a clean text export can hide tracked deletions. An absent
`comments.xml` means the downloaded package contains no classic comments, not
that the live pane or version history has been fully inspected. Use the live pane
for cloud-only context or unresolved export differences.

**Done:** the comparison covers the requested text, tables, comments and changes,
with omitted surfaces identified. Retain supplied wording and pending comments
when producing a revised DOCX; render and inspect newly authored artifacts using
the available document workflow.
