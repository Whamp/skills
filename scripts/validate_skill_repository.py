#!/usr/bin/env python3
"""Validate portable skill manifests and their local Markdown reference graph."""

from __future__ import annotations

import argparse
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

FRONTMATTER_BOUNDARY = "---"
FRONTMATTER_FIELD_PATTERN = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
IGNORED_DIRECTORY_NAMES = {"node_modules"}


@dataclass(frozen=True, order=True)
class SkillRepositoryProblem:
    """One deterministic validation failure tied to a repository-relative path."""

    path: str
    message: str


def collect_skill_repository_problems(
    repository_root: Path,
) -> list[SkillRepositoryProblem]:
    """Return every manifest, naming, link, and reference-reachability problem."""

    repository_root = repository_root.resolve()
    manifests = sorted(
        path
        for path in repository_root.rglob("SKILL.md")
        if not _is_ignored_repository_path(path.relative_to(repository_root))
    )
    problems: list[SkillRepositoryProblem] = []
    if not manifests:
        return [SkillRepositoryProblem(".", "no SKILL.md manifests found")]

    manifests_by_name: dict[str, list[Path]] = {}
    for manifest in manifests:
        frontmatter, frontmatter_problems = _read_skill_frontmatter(
            manifest, repository_root
        )
        problems.extend(frontmatter_problems)

        skill_name = frontmatter.get("name", "").strip("'\"")
        if skill_name:
            manifests_by_name.setdefault(skill_name, []).append(manifest)
            if skill_name != manifest.parent.name:
                problems.append(
                    _problem(
                        repository_root,
                        manifest,
                        f"skill name {skill_name!r} does not match directory name {manifest.parent.name!r}",
                    )
                )

        problems.extend(_validate_skill_markdown(manifest.parent, repository_root))

    for skill_name, named_manifests in sorted(manifests_by_name.items()):
        if len(named_manifests) < 2:
            continue
        locations = ", ".join(
            str(path.relative_to(repository_root)) for path in named_manifests
        )
        for manifest in named_manifests:
            problems.append(
                _problem(
                    repository_root,
                    manifest,
                    f"duplicate skill name {skill_name!r}: {locations}",
                )
            )

    return sorted(set(problems))


def _read_skill_frontmatter(
    manifest: Path, repository_root: Path
) -> tuple[dict[str, str], list[SkillRepositoryProblem]]:
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != FRONTMATTER_BOUNDARY:
        return {}, [
            _problem(repository_root, manifest, "missing opening frontmatter boundary")
        ]

    try:
        closing_boundary = lines.index(FRONTMATTER_BOUNDARY, 1)
    except ValueError:
        return {}, [
            _problem(repository_root, manifest, "missing closing frontmatter boundary")
        ]

    fields: dict[str, str] = {}
    for line in lines[1:closing_boundary]:
        match = FRONTMATTER_FIELD_PATTERN.match(line)
        if match:
            fields[match.group(1)] = (match.group(2) or "").strip()

    problems: list[SkillRepositoryProblem] = []
    if not fields.get("name"):
        problems.append(
            _problem(repository_root, manifest, "frontmatter requires a name")
        )
    if not fields.get("description"):
        problems.append(
            _problem(
                repository_root,
                manifest,
                "frontmatter requires a non-empty description",
            )
        )
    return fields, problems


def _validate_skill_markdown(
    skill_directory: Path, repository_root: Path
) -> list[SkillRepositoryProblem]:
    markdown_files = sorted(skill_directory.rglob("*.md"))
    markdown_file_set = {path.resolve() for path in markdown_files}
    markdown_edges: dict[Path, set[Path]] = {
        path.resolve(): set() for path in markdown_files
    }
    problems: list[SkillRepositoryProblem] = []

    for markdown_file in markdown_files:
        for raw_target in MARKDOWN_LINK_PATTERN.findall(
            markdown_file.read_text(encoding="utf-8")
        ):
            target = _resolve_local_link(markdown_file, raw_target)
            if target is None:
                continue
            try:
                target.relative_to(repository_root)
            except ValueError:
                problems.append(
                    _problem(
                        repository_root,
                        markdown_file,
                        f"local link escapes the repository: {raw_target}",
                    )
                )
                continue
            try:
                target.relative_to(skill_directory.resolve())
            except ValueError:
                problems.append(
                    _problem(
                        repository_root,
                        markdown_file,
                        f"local link escapes the skill directory: {raw_target}",
                    )
                )
                continue
            if not target.exists():
                problems.append(
                    _problem(
                        repository_root,
                        markdown_file,
                        f"missing local link target: {raw_target}",
                    )
                )
                continue
            if target in markdown_file_set:
                markdown_edges[markdown_file.resolve()].add(target)

    reachable = _reachable_markdown_files(
        (skill_directory / "SKILL.md").resolve(), markdown_edges
    )
    for orphan in sorted(markdown_file_set - reachable):
        problems.append(
            _problem(
                repository_root,
                orphan,
                "Markdown reference is unreachable from SKILL.md",
            )
        )
    return problems


def _resolve_local_link(source_file: Path, raw_target: str) -> Path | None:
    target_text = raw_target.strip()
    if target_text.startswith("<") and target_text.endswith(">"):
        target_text = target_text[1:-1]
    parsed = urlsplit(target_text)
    if parsed.scheme or parsed.netloc or target_text.startswith(("#", "mailto:")):
        return None
    decoded_path = unquote(parsed.path)
    if not decoded_path:
        return None
    return (source_file.parent / decoded_path).resolve()


def _reachable_markdown_files(
    root_manifest: Path, markdown_edges: dict[Path, set[Path]]
) -> set[Path]:
    reachable: set[Path] = set()
    queue = deque([root_manifest])
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        queue.extend(markdown_edges.get(current, set()) - reachable)
    return reachable


def _is_ignored_repository_path(relative_path: Path) -> bool:
    return any(
        part.startswith(".") or part in IGNORED_DIRECTORY_NAMES
        for part in relative_path.parts[:-1]
    )


def _problem(repository_root: Path, path: Path, message: str) -> SkillRepositoryProblem:
    return SkillRepositoryProblem(str(path.relative_to(repository_root)), message)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate skill manifests and local Markdown references."
    )
    parser.add_argument(
        "repository_root",
        nargs="?",
        type=Path,
        default=Path(__file__).parents[1],
    )
    arguments = parser.parse_args()

    problems = collect_skill_repository_problems(arguments.repository_root)
    for problem in problems:
        print(f"{problem.path}: {problem.message}")
    if problems:
        print(f"Skill repository validation found {len(problems)} problem(s).")
        return 1
    print("Skill repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
