"""Check task selection and non-Python search owners through real files."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts.discovery_corpus import (
    Query,
    Suite,
    implementation_spans,
    replay,
    select_tasks,
    tree_hash,
)
from scripts.eval_discoverable_code import SUITE_PATH


class DiscoveryTaskTests(unittest.TestCase):
    """Protect task isolation and the development/held-out split."""

    def test_bank_has_six_development_and_two_held_out_tasks(self) -> None:
        bank = cast(Suite, json.loads(SUITE_PATH.read_text()))
        development = copy.deepcopy(bank)
        select_tasks(development, None, include_held_out=False)
        self.assertEqual(
            6, sum(len(target["tasks"]) for target in development["targets"])
        )
        self.assertNotIn("p-queue", {target["id"] for target in development["targets"]})
        select_tasks(bank, None, include_held_out=True)
        self.assertEqual(8, sum(len(target["tasks"]) for target in bank["targets"]))
        self.assertEqual(4, len(bank["targets"]))
        for target in bank["targets"]:
            tasks = {task["id"] for task in target["tasks"]}
            self.assertTrue(all(query["task"] in tasks for query in target["queries"]))

    def test_subset_freezes_only_selected_questions_and_queries(self) -> None:
        bank = cast(Suite, json.loads(SUITE_PATH.read_text()))
        select_tasks(bank, ["itsdangerous/expiry"], include_held_out=False)
        self.assertEqual(["itsdangerous"], [target["id"] for target in bank["targets"]])
        target = bank["targets"][0]
        self.assertEqual(["expiry"], [task["id"] for task in target["tasks"]])
        self.assertTrue(all(query["task"] == "expiry" for query in target["queries"]))
        for name in ("p-queue/events", "itsdangerous/not-a-task"):
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "task selection"),
            ):
                select_tasks(
                    cast(Suite, json.loads(SUITE_PATH.read_text())),
                    [name],
                    include_held_out=False,
                )

    def test_typescript_owner_rejects_docs_missing_and_duplicate_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            module = source / "queue.ts"
            module.write_text(
                "function dispatch() {\n  emit('completed', result);\n  return result;\n}\n"
            )
            (root / "readme.md").write_text("The completed event carries the result.\n")
            query: Query = {
                "kind": "literal",
                "value": "completed",
                "owner": {
                    "glob": "source/**/*.ts",
                    "start": "function dispatch() {",
                    "end": "  return result;",
                },
            }
            landing = replay(root, query)["landing"]
            assert landing is not None
            self.assertEqual("direct", landing["status"])
            self.assertEqual(1, landing["direct_hits"])
            self.assertEqual(1, landing["other_hits"])
            module.rename(source / "renamed.ts")
            self.assertTrue(implementation_spans(root, query["owner"]))
            (source / "copy.ts").write_text((source / "renamed.ts").read_text())
            self.assertEqual([], implementation_spans(root, query["owner"]))
            (source / "copy.ts").unlink()
            (source / "renamed.ts").write_text("// completed event\n")
            unresolved = replay(root, query)["landing"]
            assert unresolved is not None
            self.assertEqual("oracle_unresolved", unresolved["status"])

    def test_validation_products_do_not_change_snapshot_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "implementation.ts").write_text("export const value = 42;\n")
            before = tree_hash(root)
            for folder in ("dist", "node_modules"):
                (root / folder).mkdir()
                (root / folder / "generated.js").write_text(
                    "irrelevant generated output"
                )
            self.assertEqual(before, tree_hash(root))
            (root / "implementation.ts").write_text("export const value = 43;\n")
            self.assertNotEqual(before, tree_hash(root))


if __name__ == "__main__":
    unittest.main()
