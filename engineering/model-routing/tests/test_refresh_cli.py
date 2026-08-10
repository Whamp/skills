#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "refresh-aa-model-profiles.py"
FIXTURE = Path(__file__).resolve().parent / "aa-free-response.json"
PARTIAL_FIXTURE = Path(__file__).resolve().parent / "aa-free-partial-response.json"


class RefreshCliTest(unittest.TestCase):
    def test_writes_selected_model_profiles_with_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profiles.csv"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(FIXTURE),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-07-12",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))
            mode = output.stat().st_mode & 0o777
            output_bytes = output.read_bytes()

        self.assertEqual(mode, 0o644)
        self.assertNotIn(b"\r", output_bytes)
        self.assertEqual(len(rows), 12)
        rows_by_id = {row["Model ID"]: row for row in rows}
        self.assertEqual(len(rows_by_id), 12)
        self.assertEqual(
            rows_by_id["openai-codex/gpt-5.6-luna:xhigh"]["Model Coding Index"],
            "68.6",
        )
        self.assertEqual(
            rows_by_id["openai-codex/gpt-5.6-sol:high"]["Model Coding Index"],
            "77.2",
        )
        self.assertEqual(
            rows_by_id["openai-codex/gpt-5.6-sol:max"]["Agentic Index"],
            "54.0",
        )
        self.assertEqual(
            rows_by_id["openai-codex/gpt-5.6-luna:xhigh"]["Access Pool"],
            "OpenAI subscription",
        )
        self.assertEqual(
            rows_by_id["zai/glm-5.2"]["Access Pool"], "Z.ai Pro subscription"
        )
        self.assertEqual(rows_by_id["zai/glm-5.2:none"]["Cost Per Task"], "")
        self.assertEqual(rows_by_id["zai/glm-5.2"]["Index Version"], "4.1")
        self.assertEqual(rows_by_id["zai/glm-5.2"]["As Of"], "2026-07-12")
        self.assertNotIn("Unselected Model", {row["Model"] for row in rows})

    def test_rejects_incomplete_payload_without_replacing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profiles.csv"
            output.write_text("existing snapshot\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(PARTIAL_FIXTURE),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-07-12",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required model profiles", result.stderr)
            self.assertEqual(output.read_text(), "existing snapshot\n")

    def test_rejects_missing_benchmark_index_without_replacing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            malformed_fixture = directory_path / "malformed.json"
            payload = json.loads(FIXTURE.read_text())
            del payload["data"][0]["evaluations"]["artificial_analysis_coding_index"]
            malformed_fixture.write_text(json.dumps(payload))
            output = directory_path / "profiles.csv"
            output.write_text("existing snapshot\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(malformed_fixture),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-07-12",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid Model Coding Index", result.stderr)
            self.assertEqual(output.read_text(), "existing snapshot\n")

    def test_rejects_invalid_as_of_date_without_replacing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profiles.csv"
            output.write_text("existing snapshot\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(FIXTURE),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-02-30",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid --as-of date", result.stderr)
            self.assertEqual(output.read_text(), "existing snapshot\n")

    def test_rejects_inconsistent_index_versions_without_replacing_snapshot(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            inconsistent_fixture = directory_path / "inconsistent.json"
            payload = json.loads(FIXTURE.read_text())
            inconsistent_fixture.write_text(
                json.dumps(
                    [
                        payload,
                        {"intelligence_index_version": "4.2", "data": []},
                    ]
                )
            )
            output = directory_path / "profiles.csv"
            output.write_text("existing snapshot\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(inconsistent_fixture),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-07-12",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("inconsistent intelligence index versions", result.stderr)
            self.assertEqual(output.read_text(), "existing snapshot\n")

    def test_rejects_page_without_index_version_without_replacing_snapshot(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            missing_version_fixture = directory_path / "missing-version.json"
            payload = json.loads(FIXTURE.read_text())
            missing_version_fixture.write_text(json.dumps([payload, {"data": []}]))
            output = directory_path / "profiles.csv"
            output.write_text("existing snapshot\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(missing_version_fixture),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-07-12",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "missing or inconsistent intelligence index versions", result.stderr
            )
            self.assertEqual(output.read_text(), "existing snapshot\n")

    def test_rejects_non_finite_number_without_replacing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            malformed_fixture = directory_path / "non-finite.json"
            payload = json.loads(FIXTURE.read_text())
            payload["data"][0]["evaluations"]["artificial_analysis_coding_index"] = (
                float("nan")
            )
            malformed_fixture.write_text(json.dumps(payload))
            output = directory_path / "profiles.csv"
            output.write_text("existing snapshot\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-json",
                    str(malformed_fixture),
                    "--output",
                    str(output),
                    "--as-of",
                    "2026-07-12",
                ],
                capture_output=True,
                check=False,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid Model Coding Index", result.stderr)
            self.assertEqual(output.read_text(), "existing snapshot\n")


if __name__ == "__main__":
    unittest.main()
