---
name: read-x-post
description: Read a public X/Twitter post from an x.com, twitter.com, FixupX, or FxTwitter status URL without login or an API key. Use when an agent needs the post author, full text, expanded links, quoted post, engagement counts, or image/video URLs, or when direct access to X is blocked. Handles provider fallback and returns normalized JSON.
---

# Read X Post

Use the bundled reader instead of scraping X HTML.

## Fetch a post

Run:

```bash
python3 scripts/read_x_post.py "https://x.com/user/status/1234567890" --pretty
```

Resolve `scripts/read_x_post.py` relative to this `SKILL.md`. The script requires only Python 3's standard library, writes normalized JSON to stdout, and writes diagnostics only to stderr.

Treat exit code `0` and `"ok": true` as success. On failure, inspect `error.code`, `error.message`, and `attempts`. Do not invent missing post content.

## Use the result

- Prefer `post.text`, `post.author`, `post.created_at`, and `post.url`.
- Use `post.links`, `post.media`, `post.quote`, and `post.metrics` when needed.
- Retain `source.provider` and `source.endpoint` as provenance.
- Expect reduced data from `twitter-oembed`: media, quotes, and metrics can be absent.

Use `--raw` only when the normalized schema omits a required provider-specific field. Use `--timeout SECONDS` to change the per-request timeout and `--user-agent TEXT` to identify the calling application.

## Boundaries

Fetch only public individual status URLs. Do not use this skill for private posts, account timelines, search, replies, or bypassing access controls. Do not claim guaranteed availability: free unauthenticated providers can change or fail.

Read [references/schema.md](references/schema.md) only when integrating the JSON into code or debugging provider differences.
