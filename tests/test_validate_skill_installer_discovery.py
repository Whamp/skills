from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import validate_skill_installer_discovery as runner


class ValidateSkillInstallerDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write_skill(self, directory: str, policy: str = "") -> Path:
        skill = self.root / directory
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {skill.name}\ndescription: Fixture.\n{policy}---\n",
            encoding="utf-8",
        )
        return skill

    def test_canonical_staging_and_user_only_listing(self) -> None:
        canonical = self.write_skill("engineering/example")
        (canonical / "guide.txt").write_text("Canonical content", encoding="utf-8")
        self.write_skill("personal/user-only", "disable-model-invocation: true\n")
        for location in (
            ".agents/skills/lane",
            ".pi/skills/local",
            ".ultimate/skills/verify-skills",
            "productivity/.hidden/local",
            "engineering/.hidden-skill",
            "engineering/example/.agents/skills/nested-tool",
        ):
            self.write_skill(location)
        (self.root / "skills-lock.json").write_text("{}", encoding="utf-8")
        staged_roots: list[Path] = []

        def cli(
            command: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            staged = Path(command[4])
            staged_roots.append(staged)
            self.assertEqual(["npx", "--yes", "skills@1.5.22", "add"], command[:4])
            self.assertEqual(["--full-depth", "--list"], command[5:])
            self.assertEqual(
                [
                    "engineering/example/SKILL.md",
                    "engineering/example/guide.txt",
                    "personal/user-only/SKILL.md",
                ],
                sorted(
                    str(p.relative_to(staged)) for p in staged.rglob("*") if p.is_file()
                ),
            )
            self.assertEqual(
                "Canonical content",
                (staged / "engineering/example/guide.txt").read_text(),
            )
            self.assertIn(
                "disable-model-invocation: true",
                (staged / "personal/user-only/SKILL.md").read_text(),
            )
            self.assertEqual(subprocess.STDOUT, kwargs["stderr"])
            return subprocess.CompletedProcess(
                command, 0, "│    \x1b[32mexample\x1b[0m\n│    user-only\n"
            )

        output = io.StringIO()
        with (
            patch.object(runner.subprocess, "run", side_effect=cli),
            redirect_stdout(output),
        ):
            self.assertEqual(0, runner.validate_discovery(self.root, "1.5.22"))
        self.assertIn("│    user-only", output.getvalue())
        self.assertIn("2 canonical skills listed exactly once", output.getvalue())
        self.assertEqual(1, len(staged_roots))
        self.assertFalse(staged_roots[0].exists())

    def test_zero_exit_requires_each_expected_name_exactly_once(self) -> None:
        self.write_skill("engineering/example")
        for rows, diagnostic in (
            ("│    other\n", "missing=['example']"),
            ("│    example\n│    other\n", "unexpected=['other']"),
            ("│    example\n│    example\n", "duplicates=['example']"),
        ):
            with self.subTest(diagnostic=diagnostic):
                output = io.StringIO()
                result = subprocess.CompletedProcess([], 0, rows)
                with (
                    patch.object(runner.subprocess, "run", return_value=result),
                    redirect_stdout(output),
                ):
                    self.assertEqual(1, runner.validate_discovery(self.root, "1.5.22"))
                self.assertIn(diagnostic, output.getvalue())


if __name__ == "__main__":
    unittest.main()
