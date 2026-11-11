"""Check clean-profile rejection, model-visible output, and process receipts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import discovery_pi as harness


def profile_fixture(repo: Path) -> dict[str, object]:
    """A known clean effective profile, independent of the real Pi loader."""
    return {
        "systemPrompt": "effective prompt",
        "tools": ["bash"],
        "provider": "openai",
        "model": "gpt-6.1-sol",
        "thinking": "medium",
        "messageCount": 0,
        "options": {
            "customPrompt": harness.SYSTEM_PROMPT,
            "selectedTools": ["bash"],
            "contextFiles": [],
            "skills": [],
            "appendSystemPrompt": "",
            "sections": {},
            "cwd": str(repo),
        },
    }


def completed_events() -> list[dict[str, object]]:
    """A full-output update followed by a smaller result actually sent to the model."""
    return [
        {
            "type": "tool_execution_start",
            "toolCallId": "call1",
            "toolName": "bash",
            "args": {"command": "cat log.txt"},
        },
        {
            "type": "tool_execution_update",
            "toolCallId": "call1",
            "partialResult": {
                "content": [
                    {"type": "text", "text": "uncapped text that must not be counted"}
                ]
            },
        },
        {
            "type": "tool_execution_end",
            "toolCallId": "call1",
            "result": {
                "content": [{"type": "text", "text": "another full output copy"}]
            },
        },
        {
            "type": "message_end",
            "message": {
                "role": "toolResult",
                "toolCallId": "call1",
                "toolName": "bash",
                "content": [{"type": "text", "text": "é\n"}],
                "details": {"fullOutput": "private full output"},
            },
        },
        {
            "type": "message_end",
            "message": {
                "role": "assistant",
                "stopReason": "stop",
                "content": [{"type": "text", "text": "Answer: log.txt:1"}],
                "usage": {"input": 10, "output": 4, "cacheRead": 3, "cacheWrite": 0},
            },
        },
        {"type": "agent_settled", "aborted": False},
    ]


class PiCollectorTests(unittest.TestCase):
    """Use final messages as the metric oracle, never streaming or execution copies."""

    def test_truncated_output_is_counted_once_in_utf8(self) -> None:
        report = harness.collect_pi_events(completed_events())
        self.assertEqual(1, report["commands"])
        self.assertEqual(3, report["output_bytes"])
        self.assertEqual("Answer: log.txt:1", report["answer"])
        self.assertEqual(
            {"input": 10, "output": 4, "cacheRead": 3, "cacheWrite": 0}, report["usage"]
        )

    def test_audit_extension_blocks_calls_after_budget(self) -> None:
        program = (
            "import assert from 'node:assert/strict';\n"
            f"import registerAudit from {json.dumps(harness.AUDIT_EXTENSION.as_uri())};\n"
            "const hooks = {};\n"
            "registerAudit({ registerCommand() {}, on(name, callback) { hooks[name] = callback; } });\n"
            "process.env.DISCOVERY_MAX_CALLS = '1';\n"
            "assert.equal(hooks.tool_call(), undefined);\n"
            "assert.equal(hooks.tool_call().block, true);\n"
        )
        subprocess.run(["node", "--input-type=module", "-e", program], check=True)

    def test_incomplete_aborted_duplicate_and_extra_tools_are_rejected(self) -> None:
        incomplete = completed_events()[:-1]
        aborted = completed_events()
        aborted[-1]["aborted"] = True
        duplicate = completed_events()
        duplicate.insert(4, duplicate[3])
        extra_tool = completed_events()
        extra_tool[0]["toolName"] = "read"
        for events in (incomplete, aborted, duplicate, extra_tool):
            with self.subTest(events=events), self.assertRaises(ValueError):
                harness.collect_pi_events(events)

    def test_jsonl_keeps_unicode_line_separators_inside_strings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text('{"type":"example","text":"a\u2028b"}\n')
            self.assertEqual("a\u2028b", harness.read_events(path)[0]["text"])

    def test_clean_profile_rejects_each_ambient_input(self) -> None:
        repo = Path("/benchmark/repo")
        config = harness.PiConfig("openai", "gpt-6.1-sol")
        harness.validate_profile(profile_fixture(repo), repo, config)
        for field, value in (
            ("contextFiles", [{"path": "AGENTS.md", "content": "ambient"}]),
            ("skills", [{"name": "write-discoverable-code"}]),
            ("appendSystemPrompt", "global memory instructions"),
            ("sections", {"extra": "unrelated instructions"}),
            ("selectedTools", ["bash", "read"]),
        ):
            profile = profile_fixture(repo)
            harness.object_value(profile["options"])[field] = value
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "ambient"),
            ):
                harness.validate_profile(profile, repo, config)
        for field, value in (
            ("messageCount", 1),
            ("model", "different-model"),
            ("tools", ["bash", "mcp__search"]),
        ):
            profile = profile_fixture(repo)
            profile[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                harness.validate_profile(profile, repo, config)

    def test_collector_rejects_runtime_profile_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            harness.write_json(
                folder / "execution.json", {"exit_code": 0, "elapsed_seconds": 1.1}
            )
            harness.write_json(
                folder / "preflight.json", {"profile": profile_fixture(folder)}
            )
            actual = {
                **profile_fixture(folder),
                "type": "eval_profile",
                "tools": ["bash", "read"],
            }
            (folder / "stderr.txt").write_text(json.dumps(actual) + "\n")
            with self.assertRaisesRegex(ValueError, "Runtime profile differs"):
                harness.collect(folder)


@unittest.skipUnless(
    shutil.which("bwrap"), "Linux bubblewrap is required for the filesystem integration"
)
class PiProcessTests(unittest.TestCase):
    """Exercise the public CLI, actual subprocesses and the real filesystem boundary."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "answer.py").write_text("answer = 42\n")

    def test_shell_cannot_modify_repository_or_read_sibling(self) -> None:
        folder = self.root / "pi"
        folder.mkdir()
        harness.prepare_profile(folder, self.repo, writable=False)
        sibling = self.root / "hidden.txt"
        sibling.write_text("held-back answer")
        command = [str(folder / "profile/benchmark-shell"), "-c"]
        result = subprocess.run(
            [*command, "cat answer.py"], capture_output=True, text=True, check=True
        )
        self.assertEqual("answer = 42\n", result.stdout)
        for script in (f"cat {sibling}", "echo wrong > answer.py"):
            result = subprocess.run(
                [*command, script], capture_output=True, text=True, check=False
            )
            self.assertNotEqual(0, result.returncode)
        self.assertEqual("answer = 42\n", (self.repo / "answer.py").read_text())

    def test_cli_preflights_runs_collects_and_preserves_raw_events(self) -> None:
        executable = self.root / "fake-pi"
        executable.write_text(
            "#!" + sys.executable + "\n"
            "import json, os, sys\n"
            "if '--version' in sys.argv:\n"
            " print('fixture-pi 1'); sys.exit(0)\n"
            "system = sys.argv[sys.argv.index('--system-prompt')+1]\n"
            "profile = {'type':'eval_profile','systemPrompt':system,'tools':['bash'],'provider':'openai','model':'gpt-6.1-sol','thinking':'medium'}\n"
            "if sys.argv[-1] == '/eval-profile':\n"
            " profile.update(messageCount=0,options={'customPrompt':system,'selectedTools':['bash'],'contextFiles':[],'skills':[],'appendSystemPrompt':'','sections':{},'cwd':os.getcwd()})\n"
            " print(json.dumps(profile),file=sys.stderr); sys.exit(0)\n"
            "sys.stdin.read()\n"
            "print(json.dumps(profile),file=sys.stderr)\n"
            + f"events = json.loads({json.dumps(json.dumps(completed_events()))})\n"
            "for event in events: print(json.dumps(event))\n"
        )
        executable.chmod(0o700)
        run = self.root / "run"
        reader = run / "readers/r01"
        reader.mkdir(parents=True)
        shutil.copytree(self.repo, reader / "repo")
        (reader / "prompt.txt").write_text("Find the answer.\n")
        (run / "private").mkdir()
        harness.write_json(run / "private/grades.json", [{"reader": "r01"}])
        script = Path(__file__).parents[1] / "scripts/eval_discoverable_code.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "run-readers",
                str(run),
                "--provider",
                "openai",
                "--model",
                "gpt-6.1-sol",
                "--pi",
                str(executable),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn('"output_bytes": 3', result.stdout)
        self.assertEqual("Answer: log.txt:1", (reader / "answer.txt").read_text())
        grade = json.loads((run / "private/grades.json").read_text())[0]
        self.assertEqual(1, grade["commands"])
        self.assertEqual(3, grade["output_bytes"])
        self.assertNotIn(
            "tasks", grade
        )  # Collection must not fabricate semantic grades.
        receipt = json.loads((reader / "pi/preflight.json").read_text())
        for flag in ("-ne", "-ns", "-np", "-nc", "--no-mcp"):
            self.assertIn(flag, receipt["argv"])
        self.assertTrue((reader / "pi/events.jsonl").is_file())
        self.assertTrue((reader / "pi/execution.json").is_file())


if __name__ == "__main__":
    unittest.main()
