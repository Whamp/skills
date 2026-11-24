from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "productivity" / "paper-to-video" / "scripts"


def _load_script_module(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


build_narration = _load_script_module(
    "paper_to_video_build_narration", "build_narration.py"
)
render_video = _load_script_module("paper_to_video_render_video", "render_video.py")


class BuildNarrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _write_beats(self, payload: object) -> Path:
        path = self.root / "beats.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_parse_and_build_timeline_cumulative_timestamps(self) -> None:
        beats_path = self._write_beats(
            {
                "title": "Sample Paper",
                "citation": "Doe et al. 2026 · arXiv:2601.00001",
                "voice": "en-GB-RyanNeural",
                "beats": [
                    {
                        "id": "hook",
                        "text": "Cut the image into patches.",
                        "pause_after_s": 0.4,
                    },
                    {
                        "id": "result",
                        "text": "Capacity explains the gain.",
                        "pause_after_s": 0.6,
                    },
                ],
            }
        )
        script = build_narration.parse_beats_file(beats_path)
        timeline = build_narration.build_timeline_payload(
            script,
            [2.25, 1.75],
            fps=30,
            mode="edge-tts",
            audio_file="narration.m4a",
            measured_audio_duration_s=5.02,
        )

        self.assertEqual(2, len(timeline["beats"]))
        self.assertEqual(0.0, timeline["beats"][0]["start_s"])
        self.assertEqual(2.25, timeline["beats"][0]["audio_end_s"])
        self.assertEqual(2.65, timeline["beats"][0]["end_s"])
        self.assertEqual(2.65, timeline["beats"][1]["start_s"])
        self.assertEqual(4.4, timeline["beats"][1]["audio_end_s"])
        self.assertEqual(5.0, timeline["beats"][1]["end_s"])
        self.assertEqual(5.02, timeline["total_duration_s"])
        self.assertEqual(9, timeline["total_words"])

    def test_duplicate_or_invalid_beat_ids_rejected(self) -> None:
        dup_path = self._write_beats(
            [
                {"id": "same", "text": "First beat."},
                {"id": "same", "text": "Second beat."},
            ]
        )
        with self.assertRaisesRegex(ValueError, "duplicate beat id"):
            build_narration.parse_beats_file(dup_path)

        bad_path = self._write_beats([{"id": "../escape", "text": "Bad id."}])
        with self.assertRaisesRegex(ValueError, "invalid id"):
            build_narration.parse_beats_file(bad_path)

    def test_vtt_and_srt_formatting(self) -> None:
        timeline = {
            "beats": [
                {
                    "index": 1,
                    "id": "hook",
                    "text": "First line.",
                    "start_s": 0.0,
                    "audio_end_s": 2.345,
                },
                {
                    "index": 2,
                    "id": "next",
                    "text": "Second line.",
                    "start_s": 2.75,
                    "audio_end_s": 65.1,
                },
            ]
        }
        vtt = build_narration.format_vtt(timeline)
        srt = build_narration.format_srt(timeline)

        self.assertIn("WEBVTT", vtt)
        self.assertIn("00:00:00.000 --> 00:00:02.345", vtt)
        self.assertIn("00:00:02.750 --> 00:01:05.100", vtt)
        self.assertIn("1\n00:00:00,000 --> 00:00:02,345\nFirst line.", srt)
        self.assertIn("2\n00:00:02,750 --> 00:01:05,100\nSecond line.", srt)

    def test_silent_mode_cli_writes_timeline_and_subtitles(self) -> None:
        beats_path = self._write_beats(
            {
                "title": "Silent Test",
                "beats": [
                    {
                        "id": "intro",
                        "text": "Four words right here.",
                        "pause_after_s": 0.5,
                    },
                    {"id": "end", "text": "Closing thought.", "pause_after_s": 0.5},
                ],
            }
        )
        out_dir = self.root / "out"
        exit_code = build_narration.main(
            [str(beats_path), "--out-dir", str(out_dir), "--silent"]
        )
        self.assertEqual(0, exit_code)

        timeline = json.loads((out_dir / "timeline.json").read_text(encoding="utf-8"))
        self.assertEqual("silent", timeline["mode"])
        self.assertTrue((out_dir / "subtitles.vtt").is_file())
        self.assertTrue((out_dir / "subtitles.srt").is_file())


class RenderVideoTests(unittest.TestCase):
    def test_compute_keyframe_targets_picks_settled_point(self) -> None:
        timeline = {
            "beats": [
                {
                    "index": 1,
                    "id": "hook",
                    "start_s": 0.0,
                    "audio_end_s": 4.0,
                    "end_s": 4.4,
                },
                {
                    "index": 2,
                    "id": "tiny",
                    "start_s": 4.4,
                    "audio_end_s": 4.6,
                    "end_s": 5.0,
                },
            ]
        }
        targets = render_video.compute_keyframe_targets(timeline)
        self.assertEqual(2, len(targets))
        self.assertEqual("01_hook.png", targets[0].filename)
        self.assertEqual(3.4, targets[0].timestamp_s)
        self.assertEqual("02_tiny.png", targets[1].filename)
        self.assertEqual(4.5, targets[1].timestamp_s)

    def test_help_flags_do_not_crash_argparse(self) -> None:
        with self.assertRaises(SystemExit) as ctx1:
            build_narration.main(["--help"])
        self.assertEqual(0, ctx1.exception.code)
        with self.assertRaises(SystemExit) as ctx2:
            render_video.main(["--help"])
        self.assertEqual(0, ctx2.exception.code)

    def test_escape_subtitles_filter_path(self) -> None:
        escaped = render_video._escape_subtitles_filter_path(Path("/tmp/a:b'c/sub.srt"))
        self.assertIn("\\:", escaped)
        self.assertIn("\\'", escaped)


if __name__ == "__main__":
    unittest.main()
