#!/usr/bin/env python3
"""Assert complete installer discovery from a canonical-only temporary source."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

CATEGORIES = ("engineering", "productivity", "personal")
ANSI_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
# Pinned skills CLI's ungrouped name rows; fail closed if its format changes.
NAME_PATTERN = re.compile(r"^│    ([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)


def validate_discovery(repository_root: Path, version: str) -> int:
    skills = sorted(
        manifest.parent
        for category in CATEGORIES
        for manifest in (repository_root / category).glob("*/SKILL.md")
        if not manifest.parent.name.startswith(".")
    )
    expected = Counter(skill.name for skill in skills)
    duplicate_expected = sorted(name for name, count in expected.items() if count > 1)
    if not expected or duplicate_expected:
        print(
            f"Invalid canonical catalog: empty={not expected}; duplicate names={duplicate_expected}"
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="skill-installer-discovery-") as temporary:
        staging_root = Path(temporary)
        for skill in skills:
            shutil.copytree(
                skill,
                staging_root / skill.relative_to(repository_root),
                ignore=shutil.ignore_patterns(".*", "node_modules"),
            )
        result = subprocess.run(
            [
                "npx",
                "--yes",
                f"skills@{version}",
                "add",
                str(staging_root),
                "--full-depth",
                "--list",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        print(result.stdout, end="")
        if result.returncode:
            print(f"Installer discovery CLI failed with exit code {result.returncode}.")
            return 1

        actual = Counter(NAME_PATTERN.findall(ANSI_PATTERN.sub("", result.stdout)))
        missing = sorted(expected.keys() - actual.keys())
        unexpected = sorted(actual.keys() - expected.keys())
        duplicates = sorted(name for name, count in actual.items() if count > 1)
        print(f"missing={missing}; unexpected={unexpected}; duplicates={duplicates}")
        if not actual:
            print(
                "No installer skill-name rows extracted; check the pinned CLI format."
            )
        if not actual or missing or unexpected or duplicates:
            return 1
    print(
        f"Installer discovery passed: {len(expected)} canonical skills listed exactly once."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skills_cli_version")
    arguments = parser.parse_args()
    try:
        return validate_discovery(
            Path(__file__).resolve().parents[1], arguments.skills_cli_version
        )
    except OSError as error:
        print(f"Installer discovery failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
