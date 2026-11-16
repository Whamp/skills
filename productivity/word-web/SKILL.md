---
name: word-web
description: Work with shared Microsoft Word, OneDrive or SharePoint document links to download the current file, review comments or make requested browser edits.
---

# Shared Word documents

Use the user's cloud document as the source. A downloaded DOCX is a checkpoint,
not a file that stays synchronized with Word.

## 1. Open the right version

Open the supplied link with the available document connector or supported browser.
Prefer an existing authenticated session when needed. Browser access can work
when a plain URL fetch fails. Inspect the document title, current text, guest or
account identity, and viewing/editing mode.

**Done:** the intended document is readable, or the exact access failure is known.
A link that opens one document does not establish access to the owner's drive.

## 2. Choose the operation

- **Download or compare:** read [download and inspection](references/download.md).
- **Comments or requested edits:** read [browser review](references/review.md).
- **Capability exploration:** read [the tested operations](references/capabilities.md)
  first, then test only the operations relevant to the user's workflow. Use a
  disposable copy for write tests; preserve the original.

**Done:** the requested result is verified from the current file or browser state.
A visible control alone is not proof that its action succeeds.

## 3. Return a checkpoint

Report the result, any remaining limit, and the local artifact when one was saved.
For downloads, retain the source link privately, retrieval time and file hash.
For revisions, verify the changed passage after reload and inspect a fresh export
when available. Distinguish the cloud version, local checkpoint, approval and
actual distribution. Close tabs opened solely for the task.

Keep sharing grants, browser sessions and private document contents out of the
skill and public evidence. This skill supplies a workflow, not standing permission
to edit, comment, resolve threads or change sharing settings.
