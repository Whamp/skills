"""Check that the eval rejects false speed wins and preserves search misses."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import eval_discoverable_code as runner
from tests.test_discovery_pi import completed_events, profile_fixture


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

    def test_generic_rewrite_gets_its_own_comparison(self) -> None:
        shutil.copytree(self.workspace / "readers/r01", self.workspace / "readers/r03")
        generic_reader: runner.Reader = {
            **self.readers[0],
            "id": "r03",
            "arm": "generic",
        }
        self.readers.append(generic_reader)
        generic_grade = copy.deepcopy(self.grades[0])
        generic_grade.update(reader="r03", commands=6, output_bytes=800)
        self.grades.append(generic_grade)
        runner.write_json(self.workspace / "private/readers.json", self.readers)
        self.save_grades()
        report = runner.score(self.workspace)[0]
        self.assertEqual(3, report["commands_saved_vs_generic"])
        self.assertEqual(400, report["output_bytes_saved_vs_generic"])
        self.assertEqual({"original": 8, "skill": 3, "generic": 6}, report["commands"])

    def test_new_run_cannot_score_without_verified_pi_evidence(self) -> None:
        (self.workspace / "private/skill.txt").write_text("fixture skill")
        runner.write_json(
            self.workspace / "private/inputs.json",
            {
                "schema_version": 2,
                "suite_sha256": hashlib.sha256(
                    (self.workspace / "private/suite.json").read_bytes()
                ).hexdigest(),
                "skill_sha256": hashlib.sha256(
                    (self.workspace / "private/skill.txt").read_bytes()
                ).hexdigest(),
            },
        )
        self.save_grades()
        with self.assertRaises(FileNotFoundError):
            runner.score(self.workspace)

    def test_verified_score_checks_raw_metrics_model_route_and_tested_source(
        self,
    ) -> None:
        private = self.workspace / "private"
        suite = json.loads((private / "suite.json").read_text())
        suite["arms"] = ["original", "skill"]
        runner.write_json(private / "suite.json", suite)
        for reader in self.readers:
            reader["task"] = "behavior"
        runner.write_json(private / "readers.json", self.readers)
        (private / "skill.txt").write_text("fixture skill")
        runner.write_json(
            private / "inputs.json",
            {
                "schema_version": 3,
                "suite_sha256": hashlib.sha256(
                    (private / "suite.json").read_bytes()
                ).hexdigest(),
                "skill_sha256": hashlib.sha256(
                    (private / "skill.txt").read_bytes()
                ).hexdigest(),
            },
        )
        for reader, grade in zip(self.readers, self.grades):
            folder = self.workspace / "readers" / reader["id"] / "pi"
            folder.mkdir()
            profile = profile_fixture(folder.parent / "repo")
            runner.write_json(
                folder / "preflight.json",
                {
                    "profile": profile,
                    "pi_version": "fixture-1",
                    "audit_sha256": "known-audit",
                },
            )
            (folder / "stderr.txt").write_text(
                json.dumps({**profile, "type": "eval_profile"}) + "\n"
            )
            runner.write_json(
                folder / "execution.json", {"exit_code": 0, "elapsed_seconds": 1.2}
            )
            (folder / "events.jsonl").write_text(
                "\n".join(json.dumps(event) for event in completed_events()) + "\n"
            )
            runner.write_json(
                private / f"validation-example-{reader['arm']}.json",
                {"exit_code": 0, "source_sha256": reader["tree_sha256"]},
            )
            grade.update(commands=1, output_bytes=3, elapsed_seconds=2)
        self.save_grades()
        self.assertTrue(runner.score(self.workspace)[0]["harness_verified"])
        runner.write_json(private / "readers.json", self.readers[:1])
        runner.write_json(private / "grades.json", self.grades[:1])
        with self.assertRaisesRegex(ValueError, "every selected task and condition"):
            runner.score(self.workspace)
        runner.write_json(private / "readers.json", self.readers)
        self.save_grades()
        self.grades[1]["output_bytes"] = 999
        self.save_grades()
        with self.assertRaisesRegex(ValueError, "differs from collected output_bytes"):
            runner.score(self.workspace)
        self.grades[1]["output_bytes"] = 3
        self.save_grades()
        second = self.workspace / "readers/r02/pi"
        receipt = json.loads((second / "preflight.json").read_text())
        receipt["profile"]["model"] = "another-model"
        runner.write_json(second / "preflight.json", receipt)
        (second / "stderr.txt").write_text(
            json.dumps({**receipt["profile"], "type": "eval_profile"}) + "\n"
        )
        with self.assertRaisesRegex(ValueError, "Reader profiles do not match"):
            runner.score(self.workspace)
        receipt["profile"]["model"] = "gpt-6.1-sol"
        runner.write_json(second / "preflight.json", receipt)
        (second / "stderr.txt").write_text(
            json.dumps({**receipt["profile"], "type": "eval_profile"}) + "\n"
        )
        runner.write_json(
            private / "validation-example-skill.json",
            {"exit_code": 0, "source_sha256": "different-source"},
        )
        with self.assertRaisesRegex(ValueError, "tested different source"):
            runner.score(self.workspace)

    def test_search_landing_distinguishes_implementation_from_exception_comment(
        self,
    ) -> None:
        root = self.workspace / "readers/r01/repo"
        (root / "exc.py").write_text("# Signature expired\n")
        module = root / "moved_signing.py"
        module.write_text(
            "class TimestampSigner:\n    def unsign(self):\n        return 0\n"
        )
        query: runner.Query = {
            "kind": "literal",
            "value": "signature expired",
            "owner": {"symbol": "TimestampSigner.unsign"},
        }
        indirect = runner.replay(root, query)
        assert indirect["landing"] is not None
        self.assertEqual("indirect", indirect["landing"]["status"])
        self.assertFalse(indirect["landing"]["implementation_file_hit"])
        module.write_text(
            'class TimestampSigner:\n    def unsign(self):\n        """Signature expired checks."""\n        return 0\n'
        )
        direct = runner.replay(root, query)
        assert direct["landing"] is not None
        self.assertEqual("direct", direct["landing"]["status"])
        self.assertEqual(1, direct["landing"]["direct_hits"])
        self.assertEqual(1, direct["landing"]["other_hits"])
        miss = runner.replay(root, {**query, "value": "does not exist"})
        assert miss["landing"] is not None
        self.assertEqual("miss", miss["landing"]["status"])

    def test_call_oracle_survives_private_function_and_module_renames(self) -> None:
        root = self.workspace / "readers/r01/repo"
        (root / "password_derivation.py").write_text(
            'def derive_password():\n    raise ValueError("bad parameters")\n    hashlib.pbkdf2_hmac("sha256")\n'
        )
        result = runner.replay(
            root,
            {
                "kind": "literal",
                "value": "bad parameters",
                "owner": {"call": "hashlib.pbkdf2_hmac"},
            },
        )
        assert result["landing"] is not None
        self.assertEqual("direct", result["landing"]["status"])

    def test_prepare_and_freeze_keep_generic_writer_free_of_skill_and_questions(
        self,
    ) -> None:
        source = self.workspace / "source"
        source.mkdir()
        (source / "src").mkdir()
        (source / "src/behavior.py").write_text("def behavior(): return 42\n")
        subprocess.run(["git", "init", "--quiet", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(source),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
            check=True,
        )
        commit = runner.git(source, "rev-parse", "HEAD").strip()
        suite = self.workspace / "suite.json"
        runner.write_json(
            suite,
            {
                "targets": [
                    {
                        "id": "fixture",
                        "url": str(source),
                        "commit": commit,
                        "module": "src/behavior.py",
                        "tasks": [
                            {"id": "task", "question": "HELD_BACK_QUESTION"},
                            {"id": "other", "question": "OTHER_PRIVATE_QUESTION"},
                        ],
                    }
                ]
            },
        )
        skill = self.workspace / "skill.txt"
        skill.write_text("DISTINCTIVE_SKILL_RULE")
        run = self.workspace / "new-run"
        with patch.object(runner, "SUITE_PATH", suite):
            runner.prepare(run, skill, "fixture", include_generic=True)
        generic = (run / "private/writer-generic-fixture.txt").read_text()
        applied = (run / "private/writer-skill-fixture.txt").read_text()
        self.assertNotIn("DISTINCTIVE_SKILL_RULE", generic)
        self.assertIn("DISTINCTIVE_SKILL_RULE", applied)
        for prompt in (generic, applied):
            self.assertNotIn("HELD_BACK_QUESTION", prompt)
            self.assertIn("50 tool calls and 15 minutes", prompt)
        runner.make_readers(run, 0)
        assignments = json.loads((run / "private/readers.json").read_text())
        self.assertEqual(6, len(assignments))
        self.assertEqual(
            {"original", "generic", "skill"}, {row["arm"] for row in assignments}
        )
        for row in assignments:
            prompt = (run / "readers" / row["id"] / "prompt.txt").read_text()
            search_root = re.search(
                r"Search only the current repository \(([^)]+)\)", prompt
            )
            self.assertIsNotNone(search_root)
            assert search_root is not None
            found = subprocess.check_output(
                ["rg", "--files", search_root[1]],
                cwd=run / "readers" / row["id"] / "repo",
                text=True,
            )
            self.assertIn("src/behavior.py", found)
            expected = (
                "HELD_BACK_QUESTION"
                if row["task"] == "task"
                else "OTHER_PRIVATE_QUESTION"
            )
            other = (
                "OTHER_PRIVATE_QUESTION"
                if row["task"] == "task"
                else "HELD_BACK_QUESTION"
            )
            self.assertIn(expected, prompt)
            self.assertNotIn(other, prompt)
            self.assertNotIn("DISTINCTIVE_SKILL_RULE", prompt)
        grades = json.loads((run / "private/grades.json").read_text())
        self.assertTrue(all(len(grade["tasks"]) == 1 for grade in grades))

    def test_separate_questions_are_scored_without_overwriting_each_other(self) -> None:
        suite = self.workspace / "private/suite.json"
        data = json.loads(suite.read_text())
        data["targets"][0]["tasks"].append({"id": "other"})
        runner.write_json(suite, data)
        for reader in self.readers:
            reader["task"] = "behavior"
        for index, (reader, grade) in enumerate(
            zip(self.readers[:], self.grades[:]), 3
        ):
            other_id = f"r{index:02d}"
            shutil.copytree(
                self.workspace / "readers" / reader["id"],
                self.workspace / "readers" / other_id,
            )
            self.readers.append({**reader, "id": other_id, "task": "other"})
            other_grade = copy.deepcopy(grade)
            other_grade.update(
                reader=other_id,
                tasks={"other": {"correct": True, "reason": "module.py:1"}},
            )
            self.grades.append(other_grade)
        runner.write_json(self.workspace / "private/readers.json", self.readers)
        self.save_grades()
        reports = runner.score(self.workspace)
        self.assertEqual(["behavior", "other"], [row["task"] for row in reports])
        self.assertTrue(all(row["total_tasks_per_reader"] == 1 for row in reports))

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
