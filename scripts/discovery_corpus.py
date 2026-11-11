"""Frozen corpus inputs, source fingerprints, and search-landing oracles."""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path
from typing import NotRequired, TypedDict, cast


class Query(TypedDict):
    """A search frozen before either rewrite."""

    kind: str
    value: str
    owner: NotRequired[dict[str, str]]


class Task(TypedDict):
    """A reader question and a controller-only correctness oracle."""

    id: str
    question: str
    rubric: str


class Target(TypedDict):
    """One pinned repository and bounded rewrite target."""

    id: str
    url: str
    commit: str
    module: str
    test_command: str
    queries: list[Query]
    tasks: list[Task]


class Suite(TypedDict):
    """The frozen experiment inputs."""

    targets: list[Target]
    arms: list[str]


class Reader(TypedDict):
    """Private assignment of a neutral reader name to an experiment arm."""

    id: str
    target: str
    arm: str
    tree_sha256: str


class TaskGrade(TypedDict):
    """Manual, evidence-backed judgement of all facts in a task rubric."""

    correct: bool | None
    reason: str


class Grade(TypedDict):
    """One reader's manually audited transcript measurements and task grades."""

    reader: str
    tasks: dict[str, TaskGrade]
    commands: int | None
    output_bytes: int | None
    elapsed_seconds: int | None
    preservation_passed: bool | None
    validation_log: str


class SearchLanding(TypedDict):
    """Whether a frozen query reaches the function that owns the behavior."""

    status: str
    implementation_spans: list[tuple[str, int, int]]
    direct_hits: int
    other_hits: int
    implementation_file_hit: bool


class SearchReplay(TypedDict):
    """Complete returned search output and its implementation-location oracle."""

    command: list[str]
    output: str
    lines: int
    output_bytes: int
    landing: SearchLanding | None


def write_json(path: Path, value: object) -> None:
    """Write readable experiment evidence."""
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def load_suite(run: Path) -> Suite:
    """Read the experiment's frozen suite rather than the working source."""
    inputs_path = run / "private/inputs.json"
    if inputs_path.exists():
        inputs = json.loads(inputs_path.read_text())
        if inputs.get("schema_version", 1) >= 2:
            for name in ("suite", "skill"):
                path = (
                    run / "private" / ("suite.json" if name == "suite" else "skill.txt")
                )
                if (
                    hashlib.sha256(path.read_bytes()).hexdigest()
                    != inputs[f"{name}_sha256"]
                ):
                    raise ValueError(f"Frozen {name} changed after preparation")
    return cast(Suite, json.loads((run / "private/suite.json").read_text()))


def tree_hash(root: Path) -> str:
    """Hash paths and contents, excluding Git and local test caches."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(
            part in {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
            for part in path.relative_to(root).parts
        ):
            digest.update(str(path.relative_to(root)).encode() + b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def implementation_spans(
    root: Path, owner: dict[str, str]
) -> list[tuple[str, int, int]]:
    """Resolve a frozen Python symbol or library-call oracle across module moves."""
    spans = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        try:
            module = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for name, function in _python_functions(module.body):
            symbol_match = owner.get("symbol") == name
            call_match = "call" in owner and any(
                isinstance(node, ast.Call) and ast.unparse(node.func) == owner["call"]
                for node in ast.walk(function)
            )
            if symbol_match or call_match:
                spans.append(
                    (
                        str(relative),
                        function.lineno,
                        function.end_lineno or function.lineno,
                    )
                )
    return spans


def _python_functions(
    nodes: list[ast.stmt], prefix: str = ""
) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    functions = []
    for node in nodes:
        if isinstance(node, ast.ClassDef):
            functions.extend(_python_functions(node.body, prefix + node.name + "."))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append((prefix + node.name, node))
            functions.extend(_python_functions(node.body, prefix + node.name + "."))
    return functions


def score_search_landing(root: Path, query: Query, output: str) -> SearchLanding:
    """Distinguish implementation hits from declarations, indirect leads and misses."""
    spans = implementation_spans(root, query["owner"])
    owner_files = {path for path, _, _ in spans}
    file_hit = False
    direct_hits = 0
    lines = output.splitlines()
    for line in lines:
        if query["kind"] == "glob":
            direct_hits += line in owner_files
            file_hit |= line in owner_files
        else:
            path, number, _ = line.split(":", 2)
            path = path.removeprefix("./")
            file_hit |= path in owner_files
            direct_hits += any(
                path == expected and start <= int(number) <= end
                for expected, start, end in spans
            )
    status = (
        "oracle_unresolved"
        if not spans
        else "direct"
        if direct_hits
        else "file_only"
        if file_hit
        else "indirect"
        if lines
        else "miss"
    )
    return {
        "status": status,
        "implementation_spans": spans,
        "direct_hits": direct_hits,
        "other_hits": len(lines) - direct_hits,
        "implementation_file_hit": file_hit,
    }


def replay(root: Path, query: Query) -> SearchReplay:
    """Replay a literal search or filename glob without truncating its output."""
    if query["kind"] == "literal":
        command = [
            "rg",
            "--hidden",
            "--no-ignore",
            "--glob",
            "!.git/**",
            "--glob",
            "!.venv/**",
            "--glob",
            "!__pycache__/**",
            "--glob",
            "!.pytest_cache/**",
            "--glob",
            "!.ruff_cache/**",
            "--line-number",
            "--no-heading",
            "--color",
            "never",
            "--fixed-strings",
            "--ignore-case",
            "--",
            query["value"],
            ".",
        ]
        result = subprocess.run(command, cwd=root, capture_output=True, check=False)
        if result.returncode not in (0, 1):
            raise ValueError(f"Search failed: {result.stderr.decode()}")
        output = result.stdout.decode()
    elif query["kind"] == "glob":
        command = ["filename-glob", query["value"]]
        output = "".join(
            str(path.relative_to(root)) + "\n"
            for path in sorted(root.rglob("*"))
            if path.is_file() and fnmatch.fnmatch(path.name, query["value"])
        )
    else:
        raise ValueError(f"Unknown search kind: {query['kind']}")
    return {
        "command": command,
        "output": output,
        "lines": len(output.splitlines()),
        "output_bytes": len(output.encode()),
        "landing": score_search_landing(root, query, output)
        if "owner" in query
        else None,
    }
