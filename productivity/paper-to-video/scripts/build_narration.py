#!/usr/bin/env python3
"""Build audio-first narration, subtitles, and exact beat timeline for paper-to-video."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_VOICE = "en-GB-RyanNeural"
DEFAULT_RATE = "+0%"
DEFAULT_PITCH = "+0Hz"
DEFAULT_PAUSE_S = 0.35
DEFAULT_WPM = 140.0
BEAT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")
STAGE_HELPERS_ASSET = (
    Path(__file__).resolve().parent.parent / "assets" / "stage_helpers.js"
)


@dataclass(frozen=True)
class BeatInput:
    """Validated narration beat read from beats.json."""

    index: int
    beat_id: str
    text: str
    pause_after_s: float
    visual_cue: str
    voice: str
    rate: str
    pitch: str
    spoken_text: str = ""
    subtitle_text: str = ""
    explicit_duration_s: float | None = None

    @property
    def effective_spoken_text(self) -> str:
        """Return text sent to TTS (spoken_text override if set, else text)."""
        return self.spoken_text or self.text

    @property
    def effective_subtitle_text(self) -> str:
        """Return text written to VTT/SRT subtitles (subtitle_text if set, else text)."""
        return self.subtitle_text or self.text

    @property
    def word_count(self) -> int:
        return len(self.effective_spoken_text.split())


@dataclass(frozen=True)
class ScriptInput:
    """Top-level script specification."""

    title: str
    citation: str
    voice: str
    rate: str
    pitch: str
    beats: tuple[BeatInput, ...]


def parse_beats_file(
    path: Path,
    *,
    default_voice: str = DEFAULT_VOICE,
    default_rate: str = DEFAULT_RATE,
    default_pitch: str = DEFAULT_PITCH,
) -> ScriptInput:
    """Load and validate beats.json into a normalized ScriptInput."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        title = ""
        citation = ""
        script_voice = default_voice
        script_rate = default_rate
        script_pitch = default_pitch
        raw_beats = raw
    elif isinstance(raw, dict):
        title = str(raw.get("title", "")).strip()
        citation = str(raw.get("citation", "")).strip()
        script_voice = str(raw.get("voice") or default_voice).strip()
        script_rate = str(raw.get("rate") or default_rate).strip()
        script_pitch = str(raw.get("pitch") or default_pitch).strip()
        raw_beats = raw.get("beats")
    else:
        raise TypeError(
            "beats.json must be a JSON object with a 'beats' list or a JSON list"
        )

    if not isinstance(raw_beats, list) or not raw_beats:
        raise ValueError("beats.json must contain a non-empty 'beats' list")

    seen_ids: set[str] = set()
    beats: list[BeatInput] = []
    for index, item in enumerate(raw_beats, start=1):
        if not isinstance(item, dict):
            raise TypeError(f"beat #{index} must be a JSON object")

        beat_id = str(item.get("id", "")).strip()
        if not BEAT_ID_PATTERN.match(beat_id):
            raise ValueError(
                f"beat #{index} has invalid id {beat_id!r}; use 1-64 chars of [A-Za-z0-9_-] starting with alphanumeric"
            )
        if beat_id in seen_ids:
            raise ValueError(f"duplicate beat id {beat_id!r}")
        seen_ids.add(beat_id)

        text = " ".join(str(item.get("text", "")).split())
        if not text:
            raise ValueError(f"beat {beat_id!r} requires non-empty 'text'")

        spoken_text = _parse_optional_text_override(item, "spoken_text", beat_id)
        subtitle_text = _parse_optional_text_override(item, "subtitle_text", beat_id)

        pause_raw = item.get("pause_after_s", DEFAULT_PAUSE_S)
        try:
            pause_after_s = float(pause_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"beat {beat_id!r} has non-numeric pause_after_s") from exc
        if pause_after_s < 0:
            raise ValueError(f"beat {beat_id!r} pause_after_s must be >= 0")

        explicit_duration: float | None = None
        if "duration_s" in item and item["duration_s"] is not None:
            try:
                explicit_duration = float(item["duration_s"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"beat {beat_id!r} has non-numeric duration_s"
                ) from exc
            if explicit_duration <= 0:
                raise ValueError(f"beat {beat_id!r} duration_s must be > 0")

        beats.append(
            BeatInput(
                index=index,
                beat_id=beat_id,
                text=text,
                pause_after_s=round(pause_after_s, 3),
                visual_cue=str(item.get("visual_cue", "")).strip(),
                voice=str(item.get("voice") or script_voice).strip(),
                rate=str(item.get("rate") or script_rate).strip(),
                pitch=str(item.get("pitch") or script_pitch).strip(),
                spoken_text=spoken_text,
                subtitle_text=subtitle_text,
                explicit_duration_s=explicit_duration,
            )
        )

    return ScriptInput(
        title=title,
        citation=citation,
        voice=script_voice,
        rate=script_rate,
        pitch=script_pitch,
        beats=tuple(beats),
    )


def _parse_optional_text_override(
    item: dict[str, Any], field: str, beat_id: str
) -> str:
    raw = item.get(field)
    if raw is None:
        return ""
    cleaned = " ".join(str(raw).split())
    if not cleaned:
        raise ValueError(f"beat {beat_id!r} {field} must be non-empty when provided")
    return cleaned


def estimate_beat_duration(beat: BeatInput, wpm: float = DEFAULT_WPM) -> float:
    """Estimate spoken duration in seconds when running in dry-run or silent mode."""

    if beat.explicit_duration_s is not None:
        return round(beat.explicit_duration_s, 3)
    words_per_second = max(1.0, wpm / 60.0)
    return round(max(1.8, beat.word_count / words_per_second), 3)


def build_timeline_payload(
    script: ScriptInput,
    audio_durations_s: list[float],
    *,
    fps: int = 30,
    mode: str = "edge-tts",
    audio_file: str | None = None,
    measured_audio_duration_s: float | None = None,
) -> dict[str, Any]:
    """Compute exact cumulative timestamps for every beat."""

    if len(audio_durations_s) != len(script.beats):
        raise ValueError("audio_durations_s length must match script.beats length")

    cursor = 0.0
    timeline_beats: list[dict[str, Any]] = []
    total_words = 0
    total_spoken_s = 0.0

    for beat, raw_audio_dur in zip(script.beats, audio_durations_s, strict=True):
        audio_dur = round(float(raw_audio_dur), 3)
        start_s = round(cursor, 3)
        audio_end_s = round(start_s + audio_dur, 3)
        end_s = round(audio_end_s + beat.pause_after_s, 3)
        duration_s = round(end_s - start_s, 3)
        cursor = end_s
        total_words += beat.word_count
        total_spoken_s += audio_dur

        beat_entry: dict[str, Any] = {
            "index": beat.index,
            "id": beat.beat_id,
            "text": beat.text,
            "visual_cue": beat.visual_cue,
            "word_count": beat.word_count,
            "start_s": start_s,
            "audio_end_s": audio_end_s,
            "end_s": end_s,
            "audio_duration_s": audio_dur,
            "pause_after_s": beat.pause_after_s,
            "duration_s": duration_s,
        }
        if beat.effective_spoken_text != beat.text:
            beat_entry["spoken_text"] = beat.effective_spoken_text
        if beat.effective_subtitle_text != beat.text:
            beat_entry["subtitle_text"] = beat.effective_subtitle_text
        timeline_beats.append(beat_entry)

    total_duration_s = round(cursor, 3)
    wpm = round((total_words / total_spoken_s) * 60.0, 1) if total_spoken_s > 0 else 0.0
    payload: dict[str, Any] = {
        "title": script.title,
        "citation": script.citation,
        "voice": script.voice,
        "mode": mode,
        "fps": fps,
        "total_words": total_words,
        "spoken_wpm": wpm,
        "total_duration_s": total_duration_s,
        "beats": timeline_beats,
    }
    if audio_file is not None:
        payload["audio_file"] = audio_file
    if measured_audio_duration_s is not None:
        payload["measured_audio_duration_s"] = round(measured_audio_duration_s, 3)
        payload["total_duration_s"] = round(
            max(total_duration_s, measured_audio_duration_s), 3
        )
    return payload


def _format_timestamp(seconds: float, *, decimal_sep: str) -> str:
    total_ms = max(0, round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{decimal_sep}{ms:03d}"


def format_vtt(timeline: dict[str, Any]) -> str:
    """Format WebVTT subtitles aligned to each beat's spoken span."""

    lines = ["WEBVTT", ""]
    for beat in timeline["beats"]:
        start = _format_timestamp(beat["start_s"], decimal_sep=".")
        end = _format_timestamp(beat["audio_end_s"], decimal_sep=".")
        lines.append(f"{start} --> {end}")
        lines.append(str(beat.get("subtitle_text") or beat["text"]))
        lines.append("")
    return "\n".join(lines)


def format_srt(timeline: dict[str, Any]) -> str:
    """Format SubRip (.srt) subtitles aligned to each beat's spoken span."""

    lines: list[str] = []
    for beat in timeline["beats"]:
        start = _format_timestamp(beat["start_s"], decimal_sep=",")
        end = _format_timestamp(beat["audio_end_s"], decimal_sep=",")
        lines.append(str(beat["index"]))
        lines.append(f"{start} --> {end}")
        lines.append(str(beat.get("subtitle_text") or beat["text"]))
        lines.append("")
    return "\n".join(lines)


def resolve_edge_tts_command() -> list[str]:
    """Locate edge-tts directly or through uvx."""

    direct = shutil.which("edge-tts")
    if direct:
        return [direct]
    uvx = shutil.which("uvx")
    if uvx:
        return [uvx, "--from", "edge-tts", "edge-tts"]
    raise RuntimeError(
        "edge-tts not found on PATH and uvx is unavailable; install edge-tts or pass --audio-dir / --silent"
    )


def probe_audio_duration(path: Path) -> float:
    """Return exact audio duration in seconds via ffprobe."""

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError(
            "ffprobe is required to measure audio duration (install ffmpeg)"
        )
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr.strip()}")
    return float(result.stdout.strip())


def build_edge_tts_command(
    edge_cmd: list[str],
    beat: BeatInput,
    output_path: Path,
) -> list[str]:
    """Construct the edge-tts CLI command using the beat's effective spoken text."""

    return [
        *edge_cmd,
        "--voice",
        beat.voice,
        "--rate",
        beat.rate,
        "--pitch",
        beat.pitch,
        "--text",
        beat.effective_spoken_text,
        "--write-media",
        str(output_path),
    ]


def synthesize_edge_tts_clip(
    edge_cmd: list[str],
    beat: BeatInput,
    output_path: Path,
) -> None:
    """Synthesize one beat clip via edge-tts."""

    cmd = build_edge_tts_command(edge_cmd, beat, output_path)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(
            f"edge-tts failed on beat {beat.beat_id!r} (exit {result.returncode}): {result.stderr.strip()}"
        )


def copy_stage_helpers(out_dir: Path) -> Path | None:
    """Copy bundled stage_helpers.js into out_dir if absent."""

    if not STAGE_HELPERS_ASSET.is_file():
        return None
    dest = out_dir / STAGE_HELPERS_ASSET.name
    if not dest.exists():
        shutil.copy2(STAGE_HELPERS_ASSET, dest)
    return dest


def locate_external_clip(audio_dir: Path, beat: BeatInput) -> Path:
    """Find a pre-generated clip for beat.beat_id inside audio_dir."""

    candidates = [audio_dir / f"{beat.beat_id}{ext}" for ext in AUDIO_EXTENSIONS] + [
        audio_dir / f"{beat.index:02d}_{beat.beat_id}{ext}" for ext in AUDIO_EXTENSIONS
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"missing audio clip for beat {beat.beat_id!r} in {audio_dir} (checked {AUDIO_EXTENSIONS})"
    )


def concat_audio_clips(
    clip_paths: list[Path],
    pauses_s: list[float],
    output_path: Path,
) -> float:
    """Normalize and concatenate per-beat clips with exact trailing pauses into narration.m4a."""

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to assemble narration.m4a")

    cmd: list[str] = [ffmpeg, "-y", "-v", "error"]
    for clip in clip_paths:
        cmd.extend(["-i", str(clip)])

    filter_parts: list[str] = []
    stream_labels: list[str] = []
    for idx, pause_s in enumerate(pauses_s):
        label = f"a{idx}"
        pad = f",apad=pad_dur={pause_s:.3f}" if pause_s > 0 else ""
        filter_parts.append(
            f"[{idx}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo{pad}[{label}]"
        )
        stream_labels.append(f"[{label}]")

    filter_parts.append(
        f"{''.join(stream_labels)}concat=n={len(clip_paths)}:v=0:a=1[out]"
    )
    cmd.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[out]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"ffmpeg concat failed: {result.stderr.strip()}")
    return probe_audio_duration(output_path)


def collect_pacing_warnings(script: ScriptInput, total_duration_s: float) -> list[str]:
    """Return non-fatal warnings when beats or total runtime look out of bounds."""

    warnings: list[str] = []
    for beat in script.beats:
        if beat.word_count > 45:
            warnings.append(
                f"beat {beat.beat_id!r} has {beat.word_count} words; split beats over ~35 words for tighter animation cues"
            )
    if total_duration_s > 150:
        warnings.append(
            f"total duration is {total_duration_s:.1f}s (> 2.5 minutes); tighten toward 100-130s unless a longer video was requested"
        )
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synthesize audio-first narration and exact timeline.json for paper-to-video."
    )
    parser.add_argument("beats_json", type=Path, help="Path to beats.json")
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for timeline.json, subtitles, clips, and narration.m4a",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Default edge-tts voice ({DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--rate",
        default=DEFAULT_RATE,
        help="Default edge-tts speaking rate (default: +0%%)",
    )
    parser.add_argument(
        "--pitch",
        default=DEFAULT_PITCH,
        help=f"Default edge-tts pitch ({DEFAULT_PITCH})",
    )
    parser.add_argument(
        "--fps", type=int, default=30, help="Target video frame rate (default 30)"
    )
    parser.add_argument(
        "--audio-dir",
        type=Path,
        help="Directory containing pre-generated per-beat audio clips (<beat-id>.mp3/.wav/.m4a)",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Estimate durations without synthesizing speech (for silent subtitled videos)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate beats.json and report estimated pacing without writing media",
    )
    args = parser.parse_args(argv)

    if args.audio_dir and args.silent:
        print("Error: --audio-dir and --silent cannot be combined", file=sys.stderr)
        return 2

    try:
        script = parse_beats_file(
            args.beats_json,
            default_voice=args.voice,
            default_rate=args.rate,
            default_pitch=args.pitch,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error reading {args.beats_json}: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        estimated = [estimate_beat_duration(beat) for beat in script.beats]
        timeline = build_timeline_payload(
            script, estimated, fps=args.fps, mode="dry-run"
        )
        warnings = collect_pacing_warnings(script, timeline["total_duration_s"])
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "dry-run",
                    "beats": len(script.beats),
                    "total_words": timeline["total_words"],
                    "estimated_duration_s": timeline["total_duration_s"],
                    "warnings": warnings,
                },
                indent=2,
            )
        )
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = args.out_dir / "clips"

    try:
        if args.silent:
            durations = [estimate_beat_duration(beat) for beat in script.beats]
            timeline = build_timeline_payload(
                script, durations, fps=args.fps, mode="silent"
            )
        else:
            clip_paths: list[Path] = []
            durations = []
            if args.audio_dir:
                mode = "external-audio"
                for beat in script.beats:
                    clip = locate_external_clip(args.audio_dir, beat)
                    clip_paths.append(clip)
                    durations.append(probe_audio_duration(clip))
            else:
                mode = "edge-tts"
                edge_cmd = resolve_edge_tts_command()
                clips_dir.mkdir(parents=True, exist_ok=True)
                for beat in script.beats:
                    clip = clips_dir / f"{beat.index:02d}_{beat.beat_id}.mp3"
                    print(
                        f"[{beat.index}/{len(script.beats)}] synthesizing {beat.beat_id} ({beat.word_count} words)...",
                        file=sys.stderr,
                    )
                    synthesize_edge_tts_clip(edge_cmd, beat, clip)
                    clip_paths.append(clip)
                    durations.append(probe_audio_duration(clip))

            narration_path = args.out_dir / "narration.m4a"
            measured_total = concat_audio_clips(
                clip_paths,
                [beat.pause_after_s for beat in script.beats],
                narration_path,
            )
            timeline = build_timeline_payload(
                script,
                durations,
                fps=args.fps,
                mode=mode,
                audio_file=narration_path.name,
                measured_audio_duration_s=measured_total,
            )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error building narration: {exc}", file=sys.stderr)
        return 1

    timeline_path = args.out_dir / "timeline.json"
    vtt_path = args.out_dir / "subtitles.vtt"
    srt_path = args.out_dir / "subtitles.srt"
    timeline_path.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    vtt_path.write_text(format_vtt(timeline), encoding="utf-8")
    srt_path.write_text(format_srt(timeline), encoding="utf-8")
    stage_helpers_path = copy_stage_helpers(args.out_dir)

    warnings = collect_pacing_warnings(script, timeline["total_duration_s"])
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    print(
        json.dumps(
            {
                "ok": True,
                "mode": timeline["mode"],
                "beats": len(timeline["beats"]),
                "total_words": timeline["total_words"],
                "spoken_wpm": timeline["spoken_wpm"],
                "total_duration_s": timeline["total_duration_s"],
                "timeline": str(timeline_path.resolve()),
                "audio": str((args.out_dir / timeline["audio_file"]).resolve())
                if "audio_file" in timeline
                else None,
                "subtitles_vtt": str(vtt_path.resolve()),
                "subtitles_srt": str(srt_path.resolve()),
                "stage_helpers": str(stage_helpers_path.resolve())
                if stage_helpers_path
                else None,
                "warnings": warnings,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
