"""Check that the eval rejects false speed wins and preserves search misses."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import eval_discoverable_code as runner


class DiscoverabilityEvalTests(unittest.TestCase):
    """Exercise replay and scoring across real files and ripgrep."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        (self.workspace / "private").mkdir()
        (self.workspace / "validation.txt").write_text(
            "Existing tests: 7 passed; exit 0\n"
        )
        runner.write_json(
            self.workspace / "private/suite.json",
            {"targets": [{"id": "example", "tasks": [{"id": "behavior"}]}]},
        )
        self.readers: list[runner.Reader] = []
        self.grades: list[runner.Grade] = []
        for reader_id, arm, commands, output_bytes in (
            ("r01", "original", 8, 1200),
            ("r02", "skill", 3, 400),
        ):
            folder = self.workspace / "readers" / reader_id
            (folder / "repo").mkdir(parents=True)
            (folder / "repo/module.py").write_text("def implementation(): pass\n")
            (folder / "answer.txt").write_text("Implementation: module.py:1\n")
            (folder / "transcript.txt").write_text("Archived model/tool transcript\n")
            self.readers.append(
                runner.Reader(
                    id=reader_id,
                    target="example",
                    arm=arm,
                    tree_sha256=runner.tree_hash(folder / "repo"),
                )
            )
            self.grades.append(
                runner.Grade(
                    reader=reader_id,
                    tasks={
                        "behavior": runner.TaskGrade(
                            correct=True,
                            reason="Code citation supports all rubric facts",
                        )
                    },
                    commands=commands,
                    output_bytes=output_bytes,
                    elapsed_seconds=120,
                    preservation_passed=True,
                    validation_log="validation.txt",
                )
            )
        runner.write_json(self.workspace / "private/readers.json", self.readers)

    def save_grades(self) -> None:
        """Save a controller's audit through the real JSON input boundary."""
        runner.write_json(self.workspace / "private/grades.json", self.grades)

    def test_correct_pair_reports_absolute_effort_saved(self) -> None:
        self.save_grades()
        result = subprocess.run(
            [sys.executable, runner.__file__, "score", str(self.workspace)],
            capture_output=True,
            text=True,
            check=True,
        )
        saved = json.loads((self.workspace / "private/score.json").read_text())
        self.assertEqual(saved, json.loads(result.stdout))
        report = saved[0]
        self.assertTrue(report["effort_comparison_eligible"])
        self.assertEqual({"original": 1, "skill": 1}, report["correct_tasks"])
        self.assertEqual(5, report["commands_saved"])
        self.assertEqual(800, report["output_bytes_saved"])

    def test_faster_wrong_answer_or_behavior_change_is_not_a_win(self) -> None:
        for failure in ("wrong_answer", "behavior_change"):
            with self.subTest(failure=failure):
                grade = self.grades[1]
                grade["tasks"]["behavior"]["correct"] = failure != "wrong_answer"
                grade["preservation_passed"] = failure != "behavior_change"
                self.save_grades()
                report = runner.score(self.workspace)[0]
                self.assertFalse(report["effort_comparison_eligible"])
                self.assertIsNone(report["commands_saved"])
                self.assertIsNone(report["output_bytes_saved"])

    def test_ungraded_duplicate_or_missing_readers_are_rejected(self) -> None:
        cases = [self.grades[:1], self.grades + self.grades[:1]]
        for grades in cases:
            with self.subTest(rows=len(grades)):
                runner.write_json(self.workspace / "private/grades.json", grades)
                with self.assertRaisesRegex(ValueError, "every reader exactly once"):
                    runner.score(self.workspace)
        self.grades[1]["tasks"]["behavior"]["correct"] = None
        self.save_grades()
        with self.assertRaisesRegex(ValueError, "Incomplete task grades"):
            runner.score(self.workspace)

    def test_reader_budget_overrun_is_not_a_speed_win(self) -> None:
        self.grades[1]["elapsed_seconds"] = 601
        self.save_grades()
        report = runner.score(self.workspace)[0]
        self.assertEqual({"original": True, "skill": False}, report["budget_compliant"])
        self.assertFalse(report["effort_comparison_eligible"])
        self.assertIsNone(report["commands_saved"])

    def test_absent_measurements_are_not_zero_effort(self) -> None:
        self.grades[1]["output_bytes"] = None
        self.save_grades()
        with self.assertRaisesRegex(ValueError, "Missing or invalid output_bytes"):
            runner.score(self.workspace)

    def test_source_change_and_missing_evidence_are_rejected(self) -> None:
        self.save_grades()
        folder = self.workspace / "readers/r02"
        (folder / "answer.txt").unlink()
        with self.assertRaisesRegex(ValueError, "Missing evidence"):
            runner.score(self.workspace)
        (folder / "answer.txt").write_text("Answer restored\n")
        (folder / "repo/module.py").write_text("def wrong_implementation(): pass\n")
        with self.assertRaisesRegex(ValueError, "Reader source changed"):
            runner.score(self.workspace)

    def test_literal_replay_does_not_treat_paraphrases_as_hits(self) -> None:
        root = self.workspace / "readers/r01/repo"
        (root / "session.py").write_text("# The session has expired.\n")
        miss = runner.replay(root, {"kind": "literal", "value": "session expired"})
        self.assertEqual(0, miss["lines"])
        hit = runner.replay(root, {"kind": "literal", "value": "session has expired"})
        self.assertEqual(1, hit["lines"])
        self.assertIn("session.py:1", str(hit["output"]))
        (root / "docs").mkdir()
        (root / "docs/guide.txt").write_text("The session has expired.\n")
        noisy = runner.replay(root, {"kind": "literal", "value": "session has expired"})
        self.assertEqual(2, noisy["lines"])
        glob = runner.replay(root, {"kind": "glob", "value": "*session*.py"})
        self.assertEqual("session.py\n", glob["output"])
        json.dumps(noisy)  # Replay evidence must remain serializable.


if __name__ == "__main__":
    unittest.main()
