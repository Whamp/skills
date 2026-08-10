#!/usr/bin/env python3
"""Capture every Herdr CLI help path without running mutating commands."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path

TOP_LEVEL_COMMANDS = (
    "status",
    "update",
    "completion",
    "server",
    "api",
    "config",
    "channel",
    "workspace",
    "worktree",
    "tab",
    "notification",
    "agent",
    "pane",
    "session",
    "integration",
    "terminal",
)
SUBCOMMAND_PATTERN = re.compile(r"^  ([a-z0-9][a-z0-9-]*)\s{2,}")
ROOT_COMMAND_PATTERN = re.compile(r"^\s+herdr ([a-z0-9][a-z0-9-]*)(?:\s|$)")


def parse_subcommands(help_text: str) -> list[str]:
    """Return subcommands from one clap-style Commands section."""
    lines = help_text.splitlines()
    try:
        start = lines.index("Commands:") + 1
    except ValueError:
        return []

    subcommands: list[str] = []
    for line in lines[start:]:
        if not line.strip():
            if subcommands:
                break
            continue
        match = SUBCOMMAND_PATTERN.match(line)
        if match:
            subcommands.append(match.group(1))
        elif subcommands and not line.startswith(" "):
            break
    return subcommands


def capture_help(binary: str, command_path: tuple[str, ...]) -> dict[str, object]:
    """Capture one command path by appending --help, which cannot mutate state."""
    argv = [binary, *command_path, "--help"]
    result = subprocess.run(argv, check=False, capture_output=True, text=True)
    return {
        "path": " ".join(command_path) if command_path else "<root>",
        "argv": argv,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", default="herdr", help="Herdr binary or path")
    parser.add_argument("--output", type=Path, required=True, help="JSON evidence path")
    args = parser.parse_args()

    binary = shutil.which(args.binary)
    if binary is None:
        parser.error(f"Herdr binary not found: {args.binary}")

    version = subprocess.run(
        [binary, "--version"], check=False, capture_output=True, text=True
    )
    queue: deque[tuple[str, ...]] = deque()
    queue.append(())
    queue.extend((command,) for command in TOP_LEVEL_COMMANDS)
    seen: set[tuple[str, ...]] = set()
    records: list[dict[str, object]] = []

    while queue:
        command_path = queue.popleft()
        if command_path in seen:
            continue
        seen.add(command_path)

        record = capture_help(binary, command_path)
        records.append(record)
        if record["exit_code"] != 0:
            continue

        help_text = f"{record['stdout']}{record['stderr']}"
        if not command_path:
            for line in help_text.splitlines():
                match = ROOT_COMMAND_PATTERN.match(line)
                if match:
                    queue.append((match.group(1),))
        for subcommand in parse_subcommands(help_text):
            queue.append((*command_path, subcommand))

    failures = [record["path"] for record in records if record["exit_code"] != 0]
    evidence = {
        "binary": binary,
        "version": version.stdout.strip(),
        "version_exit_code": version.returncode,
        "command_count": len(records),
        "failures": failures,
        "commands": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")

    if version.returncode != 0 or failures:
        print(
            f"Herdr help capture incomplete: version_exit={version.returncode}, "
            f"failed_paths={len(failures)}; evidence={args.output}",
            file=sys.stderr,
        )
        return 1

    print(f"Captured {len(records)} Herdr help paths in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
