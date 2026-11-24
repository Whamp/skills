#!/usr/bin/env python3
"""Deterministic headless Chromium frame-capture renderer for paper-to-video."""

from __future__ import annotations

import argparse
import base64
import functools
import http.server
import importlib
import json
import math
import shutil
import subprocess
import sys
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


@dataclass(frozen=True)
class KeyframeTarget:
    """One beat keyframe capture timestamp and filename."""

    index: int
    beat_id: str
    timestamp_s: float
    filename: str


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


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
) -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(_QuietHandler, directory=str(directory))
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
            await new Promise((resolve) =>
                requestAnimationFrame(() => requestAnimationFrame(resolve))
            );
        }""",
        timestamp_s,
    )
    payload = cdp.send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    return base64.b64decode(payload["data"])


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
    for idx in range(len(image_paths)):
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
    return {
        "duration_s": round(float(fmt.get("duration", 0.0)), 3),
        "size_bytes": int(fmt.get("size", 0)),
        "video_codec": video_stream.get("codec_name"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "audio_codec": audio_stream.get("codec_name"),
        "audio_duration_s": round(float(audio_stream["duration"]), 3)
        if audio_stream.get("duration")
        else None,
    }


def _escape_subtitles_filter_path(path: Path) -> str:
    text = str(path.resolve())
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def render_keyframes(
    scene_path: Path,
    timeline: dict[str, Any],
    keyframes_dir: Path,
    *,
    width: int,
    height: int,
    browser_path: Path | None,
) -> dict[str, Any]:
    """Capture one settled PNG per beat plus a contact sheet."""

    targets = compute_keyframe_targets(timeline)
    keyframes_dir.mkdir(parents=True, exist_ok=True)
    playwright_api = _import_playwright()
    server, port = _start_static_server(scene_path.parent)
    captured: list[Path] = []
    started = time.monotonic()

    try:
        with playwright_api.sync_playwright() as p:
            browser = _launch_browser(p, browser_path)
            try:
                url = f"http://127.0.0.1:{port}/{scene_path.name}"
                context, page, cdp, errors = _open_scene(
                    browser, url, timeline, width, height
                )
                try:
                    for target in targets:
                        png_bytes = _capture_frame_png(page, cdp, target.timestamp_s)
                        out_file = keyframes_dir / target.filename
                        out_file.write_bytes(png_bytes)
                        captured.append(out_file)
                    if errors:
                        raise RuntimeError(
                            "scene.html reported runtime errors:\n" + "\n".join(errors)
                        )
                finally:
                    context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

    contact_sheet = _build_contact_sheet(captured, keyframes_dir / "contact_sheet.png")
    return {
        "ok": True,
        "mode": "keyframes",
        "count": len(captured),
        "keyframes_dir": str(keyframes_dir.resolve()),
        "contact_sheet": str(contact_sheet.resolve()) if contact_sheet else None,
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
) -> dict[str, Any]:
    """Capture all frames deterministically and encode H.264 MP4 via ffmpeg."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to render MP4 video")

    duration_s = float(timeline.get("total_duration_s", 0.0))
    if duration_s <= 0:
        raise ValueError("timeline.json total_duration_s must be > 0")
    total_frames = max(1, math.ceil(duration_s * fps))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    playwright_api = _import_playwright()
    server, port = _start_static_server(scene_path.parent)
    started = time.monotonic()

    ffmpeg_cmd: list[str] = [
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
        ffmpeg_cmd.extend(["-i", str(audio_path)])
    if burn_subtitles is not None:
        escaped = _escape_subtitles_filter_path(burn_subtitles)
        style = "FontName=Inter,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H80000000,BorderStyle=3,Outline=1,MarginV=36"
        ffmpeg_cmd.extend(["-vf", f"subtitles='{escaped}':force_style='{style}'"])

    ffmpeg_cmd.extend(
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
        ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    ffmpeg_cmd.extend(["-movflags", "+faststart", str(output_path)])

    proc = subprocess.Popen(
        ffmpeg_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None

    try:
        with playwright_api.sync_playwright() as p:
            browser = _launch_browser(p, browser_path)
            try:
                url = f"http://127.0.0.1:{port}/{scene_path.name}"
                context, page, cdp, errors = _open_scene(
                    browser, url, timeline, width, height
                )
                try:
                    for frame in range(total_frames):
                        t = min(duration_s, frame / fps)
                        png_bytes = _capture_frame_png(page, cdp, t)
                        proc.stdin.write(png_bytes)
                        if (frame + 1) % (fps * 5) == 0 or frame + 1 == total_frames:
                            elapsed = max(0.001, time.monotonic() - started)
                            pct = ((frame + 1) / total_frames) * 100.0
                            print(
                                f"rendered {frame + 1}/{total_frames} frames ({pct:.1f}%, {(frame + 1) / elapsed:.1f} fps)",
                                file=sys.stderr,
                            )
                    if errors:
                        raise RuntimeError(
                            "scene.html reported runtime errors:\n" + "\n".join(errors)
                        )
                finally:
                    context.close()
            finally:
                browser.close()
    except Exception:
        proc.stdin.close()
        proc.kill()
        proc.wait()
        raise
    finally:
        server.shutdown()
        server.server_close()

    proc.stdin.close()
    _, stderr_bytes = proc.communicate()
    if proc.returncode != 0 or not output_path.exists():
        raise RuntimeError(
            f"ffmpeg encoding failed (exit {proc.returncode}): {stderr_bytes.decode('utf-8', errors='replace').strip()}"
        )

    probe = _probe_video(output_path)
    return {
        "ok": True,
        "mode": "video",
        "output": str(output_path.resolve()),
        "frames": total_frames,
        "fps": fps,
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
            )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error rendering scene: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
