"""Validate experiment evidence and compare correct, preserved benchmark conditions."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING or __package__:
    from scripts import discovery_pi
    from scripts.discovery_corpus import (
        Grade,
        Reader,
        load_suite,
        tree_hash,
        write_json,
    )
else:
    import discovery_pi
    from discovery_corpus import Grade, Reader, load_suite, tree_hash, write_json


def score(run: Path) -> list[dict[str, object]]:
    """Reject incomplete evidence and compare correct, preserved benchmark conditions."""
    readers = cast(list[Reader], json.loads((run / "private/readers.json").read_text()))
    grades = cast(list[Grade], json.loads((run / "private/grades.json").read_text()))
    if len({row["reader"] for row in grades}) != len(grades) or {
        row["reader"] for row in grades
    } != {reader["id"] for reader in readers}:
        raise ValueError("Grades must contain every reader exactly once")
    by_reader = {row["reader"]: row for row in grades}
    pairs: dict[tuple[str, str | None], dict[str, Grade]] = {}
    protocol: tuple[object, ...] | None = None
    targets = {target["id"]: target for target in load_suite(run)["targets"]}
    inputs_path = run / "private/inputs.json"
    inputs = json.loads(inputs_path.read_text()) if inputs_path.exists() else {}
    requires_pi = inputs.get("schema_version", 1) >= 2
    if inputs.get("schema_version", 1) >= 3:
        expected = {
            (target["id"], task["id"], arm)
            for target in targets.values()
            for task in target["tasks"]
            for arm in load_suite(run)["arms"]
        }
        actual = {
            (reader["target"], reader.get("task"), reader["arm"]) for reader in readers
        }
        if actual != expected or len(actual) != len(readers):
            raise ValueError(
                "Readers must cover every selected task and condition exactly once"
            )
    for reader in readers:
        grade = by_reader[reader["id"]]
        expected_tasks = {task["id"] for task in targets[reader["target"]]["tasks"]}
        if "task" in reader:
            if reader["task"] not in expected_tasks:
                raise ValueError(f"Unknown task: {reader['task']}")
            expected_tasks = {reader["task"]}
        fingerprint = _verify_reader(run, reader, grade, expected_tasks, requires_pi)
        if fingerprint is not None:
            if protocol is not None and fingerprint != protocol:
                raise ValueError("Reader profiles do not match across conditions")
            protocol = fingerprint
        pairs.setdefault((reader["target"], reader.get("task")), {})[reader["arm"]] = (
            grade
        )
    reports = []
    for (target_id, task_id), pair in sorted(pairs.items()):
        report = _compare_conditions(
            target_id,
            pair,
            1 if task_id else len(targets[target_id]["tasks"]),
            requires_pi,
        )
        if task_id is not None:
            report["task"] = task_id
        reports.append(report)
    return reports


def _verify_reader(
    run: Path, reader: Reader, grade: Grade, expected_tasks: set[str], requires_pi: bool
) -> tuple[object, ...] | None:
    """Check one reader's immutable source, raw metrics, profile, tests and grades."""
    fingerprint = None
    folder = run / "readers" / reader["id"]
    if tree_hash(folder / "repo") != reader["tree_sha256"]:
        raise ValueError(f"Reader source changed: {reader['id']}")
    for evidence in (folder / "answer.txt", folder / "transcript.txt"):
        if not evidence.is_file() or not evidence.read_text().strip():
            raise ValueError(f"Missing evidence: {evidence}")
    if requires_pi:
        metrics = discovery_pi.collect(folder / "pi")
        verified = json.loads((folder / "pi/preflight.json").read_text())
        profile = verified["profile"]
        fingerprint = (
            profile["provider"],
            profile["model"],
            profile["thinking"],
            profile["tools"],
            verified["pi_version"],
            verified["audit_sha256"],
        )
        for key in ("commands", "output_bytes", "elapsed_seconds"):
            if grade[key] != metrics[key]:
                raise ValueError(f"Grade differs from collected {key}: {reader['id']}")
        receipt_path = (
            run / "private" / f"validation-{reader['target']}-{reader['arm']}.json"
        )
        receipt = json.loads(receipt_path.read_text())
        if (
            receipt["exit_code"] != 0
            or receipt["source_sha256"] != reader["tree_sha256"]
        ):
            raise ValueError(
                f"Validation failed or tested different source: {reader['id']}"
            )
    if set(grade["tasks"]) != expected_tasks or any(
        type(item["correct"]) is not bool or not item["reason"].strip()
        for item in grade["tasks"].values()
    ):
        raise ValueError(f"Incomplete task grades: {reader['id']}")
    for metric in ("commands", "output_bytes", "elapsed_seconds"):
        value = grade[metric]
        if type(value) is not int or value < 0:
            raise ValueError(f"Missing or invalid {metric}: {reader['id']}")
    log = run / grade["validation_log"]
    if (
        type(grade["preservation_passed"]) is not bool
        or not log.is_file()
        or not log.read_text().strip()
    ):
        raise ValueError(f"Missing preservation evidence: {reader['id']}")
    return fingerprint


def _compare_conditions(
    target_id: str, pair: dict[str, Grade], total_tasks: int, requires_pi: bool
) -> dict[str, object]:
    """Compare effort only after every condition passes the same acceptance gates."""
    counts = {
        arm: sum(item["correct"] is True for item in grade["tasks"].values())
        for arm, grade in pair.items()
    }
    budget_compliant = {
        arm: isinstance(grade["commands"], int)
        and grade["commands"] <= 12
        and isinstance(grade["elapsed_seconds"], int)
        and grade["elapsed_seconds"] <= 600
        for arm, grade in pair.items()
    }
    eligible = all(
        budget_compliant[arm]
        and grade["preservation_passed"] is True
        and counts[arm] == len(grade["tasks"])
        for arm, grade in pair.items()
    )
    row: dict[str, object] = {
        "target": target_id,
        "correct_tasks": counts,
        "total_tasks_per_reader": total_tasks,
        "preservation_passed": {
            arm: grade["preservation_passed"] for arm, grade in pair.items()
        },
        "budget_compliant": budget_compliant,
        "effort_comparison_eligible": eligible,
        "harness_verified": requires_pi,
    }
    for metric in ("commands", "output_bytes", "elapsed_seconds"):
        before, after = pair["original"][metric], pair["skill"][metric]
        if isinstance(before, int) and isinstance(after, int):
            row[metric] = {arm: grade[metric] for arm, grade in pair.items()}
            row[f"{metric}_saved"] = before - after if eligible else None
            if "generic" in pair:
                generic = pair["generic"][metric]
                if isinstance(generic, int):
                    row[f"{metric}_saved_vs_generic"] = (
                        generic - after if eligible else None
                    )
    return row


def validate_rewrites(run: Path) -> list[dict[str, object]]:
    """Save existing-test exit codes bound to the source later given to readers."""
    suite = load_suite(run)
    receipts: list[dict[str, object]] = []
    for target in suite["targets"]:
        for arm in suite.get("arms", ["original", "skill"]):
            repo = run / "private" / arm / target["id"]
            log = run / "private" / f"validation-{target['id']}-{arm}.txt"
            before = tree_hash(repo)
            argv = shlex.split(target["test_command"])
            with log.open("w") as output:
                output.write(target["test_command"] + "\n")
                output.flush()
                result = subprocess.run(
                    argv, cwd=repo, stdout=output, stderr=subprocess.STDOUT, check=False
                )
            after = tree_hash(repo)
            if before != after:
                raise ValueError(f"Validation changed benchmark source: {repo}")
            receipt: dict[str, object] = {
                "target": target["id"],
                "arm": arm,
                "argv": argv,
                "cwd": str(repo),
                "exit_code": result.returncode,
                "source_sha256": after,
                "log": str(log.relative_to(run)),
            }
            write_json(log.with_suffix(".json"), receipt)
            receipts.append(receipt)
    if any(row["exit_code"] != 0 for row in receipts):
        raise ValueError(
            "Benchmark preservation tests failed; inspect validation receipts"
        )
    return receipts
