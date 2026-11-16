# Browser review and requested changes

## Read the live document

Inspect the current mode before acting. Viewing, Reviewing and Editing can expose
different controls. Use Viewing for reading when available. In a canvas editor,
full text may be easier to inspect in the downloaded DOCX than in DOM text.

Open Comments and inspect the requested threads. For all comments, check active
and resolved threads, expand replies, and traverse any scrolling or loading until
the full list is accounted for. Select a thread to locate its passage; compare
with the exported comment ID and anchor when available. State which filters were
checked before reporting an empty pane or complete coverage.

**Done:** each requested comment is paired with its passage, or the file's actual
empty/blocked state is recorded.

## Make requested changes

Use the operation the user asked for: a body edit, tracked suggestion, reply or
thread resolution. These are different outcomes. Select Reviewing/track changes
when suggestions are requested and verify that the resulting change is actually
tracked; opening the mode menu is insufficient evidence.

For a body edit, locate and confirm the exact passage before replacing it. For a
reply, identify the intended thread. When thread resolution is requested or authorized, resolve it after the change
or decision is incorporated. Preserve other comments, text and formatting.

Wait for Word's saved state, reload, and verify the changed text or thread. When
export works, inspect a fresh DOCX for the corresponding text, revision or comment
record. A local DOCX edit does not update the cloud document until an authorized
upload/replacement succeeds.

**Done:** the intended change persists after reload and is reflected in the
available export, or the difference between UI, cloud save and export is explicit.

## Probe capabilities

Use an identified disposable document for write tests. A useful small probe adds
a unique text marker, posts a comment on it, replies, checks the anchor after
reload, and exercises resolution/reopening only when those operations matter.
Export before and after to test what survives into DOCX. Remove only the test
material and verify cleanup. Preserve the original document and sharing policy.

If a copy cannot be created or written, retain the exact failure and keep write
operations unverified. A local synthetic OOXML example can test extraction logic;
it cannot establish that the cloud comment or save operation works.

**Done:** every tested operation has an observed outcome and cleanup result;
remaining operations are listed as untested or blocked, with the missing input.
