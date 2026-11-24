#!/usr/bin/env python3
"""Deterministic headless Chromium frame-capture renderer for paper-to-video."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import functools
import http.server
import importlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SYSTEM_BROWSER_CANDIDATES = (
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)

STAGE_HELPERS_DIR = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_WORKERS = 4
DEFAULT_SAFE_MARGIN_X = 72
DEFAULT_SAFE_MARGIN_Y = 56
MARGIN_TOLERANCE_PX = 2.0
OVERLAP_MIN_PX = 4.0

_COLLECT_FRAME_GEOMETRY_JS = """() => {
    const root = document.getElementById("stage") || document.body;
    const vw = window.innerWidth || 1920;
    const vh = window.innerHeight || 1080;

    function effectiveOpacity(el) {
        let opacity = 1;
        let cur = el;
        while (cur && cur.nodeType === 1) {
            const style = getComputedStyle(cur);
            if (style.display === "none" || style.visibility === "hidden") {
                return 0;
            }
            const op = parseFloat(style.opacity || "1");
            if (!Number.isNaN(op)) {
                opacity *= op;
            }
            if (opacity <= 0.05) {
                return 0;
            }
            if (cur === root) {
                break;
            }
            cur = cur.parentElement;
        }
        return opacity;
    }

    function toBox(rect) {
        return {
            left: Math.round(rect.left * 10) / 10,
            top: Math.round(rect.top * 10) / 10,
            right: Math.round(rect.right * 10) / 10,
            bottom: Math.round(rect.bottom * 10) / 10,
            width: Math.round(rect.width * 10) / 10,
            height: Math.round(rect.height * 10) / 10,
        };
    }

    const allMathNodes = Array.from(root.querySelectorAll(".math-node"));
    const visibleMathNodes = [];
    for (const node of allMathNodes) {
        if (node.closest("[data-audit-ignore='true']")) {
            continue;
        }
        if (effectiveOpacity(node) <= 0.05) {
            continue;
        }
        const rect = node.getBoundingClientRect();
        if (rect.width <= 0.5 || rect.height <= 0.5) {
            continue;
        }
        visibleMathNodes.push({
            text: (node.textContent || "").trim().slice(0, 80),
            has_rendered_katex: Boolean(node.querySelector(".katex")),
            has_katex_error: Boolean(node.querySelector(".katex-error")),
            rect: toBox(rect),
        });
    }

    const texts = [];
    for (const el of root.querySelectorAll("svg text")) {
        if (el.closest("[data-audit-ignore='true']")) {
            continue;
        }
        const label = (el.textContent || "").trim();
        if (!label || effectiveOpacity(el) <= 0.05) {
            continue;
        }
        const rect = el.getBoundingClientRect();
        if (rect.width <= 0.5 || rect.height <= 0.5) {
            continue;
        }
        texts.push({
            text: label.slice(0, 80),
            rect: toBox(rect),
        });
    }

    const shapes = [];
    for (const el of root.querySelectorAll("svg rect, svg polygon")) {
        if (
            el.closest("[data-audit-ignore='true']") ||
            el.closest("defs, clipPath, mask, pattern, marker")
        ) {
            continue;
        }
        if (effectiveOpacity(el) <= 0.05) {
            continue;
        }
        const style = getComputedStyle(el);
        const fill = style.fill || "none";
        const stroke = style.stroke || "none";
        const fillOp = parseFloat(style.fillOpacity || "1");
        const strokeOp = parseFloat(style.strokeOpacity || "1");
        const strokeW = parseFloat(style.strokeWidth || "0");
        const visibleFill = fill !== "none" && fill !== "rgba(0, 0, 0, 0)" && fillOp > 0.01;
        const visibleStroke = stroke !== "none" && stroke !== "rgba(0, 0, 0, 0)" && strokeOp > 0.01 && strokeW > 0;
        if (!visibleFill && !visibleStroke) {
            continue;
        }
        const rect = el.getBoundingClientRect();
        if (rect.width <= 0.5 || rect.height <= 0.5) {
            continue;
        }
        if (rect.width >= vw * 0.85 && rect.height >= vh * 0.85) {
            continue;
        }
        shapes.push({
            tag: el.tagName.toLowerCase(),
            rect: toBox(rect),
        });
    }

    return {
        has_katex: typeof window.katex !== "undefined" && window.katex !== null,
        all_math_node_count: allMathNodes.length,
        math_nodes: visibleMathNodes,
        texts,
        shapes,
    };
}"""


@dataclass(frozen=True)
class KeyframeTarget:
    """One beat keyframe capture timestamp and filename."""

    index: int
    beat_id: str
    timestamp_s: float
    filename: str


@dataclass(frozen=True)
class RectBox:
    """Axis-aligned viewport bounding box in CSS pixels."""

    left: float
    top: float
    right: float
    bottom: float
    width: float
    height: float

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> RectBox:
        """Build a RectBox from serialized DOMRect coordinates."""

        left = float(raw["left"])
        top = float(raw["top"])
        right = float(raw["right"])
        bottom = float(raw["bottom"])
        width = float(raw.get("width", max(0.0, right - left)))
        height = float(raw.get("height", max(0.0, bottom - top)))
        return cls(
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            width=width,
            height=height,
        )


@dataclass(frozen=True)
class _RenderSceneSpec:
    """Immutable scene rendering parameters shared across capture workers."""

    url: str
    timeline: dict[str, Any]
    duration_s: float
    fps: int
    width: int
    height: int
    browser_path: Path | None


@dataclass(frozen=True)
class _SafeFrameBounds:
    """Viewport size and outer safe margins for layout auditing."""

    width: int
    height: int
    margin_x: int = DEFAULT_SAFE_MARGIN_X
    margin_y: int = DEFAULT_SAFE_MARGIN_Y


@dataclass(frozen=True)
class LayoutAuditIssue:
    """One deterministic KaTeX or SVG/DOM geometry audit defect."""

    beat_id: str
    timestamp_s: float
    kind: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize issue to a JSON-compatible dictionary."""

        return {
            "beat_id": self.beat_id,
            "timestamp_s": self.timestamp_s,
            "kind": self.kind,
            "message": self.message,
        }


class _SceneRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Quiet static server that falls back to bundled stage_helpers.js when absent."""

    fallback_assets_dir: Path | None = None

    def log_message(self, format: str, *args: Any) -> None:
        return

    def translate_path(self, path: str) -> str:
        resolved = Path(super().translate_path(path))
        if (
            not resolved.exists()
            and self.fallback_assets_dir is not None
            and resolved.name == "stage_helpers.js"
        ):
            candidate = self.fallback_assets_dir / "stage_helpers.js"
            if candidate.is_file():
                return str(candidate)
        return str(resolved)


def compute_keyframe_targets(timeline: dict[str, Any]) -> list[KeyframeTarget]:
    """Choose the settled visual inspection timestamp for every beat."""

    beats = timeline.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("timeline.json contains no beats")

    targets: list[KeyframeTarget] = []
    for pos, beat in enumerate(beats, start=1):
        beat_id = str(beat["id"])
        index = int(beat.get("index", pos))
        start_s = float(beat["start_s"])
        audio_end_s = float(beat.get("audio_end_s", beat["end_s"]))
        audio_dur = max(0.0, audio_end_s - start_s)
        if audio_dur > 0.35:
            offset = min(audio_dur * 0.85, audio_dur - 0.12)
        else:
            offset = audio_dur * 0.5
        timestamp_s = round(start_s + max(0.0, offset), 3)
        targets.append(
            KeyframeTarget(
                index=index,
                beat_id=beat_id,
                timestamp_s=timestamp_s,
                filename=f"{index:02d}_{beat_id}.png",
            )
        )
    return targets


def compute_frame_ranges(total_frames: int, workers: int) -> list[tuple[int, int]]:
    """Partition [0, total_frames) into contiguous non-empty worker slices."""

    if total_frames < 1:
        raise ValueError("total_frames must be >= 1")
    if workers < 1:
        raise ValueError("workers must be >= 1")

    bucket_count = min(total_frames, workers)
    base, extra = divmod(total_frames, bucket_count)
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for idx in range(bucket_count):
        size = base + (1 if idx < extra else 0)
        ranges.append((cursor, cursor + size))
        cursor += size
    return ranges


def _box_overlap(a: RectBox, b: RectBox) -> tuple[float, float]:
    ov_w = min(a.right, b.right) - max(a.left, b.left)
    ov_h = min(a.bottom, b.bottom) - max(a.top, b.top)
    return max(0.0, ov_w), max(0.0, ov_h)


def _audit_katex_nodes(
    geometry: dict[str, Any], beat_id: str, timestamp_s: float
) -> list[LayoutAuditIssue]:
    issues: list[LayoutAuditIssue] = []
    all_count = int(geometry.get("all_math_node_count", 0))
    has_katex = bool(geometry.get("has_katex", False))
    if all_count > 0 and not has_katex:
        issues.append(
            LayoutAuditIssue(
                beat_id=beat_id,
                timestamp_s=timestamp_s,
                kind="katex_missing",
                message="page declares .math-node elements but window.katex is missing",
            )
        )

    for node in geometry.get("math_nodes", []):
        label = str(node.get("text", ""))
        if node.get("has_katex_error"):
            issues.append(
                LayoutAuditIssue(
                    beat_id=beat_id,
                    timestamp_s=timestamp_s,
                    kind="katex_parse_error",
                    message=f"KaTeX render error in .math-node {label!r}",
                )
            )
        elif label and not node.get("has_rendered_katex"):
            issues.append(
                LayoutAuditIssue(
                    beat_id=beat_id,
                    timestamp_s=timestamp_s,
                    kind="katex_unrendered",
                    message=f"visible .math-node {label!r} lacks a rendered .katex child",
                )
            )
    return issues


def _audit_safe_margins(
    label_items: list[tuple[str, RectBox]],
    *,
    beat_id: str,
    timestamp_s: float,
    bounds: _SafeFrameBounds,
) -> list[LayoutAuditIssue]:
    issues: list[LayoutAuditIssue] = []
    min_x = bounds.margin_x - MARGIN_TOLERANCE_PX
    max_x = bounds.width - bounds.margin_x + MARGIN_TOLERANCE_PX
    min_y = bounds.margin_y - MARGIN_TOLERANCE_PX
    max_y = bounds.height - bounds.margin_y + MARGIN_TOLERANCE_PX

    for text, box in label_items:
        if (
            box.left < min_x
            or box.right > max_x
            or box.top < min_y
            or box.bottom > max_y
        ):
            issues.append(
                LayoutAuditIssue(
                    beat_id=beat_id,
                    timestamp_s=timestamp_s,
                    kind="safe_margin",
                    message=(
                        f"{text!r} ({box.left:.0f},{box.top:.0f})-({box.right:.0f},{box.bottom:.0f}) "
                        f"exceeds safe margin [{bounds.margin_x},{bounds.width - bounds.margin_x}]x"
                        f"[{bounds.margin_y},{bounds.height - bounds.margin_y}]"
                    ),
                )
            )
    return issues


def _audit_text_overlaps(
    label_items: list[tuple[str, RectBox]], beat_id: str, timestamp_s: float
) -> list[LayoutAuditIssue]:
    issues: list[LayoutAuditIssue] = []
    for idx, (text_a, box_a) in enumerate(label_items):
        for text_b, box_b in label_items[idx + 1 :]:
            ov_w, ov_h = _box_overlap(box_a, box_b)
            min_w = min(box_a.width, box_b.width)
            min_h = min(box_a.height, box_b.height)
            if (
                ov_w >= OVERLAP_MIN_PX
                and ov_h >= OVERLAP_MIN_PX
                and ov_h >= min_h * 0.22
                and ov_w >= min_w * 0.10
            ):
                issues.append(
                    LayoutAuditIssue(
                        beat_id=beat_id,
                        timestamp_s=timestamp_s,
                        kind="text_overlap",
                        message=f"{text_a!r} overlaps {text_b!r} by {ov_w:.0f}x{ov_h:.0f}px",
                    )
                )
    return issues


def _audit_shape_collisions(
    label_items: list[tuple[str, RectBox]],
    shape_items: list[tuple[str, RectBox]],
    beat_id: str,
    timestamp_s: float,
) -> list[LayoutAuditIssue]:
    issues: list[LayoutAuditIssue] = []
    for text, label_box in label_items:
        for tag, shape_box in shape_items:
            ov_w, ov_h = _box_overlap(label_box, shape_box)
            if ov_w < OVERLAP_MIN_PX or ov_h < OVERLAP_MIN_PX:
                continue
            contained = (
                label_box.left >= shape_box.left - 1.0
                and label_box.right <= shape_box.right + 1.0
                and label_box.top >= shape_box.top - 2.0
                and label_box.bottom <= shape_box.bottom + 2.0
            )
            if not contained:
                issues.append(
                    LayoutAuditIssue(
                        beat_id=beat_id,
                        timestamp_s=timestamp_s,
                        kind="shape_collision",
                        message=(
                            f"{text!r} collides with <{tag}> border "
                            f"({shape_box.left:.0f},{shape_box.top:.0f})-"
                            f"({shape_box.right:.0f},{shape_box.bottom:.0f})"
                        ),
                    )
                )
    return issues


def audit_frame_geometry(
    geometry: dict[str, Any],
    *,
    beat_id: str,
    timestamp_s: float,
    width: int,
    height: int,
    safe_margin_x: int = DEFAULT_SAFE_MARGIN_X,
    safe_margin_y: int = DEFAULT_SAFE_MARGIN_Y,
) -> list[LayoutAuditIssue]:
    """Audit extracted DOM/SVG frame geometry for KaTeX, margin, and collision defects."""

    label_items: list[tuple[str, RectBox]] = [
        (str(item.get("text", "")), RectBox.from_mapping(item["rect"]))
        for item in geometry.get("texts", [])
    ]
    label_items.extend(
        (str(item.get("text", "")), RectBox.from_mapping(item["rect"]))
        for item in geometry.get("math_nodes", [])
    )
    shape_items: list[tuple[str, RectBox]] = [
        (str(item.get("tag", "rect")), RectBox.from_mapping(item["rect"]))
        for item in geometry.get("shapes", [])
    ]

    bounds = _SafeFrameBounds(
        width=width,
        height=height,
        margin_x=safe_margin_x,
        margin_y=safe_margin_y,
    )
    issues: list[LayoutAuditIssue] = []
    issues.extend(_audit_katex_nodes(geometry, beat_id, timestamp_s))
    issues.extend(
        _audit_safe_margins(
            label_items,
            beat_id=beat_id,
            timestamp_s=timestamp_s,
            bounds=bounds,
        )
    )
    issues.extend(_audit_text_overlaps(label_items, beat_id, timestamp_s))
    issues.extend(
        _audit_shape_collisions(label_items, shape_items, beat_id, timestamp_s)
    )
    return issues


def discover_system_browser(explicit_path: Path | None = None) -> str | None:
    """Return an explicit or auto-discovered Chromium/Chrome executable path."""

    if explicit_path is not None:
        if not explicit_path.exists():
            raise FileNotFoundError(f"browser executable not found: {explicit_path}")
        return str(explicit_path)

    for name in (
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
    ):
        found = shutil.which(name)
        if found:
            return found

    for candidate in SYSTEM_BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def _start_static_server(
    directory: Path,
    *,
    fallback_assets_dir: Path | None = STAGE_HELPERS_DIR,
) -> tuple[http.server.ThreadingHTTPServer, int]:
    class _BoundHandler(_SceneRequestHandler):
        pass

    _BoundHandler.fallback_assets_dir = fallback_assets_dir
    handler = functools.partial(_BoundHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def _import_playwright() -> Any:
    try:
        return importlib.import_module("playwright.sync_api")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "playwright is not installed in this Python environment; run with `uv run --with playwright python3 ...`"
        ) from exc


def _launch_browser(playwright_instance: Any, explicit_browser: Path | None) -> Any:
    launch_args = [
        "--disable-gpu-sandbox",
        "--headless=new",
        "--font-render-hinting=none",
    ]
    if explicit_browser is not None:
        return playwright_instance.chromium.launch(
            executable_path=str(explicit_browser),
            headless=True,
            args=launch_args,
        )

    try:
        return playwright_instance.chromium.launch(headless=True, args=launch_args)
    except Exception:
        system_browser = discover_system_browser()
        if not system_browser:
            raise
        return playwright_instance.chromium.launch(
            executable_path=system_browser,
            headless=True,
            args=launch_args,
        )


def _open_scene(
    browser: Any,
    url: str,
    timeline: dict[str, Any],
    width: int,
    height: int,
) -> tuple[Any, Any, Any, list[str]]:
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
    )
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda err: errors.append(f"pageerror: {err}"))
    page.on(
        "console",
        lambda msg: (
            errors.append(f"console.error: {msg.text}") if msg.type == "error" else None
        ),
    )
    page.add_init_script(f"window.__TIMELINE__ = {json.dumps(timeline)};")
    page.goto(url, wait_until="load", timeout=60_000)
    page.evaluate(
        """async () => {
            if (document.fonts && document.fonts.ready) {
                await document.fonts.ready;
            }
            if (window.__SCENE_READY__) {
                await window.__SCENE_READY__;
            }
            if (typeof window.renderAt !== "function") {
                throw new Error("scene.html must define window.renderAt(t)");
            }
        }"""
    )
    if errors:
        raise RuntimeError("scene.html reported runtime errors:\n" + "\n".join(errors))
    cdp = context.new_cdp_session(page)
    return context, page, cdp, errors


def _capture_frame_png(page: Any, cdp: Any, timestamp_s: float) -> bytes:
    page.evaluate(
        """async (t) => {
            window.renderAt(t);
            await new Promise((resolve) => requestAnimationFrame(resolve));
        }""",
        timestamp_s,
    )
    payload = cdp.send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    return base64.b64decode(payload["data"])


def _collect_frame_geometry(page: Any) -> dict[str, Any]:
    result = page.evaluate(_COLLECT_FRAME_GEOMETRY_JS)
    if not isinstance(result, dict):
        raise TypeError("layout audit geometry probe returned unexpected payload")
    return result


def _build_contact_sheet(
    image_paths: list[Path],
    output_path: Path,
    *,
    columns: int = 3,
    tile_width: int = 640,
    tile_height: int = 360,
) -> Path | None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not image_paths:
        return None
    columns = max(1, min(columns, len(image_paths)))
    rows = math.ceil(len(image_paths) / columns)
    cmd = [ffmpeg, "-y", "-v", "error"]
    for img in image_paths:
        cmd.extend(["-i", str(img)])

    scaled_parts: list[str] = []
    labels: list[str] = []
    for idx, _ in enumerate(image_paths):
        scaled_parts.append(
            f"[{idx}:v]scale={tile_width}:{tile_height}:force_original_aspect_ratio=decrease,"
            f"pad={tile_width}:{tile_height}:(ow-iw)/2:(oh-ih)/2:color=black[s{idx}]"
        )
        labels.append(f"[s{idx}]")

    filter_complex = (
        ";".join(scaled_parts)
        + f";{''.join(labels)}concat=n={len(image_paths)}:v=1:a=0,"
        + f"tile={columns}x{rows}:padding=8:margin=8:color=0x22262e[grid]"
    )
    cmd.extend(
        [
            "-filter_complex",
            filter_complex,
            "-map",
            "[grid]",
            "-frames:v",
            "1",
            str(output_path),
        ]
    )
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not output_path.exists():
        print(
            f"Warning: contact sheet generation failed: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return None
    return output_path


def _probe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {}
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,duration",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    fmt = data.get("format", {})
    duration_s = round(float(fmt.get("duration", 0.0)), 3)
    audio_duration_s = (
        round(float(audio_stream["duration"]), 3)
        if audio_stream.get("duration")
        else None
    )
    probe: dict[str, Any] = {
        "duration_s": duration_s,
        "size_bytes": int(fmt.get("size", 0)),
        "video_codec": video_stream.get("codec_name"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "audio_codec": audio_stream.get("codec_name"),
        "audio_duration_s": audio_duration_s,
    }
    if audio_duration_s is not None:
        probe["audio_duration_delta_s"] = round(abs(duration_s - audio_duration_s), 3)
    return probe


def _escape_subtitles_filter_path(path: Path) -> str:
    text = str(path.resolve())
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _build_subtitle_filter(burn_subtitles: Path) -> str:
    escaped = _escape_subtitles_filter_path(burn_subtitles)
    style = (
        "FontName=Inter,FontSize=20,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H80000000,BorderStyle=3,Outline=1,MarginV=36"
    )
    return f"subtitles='{escaped}':force_style='{style}'"


def _capture_keyframe_batch(
    browser: Any,
    url: str,
    timeline: dict[str, Any],
    targets: list[KeyframeTarget],
    keyframes_dir: Path,
    *,
    bounds: _SafeFrameBounds,
    skip_audit: bool,
) -> tuple[list[Path], list[LayoutAuditIssue]]:
    captured: list[Path] = []
    audit_issues: list[LayoutAuditIssue] = []
    context, page, cdp, errors = _open_scene(
        browser, url, timeline, bounds.width, bounds.height
    )
    try:
        for target in targets:
            png_bytes = _capture_frame_png(page, cdp, target.timestamp_s)
            out_file = keyframes_dir / target.filename
            out_file.write_bytes(png_bytes)
            captured.append(out_file)
            if not skip_audit:
                geometry = _collect_frame_geometry(page)
                audit_issues.extend(
                    audit_frame_geometry(
                        geometry,
                        beat_id=target.beat_id,
                        timestamp_s=target.timestamp_s,
                        width=bounds.width,
                        height=bounds.height,
                        safe_margin_x=bounds.margin_x,
                        safe_margin_y=bounds.margin_y,
                    )
                )
        if errors:
            raise RuntimeError(
                "scene.html reported runtime errors:\n" + "\n".join(errors)
            )
    finally:
        context.close()
    return captured, audit_issues


def render_keyframes(
    scene_path: Path,
    timeline: dict[str, Any],
    keyframes_dir: Path,
    *,
    width: int,
    height: int,
    browser_path: Path | None,
    skip_audit: bool = False,
    safe_margin_x: int = DEFAULT_SAFE_MARGIN_X,
    safe_margin_y: int = DEFAULT_SAFE_MARGIN_Y,
) -> dict[str, Any]:
    """Capture one settled PNG per beat, run KaTeX/layout audit, and build a contact sheet."""

    targets = compute_keyframe_targets(timeline)
    keyframes_dir.mkdir(parents=True, exist_ok=True)
    playwright_api = _import_playwright()
    server, port = _start_static_server(scene_path.parent)
    bounds = _SafeFrameBounds(
        width=width, height=height, margin_x=safe_margin_x, margin_y=safe_margin_y
    )
    started = time.monotonic()

    try:
        with playwright_api.sync_playwright() as p:
            browser = _launch_browser(p, browser_path)
            try:
                url = f"http://127.0.0.1:{port}/{scene_path.name}"
                captured, audit_issues = _capture_keyframe_batch(
                    browser,
                    url,
                    timeline,
                    targets,
                    keyframes_dir,
                    bounds=bounds,
                    skip_audit=skip_audit,
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    contact_sheet = _build_contact_sheet(captured, keyframes_dir / "contact_sheet.png")
    passed = skip_audit or len(audit_issues) == 0
    return {
        "ok": passed,
        "mode": "keyframes",
        "count": len(captured),
        "keyframes_dir": str(keyframes_dir.resolve()),
        "contact_sheet": str(contact_sheet.resolve()) if contact_sheet else None,
        "audit": {
            "enabled": not skip_audit,
            "passed": passed,
            "issue_count": len(audit_issues),
            "issues": [issue.to_dict() for issue in audit_issues],
        },
        "files": [
            {
                "id": target.beat_id,
                "timestamp_s": target.timestamp_s,
                "path": str(path.resolve()),
            }
            for target, path in zip(targets, captured, strict=True)
        ],
        "render_seconds": round(time.monotonic() - started, 2),
    }


class _RenderProgress:
    """Thread-safe frame completion tracker across parallel capture workers."""

    def __init__(self, total_frames: int, fps: int, started: float) -> None:
        self._total = total_frames
        self._step = max(1, fps * 5)
        self._started = started
        self._done = 0
        self._lock = threading.Lock()

    def advance(self) -> None:
        with self._lock:
            self._done += 1
            if self._done % self._step == 0 or self._done == self._total:
                elapsed = max(0.001, time.monotonic() - self._started)
                pct = (self._done / self._total) * 100.0
                print(
                    f"rendered {self._done}/{self._total} frames "
                    f"({pct:.1f}%, {self._done / elapsed:.1f} fps)",
                    file=sys.stderr,
                )


def _pipe_frames_to_stdin(
    browser: Any,
    spec: _RenderSceneSpec,
    frame_range: tuple[int, int],
    stdin_pipe: Any,
    progress: _RenderProgress,
    cancel_event: threading.Event,
) -> None:
    context, page, cdp, errors = _open_scene(
        browser, spec.url, spec.timeline, spec.width, spec.height
    )
    start_frame, end_frame = frame_range
    try:
        for frame in range(start_frame, end_frame):
            if cancel_event.is_set():
                break
            t = min(spec.duration_s, frame / spec.fps)
            stdin_pipe.write(_capture_frame_png(page, cdp, t))
            progress.advance()
        if errors:
            raise RuntimeError(
                "scene.html reported runtime errors:\n" + "\n".join(errors)
            )
    finally:
        context.close()


def _render_frame_slice(
    playwright_api: Any,
    spec: _RenderSceneSpec,
    frame_range: tuple[int, int],
    ffmpeg_cmd: list[str],
    output_path: Path,
    progress: _RenderProgress,
    cancel_event: threading.Event,
) -> Path:
    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None
    try:
        with playwright_api.sync_playwright() as p:
            browser = _launch_browser(p, spec.browser_path)
            try:
                _pipe_frames_to_stdin(
                    browser, spec, frame_range, proc.stdin, progress, cancel_event
                )
            finally:
                browser.close()
    except Exception:
        cancel_event.set()
        proc.stdin.close()
        proc.kill()
        proc.wait()
        raise

    proc.stdin.close()
    _, stderr_bytes = proc.communicate()
    if cancel_event.is_set():
        return output_path
    if proc.returncode != 0 or not output_path.exists():
        cancel_event.set()
        raise RuntimeError(
            f"ffmpeg encoding failed (exit {proc.returncode}): "
            f"{stderr_bytes.decode('utf-8', errors='replace').strip()}"
        )
    return output_path


def _build_direct_ffmpeg_cmd(
    ffmpeg: str,
    fps: int,
    crf: int,
    output_path: Path,
    *,
    audio_path: Path | None,
    burn_subtitles: Path | None,
) -> list[str]:
    cmd: list[str] = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-framerate",
        str(fps),
        "-i",
        "-",
    ]
    if audio_path is not None:
        cmd.extend(["-i", str(audio_path)])
    if burn_subtitles is not None:
        cmd.extend(["-vf", _build_subtitle_filter(burn_subtitles)])
    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            str(crf),
            "-preset",
            "medium",
        ]
    )
    if audio_path is not None:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    cmd.extend(["-movflags", "+faststart", str(output_path)])
    return cmd


def _build_segment_ffmpeg_cmd(
    ffmpeg: str, fps: int, crf: int, preset: str, seg_path: Path
) -> list[str]:
    return [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-framerate",
        str(fps),
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        str(crf),
        "-preset",
        preset,
        "-video_track_timescale",
        "90000",
        str(seg_path),
    ]


def _render_parallel_segments(
    playwright_api: Any,
    ffmpeg: str,
    spec: _RenderSceneSpec,
    ranges: list[tuple[int, int]],
    output_path: Path,
    *,
    audio_path: Path | None,
    burn_subtitles: Path | None,
    crf: int,
    progress: _RenderProgress,
    cancel_event: threading.Event,
) -> None:
    seg_crf = 12 if burn_subtitles is not None else crf
    seg_preset = "ultrafast" if burn_subtitles is not None else "medium"
    with tempfile.TemporaryDirectory(prefix="paper_to_video_segs_") as tmp:
        temp_dir = Path(tmp)
        segment_paths: list[Path] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(ranges)) as pool:
            futures: list[concurrent.futures.Future[Path]] = []
            for idx, frame_range in enumerate(ranges):
                seg_path = temp_dir / f"seg_{idx:03d}.mp4"
                segment_paths.append(seg_path)
                seg_cmd = _build_segment_ffmpeg_cmd(
                    ffmpeg, spec.fps, seg_crf, seg_preset, seg_path
                )
                futures.append(
                    pool.submit(
                        _render_frame_slice,
                        playwright_api,
                        spec,
                        frame_range,
                        seg_cmd,
                        seg_path,
                        progress,
                        cancel_event,
                    )
                )
            for future in futures:
                future.result()

        _concat_video_segments(
            ffmpeg,
            segment_paths,
            output_path,
            audio_path=audio_path,
            burn_subtitles=burn_subtitles,
            crf=crf,
            temp_dir=temp_dir,
        )


def _concat_video_segments(
    ffmpeg: str,
    segments: list[Path],
    output_path: Path,
    *,
    audio_path: Path | None,
    burn_subtitles: Path | None,
    crf: int,
    temp_dir: Path,
) -> None:
    concat_file = temp_dir / "concat.txt"
    lines = [
        f"file '{str(seg.resolve()).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'"
        for seg in segments
    ]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd: list[str] = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
    ]
    if audio_path is not None:
        cmd.extend(["-i", str(audio_path)])

    if burn_subtitles is not None:
        cmd.extend(
            [
                "-vf",
                _build_subtitle_filter(burn_subtitles),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                str(crf),
                "-preset",
                "medium",
            ]
        )
    else:
        cmd.extend(["-c:v", "copy"])

    if audio_path is not None:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    cmd.extend(["-movflags", "+faststart", str(output_path)])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(
            f"ffmpeg segment concat failed (exit {result.returncode}): {result.stderr.strip()}"
        )


def render_mp4(
    scene_path: Path,
    timeline: dict[str, Any],
    output_path: Path,
    *,
    audio_path: Path | None,
    burn_subtitles: Path | None,
    fps: int,
    width: int,
    height: int,
    crf: int,
    browser_path: Path | None,
    workers: int = DEFAULT_WORKERS,
) -> dict[str, Any]:
    """Capture all frames deterministically across parallel workers and encode H.264 MP4."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to render MP4 video")

    duration_s = float(timeline.get("total_duration_s", 0.0))
    if duration_s <= 0:
        raise ValueError("timeline.json total_duration_s must be > 0")
    total_frames = max(1, math.ceil(duration_s * fps))
    ranges = compute_frame_ranges(total_frames, workers)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    playwright_api = _import_playwright()
    server, port = _start_static_server(scene_path.parent)
    url = f"http://127.0.0.1:{port}/{scene_path.name}"
    started = time.monotonic()
    progress = _RenderProgress(total_frames, fps, started)
    cancel_event = threading.Event()

    spec = _RenderSceneSpec(
        url=url,
        timeline=timeline,
        duration_s=duration_s,
        fps=fps,
        width=width,
        height=height,
        browser_path=browser_path,
    )
    try:
        if len(ranges) == 1:
            ffmpeg_cmd = _build_direct_ffmpeg_cmd(
                ffmpeg,
                fps,
                crf,
                output_path,
                audio_path=audio_path,
                burn_subtitles=burn_subtitles,
            )
            _render_frame_slice(
                playwright_api,
                spec,
                ranges[0],
                ffmpeg_cmd,
                output_path,
                progress,
                cancel_event,
            )
        else:
            _render_parallel_segments(
                playwright_api,
                ffmpeg,
                spec,
                ranges,
                output_path,
                audio_path=audio_path,
                burn_subtitles=burn_subtitles,
                crf=crf,
                progress=progress,
                cancel_event=cancel_event,
            )
    finally:
        server.shutdown()
        server.server_close()

    probe = _probe_video(output_path)
    return {
        "ok": True,
        "mode": "video",
        "output": str(output_path.resolve()),
        "frames": total_frames,
        "fps": fps,
        "workers": len(ranges),
        "render_seconds": round(time.monotonic() - started, 2),
        **probe,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render a deterministic scene.html animation to beat keyframes or MP4."
    )
    parser.add_argument("scene_html", type=Path, help="Path to scene.html")
    parser.add_argument(
        "--timeline", type=Path, required=True, help="Path to timeline.json"
    )
    parser.add_argument(
        "--out", type=Path, help="Output MP4 path (required unless --keyframes)"
    )
    parser.add_argument("--audio", type=Path, help="Master audio track (narration.m4a)")
    parser.add_argument(
        "--burn-subtitles", type=Path, help="Optional .srt/.vtt file to burn in"
    )
    parser.add_argument(
        "--fps", type=int, help="Frame rate (defaults to timeline.json fps or 30)"
    )
    parser.add_argument(
        "--width", type=int, default=1920, help="Viewport width (default 1920)"
    )
    parser.add_argument(
        "--height", type=int, default=1080, help="Viewport height (default 1080)"
    )
    parser.add_argument(
        "--crf", type=int, default=18, help="H.264 CRF quality (default 18)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Parallel Chromium workers for MP4 rendering (default {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--browser-path", type=Path, help="Explicit Chromium/Chrome executable path"
    )
    parser.add_argument(
        "--keyframes",
        action="store_true",
        help="Capture one settled PNG per beat plus contact_sheet.png instead of rendering MP4",
    )
    parser.add_argument(
        "--keyframes-dir",
        type=Path,
        help="Output directory for --keyframes (defaults to <scene_dir>/keyframes)",
    )
    parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Skip KaTeX and SVG/DOM layout audit failure checks during --keyframes",
    )
    args = parser.parse_args(argv)

    if not args.scene_html.is_file():
        print(f"Error: scene file not found: {args.scene_html}", file=sys.stderr)
        return 1
    if not args.timeline.is_file():
        print(f"Error: timeline file not found: {args.timeline}", file=sys.stderr)
        return 1
    if not args.keyframes and args.out is None:
        print(
            "Error: --out is required unless --keyframes is specified", file=sys.stderr
        )
        return 2
    if args.workers < 1:
        print("Error: --workers must be >= 1", file=sys.stderr)
        return 2
    if args.audio is not None and not args.audio.is_file():
        print(f"Error: audio file not found: {args.audio}", file=sys.stderr)
        return 1
    if args.burn_subtitles is not None and not args.burn_subtitles.is_file():
        print(
            f"Error: subtitles file not found: {args.burn_subtitles}", file=sys.stderr
        )
        return 1

    try:
        timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
        fps = int(args.fps or timeline.get("fps") or 30)
        if args.keyframes:
            kf_dir = args.keyframes_dir or (args.scene_html.parent / "keyframes")
            result = render_keyframes(
                args.scene_html.resolve(),
                timeline,
                kf_dir,
                width=args.width,
                height=args.height,
                browser_path=args.browser_path,
                skip_audit=args.no_audit,
            )
        else:
            assert args.out is not None
            result = render_mp4(
                args.scene_html.resolve(),
                timeline,
                args.out,
                audio_path=args.audio,
                burn_subtitles=args.burn_subtitles,
                fps=fps,
                width=args.width,
                height=args.height,
                crf=args.crf,
                browser_path=args.browser_path,
                workers=args.workers,
            )
    except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error rendering scene: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    if not result.get("ok", True):
        audit_report = result.get("audit")
        issue_count = (
            audit_report["issue_count"] if isinstance(audit_report, dict) else 0
        )
        print(
            f"Layout audit failed with {issue_count} issue(s); inspect keyframes and audit.issues.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
