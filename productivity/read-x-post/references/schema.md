# Normalized output

The command always emits one JSON object.

## Success

```json
{
  "ok": true,
  "input_url": "https://x.com/user/status/1234567890",
  "post_id": "1234567890",
  "source": {"provider": "fxtwitter-v2", "endpoint": "https://api.fxtwitter.com/2/status/1234567890"},
  "post": {
    "id": "1234567890", "url": "https://x.com/user/status/1234567890",
    "text": "Post text", "created_at": "ISO date or provider date",
    "author": {"id": "...", "name": "Name", "username": "user", "avatar_url": "...", "verified": false},
    "links": [{"url": "https://example.com", "display": "example.com"}],
    "media": [{"type": "photo|video|gif", "url": "...", "thumbnail_url": "...", "width": 1200, "height": 800, "alt_text": "..."}],
    "metrics": {"likes": 1, "reposts": 2, "quotes": 3, "replies": 4, "bookmarks": null, "views": 5},
    "quote": null
  },
  "attempts": [{"provider": "fxtwitter-v2", "ok": true}]
}
```

Fields may be `null` or empty when an upstream provider does not expose them. A quoted post recursively uses the same normalized post shape.

## Failure

```json
{
  "ok": false,
  "input_url": "...",
  "post_id": "...",
  "error": {"code": "invalid_url|not_found|rate_limited|upstream_failed", "message": "..."},
  "attempts": [{"provider": "...", "ok": false, "error": "..."}]
}
```

Provider order is FxTwitter API v2, FxTwitter legacy compatibility API, then X's public oEmbed endpoint. FxTwitter v2 is richest. The legacy endpoint protects against v2 routing changes. oEmbed is an independent reduced-data fallback.
