from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_skill_repository import collect_skill_repository_problems


class ValidateSkillRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository_root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_skill(
        self,
        relative_directory: str,
        *,
        name: str | None = None,
        body: str = "# Test skill\n",
    ) -> Path:
        skill_directory = self.repository_root / relative_directory
        skill_directory.mkdir(parents=True)
        skill_name = name or skill_directory.name
        manifest = skill_directory / "SKILL.md"
        manifest.write_text(
            f"---\nname: {skill_name}\ndescription: Test fixture skill.\n---\n\n{body}",
            encoding="utf-8",
        )
        return skill_directory

    def test_valid_skill_repository_has_no_problems(self) -> None:
        skill_directory = self.write_skill(
            "engineering/example-skill",
            body="# Example\n\nRead [the guide](references/guide.md).\n",
        )
        references = skill_directory / "references"
        references.mkdir()
        (references / "guide.md").write_text("# Guide\n", encoding="utf-8")

        self.assertEqual([], collect_skill_repository_problems(self.repository_root))

    def test_manifest_requires_frontmatter_name_and_description(self) -> None:
        skill_directory = self.repository_root / "engineering" / "broken-skill"
        skill_directory.mkdir(parents=True)
        (skill_directory / "SKILL.md").write_text(
            "# Missing frontmatter\n", encoding="utf-8"
        )

        problems = collect_skill_repository_problems(self.repository_root)

        self.assertTrue(any("frontmatter" in problem.message for problem in problems))

    def test_manifest_rejects_empty_description(self) -> None:
        skill_directory = self.write_skill("engineering/empty-description")
        (skill_directory / "SKILL.md").write_text(
            "---\nname: empty-description\ndescription:\n---\n",
            encoding="utf-8",
        )

        problems = collect_skill_repository_problems(self.repository_root)

        self.assertTrue(any("description" in problem.message for problem in problems))

    def test_skill_name_matches_directory_and_is_unique(self) -> None:
        self.write_skill("engineering/first-copy", name="shared-name")
        self.write_skill("productivity/shared-name", name="shared-name")

        problems = collect_skill_repository_problems(self.repository_root)
        messages = [problem.message for problem in problems]

        self.assertTrue(any("directory name" in message for message in messages))
        self.assertTrue(any("duplicate skill name" in message for message in messages))

    def test_broken_local_markdown_link_is_reported(self) -> None:
        self.write_skill(
            "engineering/broken-link",
            body="# Broken link\n\nRead [the missing guide](references/missing.md).\n",
        )

        problems = collect_skill_repository_problems(self.repository_root)

        self.assertTrue(
            any("missing local link target" in problem.message for problem in problems)
        )

    def test_local_markdown_link_cannot_escape_skill_directory(self) -> None:
        self.write_skill(
            "engineering/nonportable-link",
            body="# Nonportable link\n\nRead [shared notes](../../shared.md).\n",
        )
        (self.repository_root / "shared.md").write_text("# Shared\n", encoding="utf-8")

        problems = collect_skill_repository_problems(self.repository_root)

        self.assertTrue(
            any(
                "escapes the skill directory" in problem.message for problem in problems
            )
        )

    def test_unreachable_markdown_reference_is_reported(self) -> None:
        skill_directory = self.write_skill("engineering/orphaned-reference")
        references = skill_directory / "references"
        references.mkdir()
        (references / "orphan.md").write_text("# Orphan\n", encoding="utf-8")

        problems = collect_skill_repository_problems(self.repository_root)

        self.assertTrue(
            any("unreachable from SKILL.md" in problem.message for problem in problems)
        )


if __name__ == "__main__":
    unittest.main()
