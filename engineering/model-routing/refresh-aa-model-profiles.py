#!/usr/bin/env python3
"""Refresh the Artificial Analysis model-profile snapshot used by model-routing."""

import argparse
import csv
import json
import math
import os
import tempfile
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

API_URL = "https://artificialanalysis.ai/api/v2/language/models/free"
FIELDS = [
    "Provider",
    "Model",
    "Model ID",
    "Effort",
    "Effective Effort",
    "Access Pool",
    "Cost Per Task",
    "Intelligence Index",
    "Model Coding Index",
    "Agentic Index",
    "Benchmark Status",
    "Index Version",
    "As Of",
    "Source",
]
BENCHMARK_PROFILES = [
    (
        "gpt-5-6-luna-low",
        "OpenAI",
        "GPT-5.6 Luna",
        "openai-codex/gpt-5.6-luna:low",
        "low",
        "low",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-luna-medium",
        "OpenAI",
        "GPT-5.6 Luna",
        "openai-codex/gpt-5.6-luna:medium",
        "medium",
        "medium",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-luna-high",
        "OpenAI",
        "GPT-5.6 Luna",
        "openai-codex/gpt-5.6-luna:high",
        "high",
        "high",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-luna-xhigh",
        "OpenAI",
        "GPT-5.6 Luna",
        "openai-codex/gpt-5.6-luna:xhigh",
        "xhigh",
        "xhigh",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-luna",
        "OpenAI",
        "GPT-5.6 Luna",
        "openai-codex/gpt-5.6-luna:max",
        "max",
        "max",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-sol-low",
        "OpenAI",
        "GPT-5.6 Sol",
        "openai-codex/gpt-5.6-sol:low",
        "low",
        "low",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-sol-medium",
        "OpenAI",
        "GPT-5.6 Sol",
        "openai-codex/gpt-5.6-sol:medium",
        "medium",
        "medium",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-sol-high",
        "OpenAI",
        "GPT-5.6 Sol",
        "openai-codex/gpt-5.6-sol:high",
        "high",
        "high",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-sol-xhigh",
        "OpenAI",
        "GPT-5.6 Sol",
        "openai-codex/gpt-5.6-sol:xhigh",
        "xhigh",
        "xhigh",
        "OpenAI subscription",
    ),
    (
        "gpt-5-6-sol",
        "OpenAI",
        "GPT-5.6 Sol",
        "openai-codex/gpt-5.6-sol:max",
        "max",
        "max",
        "OpenAI subscription",
    ),
]

PENDING_PROFILES = [
    {
        "Provider": "Z.ai",
        "Model": "GLM-5.3",
        "Model ID": "zai/glm-5.3:max",
        "Effort": "max",
        "Effective Effort": "max",
        "Access Pool": "Z.ai Pro subscription",
        "Source": "local: pi --list-models zai",
    },
    {
        "Provider": "Cursor",
        "Model": "Grok 4.6",
        "Model ID": "cursor-grok-4.6-xhigh",
        "Effort": "xhigh",
        "Effective Effort": "xhigh",
        "Access Pool": "Cursor subscription via agent CLI",
        "Source": "local: agent --list-models",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-json", type=Path, help="Use a saved API response instead of fetching"
    )
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).with_name("MODEL-PROFILES.csv")
    )
    parser.add_argument("--as-of", default=datetime.now(UTC).date().isoformat())
    return parser.parse_args()


def validate_as_of(as_of: str) -> str:
    try:
        parsed = date.fromisoformat(as_of)
    except ValueError:
        raise SystemExit("invalid --as-of date: expected YYYY-MM-DD") from None
    if parsed.isoformat() != as_of:
        raise SystemExit("invalid --as-of date: expected YYYY-MM-DD")
    return as_of


def fetch_payloads() -> list[dict[str, Any]]:
    api_key = os.environ.get("ARTIFICIAL_ANALYSIS_KEY")
    if not api_key:
        raise SystemExit("ARTIFICIAL_ANALYSIS_KEY is required")

    payloads = []
    page = 1
    while True:
        request = urllib.request.Request(
            f"{API_URL}?page={page}", headers={"x-api-key": api_key}
        )
        with urllib.request.urlopen(request) as response:
            payload = json.load(response)
        payloads.append(payload)
        if not payload.get("pagination", {}).get("has_more", False):
            return payloads
        page += 1


def load_payloads(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return fetch_payloads()
    with path.open() as input_file:
        payload = json.load(input_file)
    return payload if isinstance(payload, list) else [payload]


def value(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def require_number(candidate: Any, field: str, slug: str) -> int | float:
    if (
        isinstance(candidate, bool)
        or not isinstance(candidate, (int, float))
        or not math.isfinite(candidate)
    ):
        raise SystemExit(f"invalid {field} for {slug}: expected a finite number")
    return candidate


def make_rows(payloads: list[dict[str, Any]], as_of: str) -> list[dict[str, Any]]:
    models = {
        model["slug"]: model
        for payload in payloads
        for model in payload.get("data", [])
    }
    missing_slugs = [slug for slug, *_ in BENCHMARK_PROFILES if slug not in models]
    if missing_slugs:
        raise SystemExit("missing required model profiles: " + ", ".join(missing_slugs))

    versions = [payload.get("intelligence_index_version") for payload in payloads]
    if not versions or any(
        isinstance(version, bool)
        or not isinstance(version, (str, int, float))
        or not str(version)
        for version in versions
    ):
        raise SystemExit("missing or inconsistent intelligence index versions")
    normalized_versions = {str(version) for version in versions}
    if len(normalized_versions) != 1:
        raise SystemExit("missing or inconsistent intelligence index versions")
    version = normalized_versions.pop()

    rows = []
    for (
        slug,
        provider,
        model_name,
        model_id,
        effort,
        effective_effort,
        pool,
    ) in BENCHMARK_PROFILES:
        model = models[slug]
        cost = value(
            model,
            "artificial_analysis_intelligence_index_cost",
            "cost_per_task",
            "total_cost",
        )
        cost = require_number(cost, "Cost Per Task", slug)

        rows.append(
            {
                "Provider": provider,
                "Model": model_name,
                "Model ID": model_id,
                "Effort": effort,
                "Effective Effort": effective_effort,
                "Access Pool": pool,
                "Cost Per Task": cost,
                "Intelligence Index": require_number(
                    value(
                        model, "evaluations", "artificial_analysis_intelligence_index"
                    ),
                    "Intelligence Index",
                    slug,
                ),
                "Model Coding Index": require_number(
                    value(model, "evaluations", "artificial_analysis_coding_index"),
                    "Model Coding Index",
                    slug,
                ),
                "Agentic Index": require_number(
                    value(model, "evaluations", "artificial_analysis_agentic_index"),
                    "Agentic Index",
                    slug,
                ),
                "Benchmark Status": "published",
                "Index Version": version,
                "As Of": as_of,
                "Source": API_URL,
            }
        )

    for profile in PENDING_PROFILES:
        rows.append(
            {
                **profile,
                "Cost Per Task": "",
                "Intelligence Index": "",
                "Model Coding Index": "",
                "Agentic Index": "",
                "Benchmark Status": "pending",
                "Index Version": "",
                "As Of": as_of,
            }
        )
    return rows


def write_rows(output: Path, rows: list[dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", newline="", dir=output.parent, delete=False
    ) as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(file.name)
    temporary.replace(output)
    output.chmod(0o644)


def main() -> None:
    args = parse_args()
    as_of = validate_as_of(args.as_of)
    write_rows(args.output, make_rows(load_payloads(args.input_json), as_of))
    print(args.output)


if __name__ == "__main__":
    main()
