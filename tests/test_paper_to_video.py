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
        self.assertTrue((out_dir / "stage_helpers.js").is_file())

    def test_spoken_text_and_subtitle_text_overrides(self) -> None:
        beats_path = self._write_beats(
            {
                "title": "Pronunciation Test",
                "beats": [
                    {
                        "id": "bpe",
                        "text": "BPE fails at 1.3B.",
                        "spoken_text": "B P E fails at one point three billion.",
                        "pause_after_s": 0.3,
                    },
                    {
                        "id": "custom_sub",
                        "text": "Default text.",
                        "subtitle_text": "Explicit subtitle.",
                        "pause_after_s": 0.3,
                    },
                ],
            }
        )
        script = build_narration.parse_beats_file(beats_path)
        self.assertEqual(
            "B P E fails at one point three billion.",
            script.beats[0].effective_spoken_text,
        )
        self.assertEqual("BPE fails at 1.3B.", script.beats[0].effective_subtitle_text)
        self.assertEqual(9, script.beats[0].word_count)

        cmd = build_narration.build_edge_tts_command(
            ["edge-tts"], script.beats[0], self.root / "01_bpe.mp3"
        )
        text_index = cmd.index("--text") + 1
        self.assertEqual("B P E fails at one point three billion.", cmd[text_index])

        timeline = build_narration.build_timeline_payload(script, [3.0, 2.0])
        self.assertEqual(
            "B P E fails at one point three billion.",
            timeline["beats"][0]["spoken_text"],
        )
        self.assertNotIn("subtitle_text", timeline["beats"][0])
        self.assertEqual("Explicit subtitle.", timeline["beats"][1]["subtitle_text"])

        vtt = build_narration.format_vtt(timeline)
        srt = build_narration.format_srt(timeline)
        self.assertIn("BPE fails at 1.3B.", vtt)
        self.assertNotIn("B P E", vtt)
        self.assertIn("Explicit subtitle.", srt)

    def test_empty_spoken_or_subtitle_override_rejected(self) -> None:
        bad_spoken = self._write_beats(
            [{"id": "a", "text": "Valid text.", "spoken_text": "   "}]
        )
        with self.assertRaisesRegex(ValueError, "spoken_text"):
            build_narration.parse_beats_file(bad_spoken)

        bad_sub = self._write_beats(
            [{"id": "a", "text": "Valid text.", "subtitle_text": ""}]
        )
        with self.assertRaisesRegex(ValueError, "subtitle_text"):
            build_narration.parse_beats_file(bad_sub)

    def test_pacing_warning_threshold_flags_over_150s(self) -> None:
        beats_path = self._write_beats([{"id": "a", "text": "Short beat."}])
        script = build_narration.parse_beats_file(beats_path)
        self.assertEqual([], build_narration.collect_pacing_warnings(script, 125.0))
        warnings = build_narration.collect_pacing_warnings(script, 155.0)
        self.assertEqual(1, len(warnings))
        self.assertIn("155.0s", warnings[0])


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

    def test_compute_frame_ranges_partitions_frames_contiguously(self) -> None:
        self.assertEqual(
            [(0, 3), (3, 6), (6, 8), (8, 10)],
            render_video.compute_frame_ranges(10, 4),
        )
        self.assertEqual(
            [(0, 1), (1, 2), (2, 3)],
            render_video.compute_frame_ranges(3, 8),
        )
        self.assertEqual([(0, 100)], render_video.compute_frame_ranges(100, 1))
        with self.assertRaises(ValueError):
            render_video.compute_frame_ranges(0, 4)
        with self.assertRaises(ValueError):
            render_video.compute_frame_ranges(10, 0)

    def test_audit_frame_geometry_passes_clean_scene(self) -> None:
        geometry = {
            "has_katex": True,
            "all_math_node_count": 1,
            "math_nodes": [
                {
                    "text": "p_t = 1/2",
                    "has_rendered_katex": True,
                    "has_katex_error": False,
                    "rect": {
                        "left": 700,
                        "top": 400,
                        "right": 920,
                        "bottom": 450,
                        "width": 220,
                        "height": 50,
                    },
                }
            ],
            "texts": [
                {
                    "text": "Cosine Routing",
                    "rect": {
                        "left": 200,
                        "top": 68,
                        "right": 360,
                        "bottom": 96,
                        "width": 160,
                        "height": 28,
                    },
                },
                {
                    "text": "Sub-label",
                    "rect": {
                        "left": 200,
                        "top": 130,
                        "right": 310,
                        "bottom": 156,
                        "width": 110,
                        "height": 26,
                    },
                },
            ],
            "shapes": [
                {
                    "tag": "rect",
                    "rect": {
                        "left": 180,
                        "top": 58,
                        "right": 380,
                        "bottom": 106,
                        "width": 200,
                        "height": 48,
                    },
                }
            ],
        }
        issues = render_video.audit_frame_geometry(
            geometry, beat_id="hook", timestamp_s=1.5, width=1920, height=1080
        )
        self.assertEqual([], issues)

    def test_audit_frame_geometry_detects_katex_failures(self) -> None:
        missing_katex = {
            "has_katex": False,
            "all_math_node_count": 1,
            "math_nodes": [
                {
                    "text": r"\sum x_i",
                    "has_rendered_katex": False,
                    "has_katex_error": False,
                    "rect": {
                        "left": 400,
                        "top": 400,
                        "right": 560,
                        "bottom": 440,
                        "width": 160,
                        "height": 40,
                    },
                }
            ],
            "texts": [],
            "shapes": [],
        }
        issues = render_video.audit_frame_geometry(
            missing_katex, beat_id="eq", timestamp_s=3.0, width=1920, height=1080
        )
        kinds = {issue.kind for issue in issues}
        self.assertEqual({"katex_missing", "katex_unrendered"}, kinds)

        parse_err = {
            "has_katex": True,
            "all_math_node_count": 1,
            "math_nodes": [
                {
                    "text": r"\invalidmacro",
                    "has_rendered_katex": True,
                    "has_katex_error": True,
                    "rect": {
                        "left": 400,
                        "top": 400,
                        "right": 560,
                        "bottom": 440,
                        "width": 160,
                        "height": 40,
                    },
                }
            ],
            "texts": [],
            "shapes": [],
        }
        err_issues = render_video.audit_frame_geometry(
            parse_err, beat_id="eq", timestamp_s=3.0, width=1920, height=1080
        )
        self.assertEqual(["katex_parse_error"], [issue.kind for issue in err_issues])

    def test_audit_frame_geometry_detects_margins_overlaps_and_collisions(self) -> None:
        geometry = {
            "has_katex": True,
            "all_math_node_count": 0,
            "math_nodes": [],
            "texts": [
                {
                    "text": "Too far left",
                    "rect": {
                        "left": 40,
                        "top": 200,
                        "right": 180,
                        "bottom": 228,
                        "width": 140,
                        "height": 28,
                    },
                },
                {
                    "text": "Main M",
                    "rect": {
                        "left": 500,
                        "top": 300,
                        "right": 620,
                        "bottom": 328,
                        "width": 120,
                        "height": 28,
                    },
                },
                {
                    "text": "Overlapping label",
                    "rect": {
                        "left": 560,
                        "top": 304,
                        "right": 740,
                        "bottom": 332,
                        "width": 180,
                        "height": 28,
                    },
                },
                {
                    "text": "Target 1/N",
                    "rect": {
                        "left": 900,
                        "top": 500,
                        "right": 1020,
                        "bottom": 528,
                        "width": 120,
                        "height": 28,
                    },
                },
            ],
            "shapes": [
                {
                    "tag": "rect",
                    "rect": {
                        "left": 540,
                        "top": 280,
                        "right": 780,
                        "bottom": 360,
                        "width": 240,
                        "height": 80,
                    },
                },
                {
                    "tag": "polygon",
                    "rect": {
                        "left": 940,
                        "top": 502,
                        "right": 960,
                        "bottom": 520,
                        "width": 20,
                        "height": 18,
                    },
                },
            ],
        }
        issues = render_video.audit_frame_geometry(
            geometry, beat_id="mech", timestamp_s=10.0, width=1920, height=1080
        )
        kinds = [issue.kind for issue in issues]
        self.assertIn("safe_margin", kinds)
        self.assertIn("text_overlap", kinds)
        self.assertEqual(2, kinds.count("shape_collision"))

    def test_help_flags_do_not_crash_argparse(self) -> None:
        with self.assertRaises(SystemExit) as ctx1:
            build_narration.main(["--help"])
        self.assertEqual(0, ctx1.exception.code)
        with self.assertRaises(SystemExit) as ctx2:
            render_video.main(["--help"])
        self.assertEqual(0, ctx2.exception.code)

    def test_workers_cli_validation_rejects_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene = root / "scene.html"
            timeline = root / "timeline.json"
            scene.write_text("<html></html>", encoding="utf-8")
            timeline.write_text('{"beats":[]}', encoding="utf-8")
            code = render_video.main(
                [
                    str(scene),
                    "--timeline",
                    str(timeline),
                    "--out",
                    str(root / "out.mp4"),
                    "--workers",
                    "0",
                ]
            )
            self.assertEqual(2, code)

    def test_escape_subtitles_filter_path(self) -> None:
        escaped = render_video._escape_subtitles_filter_path(Path("/tmp/a:b'c/sub.srt"))
        self.assertIn("\\:", escaped)
        self.assertIn("\\'", escaped)


if __name__ == "__main__":
    unittest.main()
