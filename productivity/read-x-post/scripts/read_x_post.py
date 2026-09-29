#!/usr/bin/env python3
"""Fetch one public X/Twitter post and emit normalized JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

STATUS_RE = re.compile(
    r"/(?:[^/]+/)?status(?:es)?/(\d{2,20})(?:[/?#]|$)", re.IGNORECASE
)
ALLOWED_HOSTS = {
    "x.com",
    "www.x.com",
    "mobile.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
    "fixupx.com",
    "www.fixupx.com",
    "fxtwitter.com",
    "www.fxtwitter.com",
    "api.fxtwitter.com",
}


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str):
        self.parts.append(data)

    def text(self):
        return " ".join(" ".join(self.parts).split())


def extract_post_id(value: str) -> str:
    value = value.strip()
    if value.isdigit() and 2 <= len(value) <= 20:
        return value
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or (parsed.hostname or "").lower() not in ALLOWED_HOSTS
    ):
        raise ValueError("Expected a public x.com or twitter.com status URL")
    match = STATUS_RE.search(parsed.path + "/")
    if not match:
        raise ValueError("URL does not contain /status/<numeric-id>")
    return match.group(1)


def get_json(url: str, timeout: float, user_agent: str) -> dict[str, Any]:
    req = Request(url, headers={"Accept": "application/json", "User-Agent": user_agent})
    with urlopen(req, timeout=timeout) as response:
        body = response.read().decode(
            response.headers.get_content_charset() or "utf-8", errors="replace"
        )
    data = json.loads(body)
    if not isinstance(data, dict):
        raise TypeError("Provider returned non-object JSON")
    return data


def first(mapping: dict[str, Any], *names: str) -> Any:
    return next((mapping[n] for n in names if mapping.get(n) is not None), None)


def normalize_author(author: Any) -> dict[str, Any] | None:
    if not isinstance(author, dict):
        return None
    verification = (
        author.get("verification")
        if isinstance(author.get("verification"), dict)
        else {}
    )
    return {
        "id": first(author, "id", "rest_id"),
        "name": first(author, "name", "display_name"),
        "username": first(author, "screen_name", "username", "handle"),
        "avatar_url": first(author, "avatar_url", "avatar", "profile_image_url"),
        "verified": bool(
            first(author, "verified", "is_verified") or verification.get("verified")
        ),
    }


def normalize_links(status: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    raw = status.get("raw_text")
    facets = raw.get("facets", []) if isinstance(raw, dict) else []
    for facet in facets if isinstance(facets, list) else []:
        if isinstance(facet, dict) and facet.get("type") == "url":
            url = first(facet, "replacement", "url", "original")
            if url:
                out.append(
                    {"url": url, "display": first(facet, "display", "display_url")}
                )
    for item in status.get("urls", []) if isinstance(status.get("urls"), list) else []:
        if isinstance(item, dict):
            url = first(item, "expanded_url", "url")
            if url and not any(x["url"] == url for x in out):
                out.append(
                    {"url": url, "display": first(item, "display_url", "display")}
                )
    return out


def normalize_media(status: dict[str, Any]) -> list[dict[str, Any]]:
    raw_media = status.get("media")
    media = raw_media if isinstance(raw_media, dict) else {}
    all_media = media.get("all")
    items = all_media if isinstance(all_media, list) else []
    if not items:
        items = []
        for kind in ("photos", "videos"):
            group = media.get(kind)
            if isinstance(group, list):
                items.extend(group)
    return [
        {
            "type": first(i, "type", "format"),
            "url": first(i, "url", "media_url", "transcode_url"),
            "thumbnail_url": first(i, "thumbnail_url", "thumb_url"),
            "width": i.get("width"),
            "height": i.get("height"),
            "alt_text": first(i, "altText", "alt_text"),
        }
        for i in items
        if isinstance(i, dict)
    ]


def normalize_status(status: Any) -> dict[str, Any] | None:
    if not isinstance(status, dict) or status.get("type") == "tombstone":
        return None
    quoted = first(status, "quote", "quoted_tweet", "quoted_status")
    return {
        "id": str(first(status, "id", "tweet_id") or ""),
        "url": first(status, "url", "tweet_url"),
        "text": first(status, "text", "full_text"),
        "created_at": first(status, "created_at", "created_timestamp"),
        "author": normalize_author(first(status, "author", "user")),
        "links": normalize_links(status),
        "media": normalize_media(status),
        "metrics": {
            "likes": first(status, "likes", "favorite_count"),
            "reposts": first(status, "reposts", "retweets", "retweet_count"),
            "quotes": first(status, "quotes", "quote_count"),
            "replies": first(status, "replies", "reply_count"),
            "bookmarks": first(status, "bookmarks", "bookmark_count"),
            "views": first(status, "views", "view_count"),
        },
        "quote": normalize_status(quoted),
    }


def normalize_oembed(data: dict[str, Any], post_id: str) -> dict[str, Any]:
    parser = TextExtractor()
    parser.feed(html.unescape(str(data.get("html", ""))))
    author_url = str(data.get("author_url", ""))
    username = urlparse(author_url).path.strip("/").split("/")[0] or None
    return {
        "id": post_id,
        "url": f"https://x.com/{username or 'i'}/status/{post_id}",
        "text": parser.text() or None,
        "created_at": None,
        "author": {
            "id": None,
            "name": data.get("author_name"),
            "username": username,
            "avatar_url": None,
            "verified": False,
        },
        "links": [],
        "media": [],
        "metrics": {
            k: None
            for k in ("likes", "reposts", "quotes", "replies", "bookmarks", "views")
        },
        "quote": None,
    }


def classify_error(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, HTTPError):
        return (
            {404: "not_found", 429: "rate_limited"}.get(exc.code, "upstream_failed"),
            f"HTTP {exc.code}",
        )
    return ("upstream_failed", str(exc))


def fetch(
    input_url: str, timeout: float, user_agent: str, include_raw: bool
) -> tuple[dict[str, Any], int]:
    try:
        post_id = extract_post_id(input_url)
    except ValueError as exc:
        return {
            "ok": False,
            "input_url": input_url,
            "post_id": None,
            "error": {"code": "invalid_url", "message": str(exc)},
            "attempts": [],
        }, 2
    canonical = f"https://x.com/i/status/{post_id}"
    providers = [
        ("fxtwitter-v2", f"https://api.fxtwitter.com/2/status/{post_id}"),
        ("fxtwitter-legacy", f"https://api.fxtwitter.com/i/status/{post_id}"),
        (
            "twitter-oembed",
            "https://publish.twitter.com/oembed?omit_script=true&dnt=true&url="
            + quote(canonical, safe=""),
        ),
    ]
    attempts, last_code, last_message = [], "upstream_failed", "All providers failed"
    for provider, endpoint in providers:
        try:
            raw = get_json(endpoint, timeout, user_agent)
            if provider.startswith("fxtwitter"):
                code = raw.get("code", 200)
                if isinstance(code, int) and code >= 400:
                    raise RuntimeError(f"Provider code {code}")
                post = normalize_status(first(raw, "status", "tweet"))
            else:
                post = normalize_oembed(raw, post_id)
            if not post or not post.get("text"):
                raise ValueError("Provider returned no readable post text")
            attempts.append({"provider": provider, "ok": True})
            result = {
                "ok": True,
                "input_url": input_url,
                "post_id": post_id,
                "source": {"provider": provider, "endpoint": endpoint},
                "post": post,
                "attempts": attempts,
            }
            if include_raw:
                result["raw"] = raw
            return result, 0
        except (
            HTTPError,
            URLError,
            TimeoutError,
            ValueError,
            TypeError,
            RuntimeError,
        ) as exc:
            last_code, last_message = classify_error(exc)
            attempts.append({"provider": provider, "ok": False, "error": last_message})
    return {
        "ok": False,
        "input_url": input_url,
        "post_id": post_id,
        "error": {"code": last_code, "message": last_message},
        "attempts": attempts,
    }, 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="Read one public X/Twitter post as normalized JSON"
    )
    p.add_argument("url")
    p.add_argument("--timeout", type=float, default=12.0)
    p.add_argument(
        "--user-agent", default="read-x-post-agent-skill/1.0 (+https://agentskills.io)"
    )
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--raw", action="store_true")
    args = p.parse_args()
    result, code = fetch(args.url, args.timeout, args.user_agent, args.raw)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
