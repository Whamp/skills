import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";

const TESTS_DIR = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(TESTS_DIR, "..", "scripts", "agent-vault-set-secret.sh");
const SETTINGS = [
  "--host",
  "vault-host",
  "--user",
  "vault-user",
  "--container",
  "Agent-Vault",
  "--vault",
  "default",
];

function runWithStubSsh(args, input) {
  const dir = mkdtempSync(join(tmpdir(), "agent-vault-set-secret-test-"));
  const capturePath = join(dir, "captured-stdin.txt");
  const sshPath = join(dir, "ssh");
  writeFileSync(
    sshPath,
    `#!/usr/bin/env bash
set -euo pipefail
for arg in "$@"; do
  if [[ "$arg" == *"credential list"* ]]; then
    exit 0
  fi
done
cat > "${capturePath}"
`,
    { mode: 0o755 },
  );

  try {
    const result = spawnSync(SCRIPT, [...args, ...SETTINGS], {
      input,
      encoding: "utf8",
      env: { ...process.env, PATH: `${dir}:${process.env.PATH}` },
    });
    let captured = null;
    try {
      captured = readFileSync(capturePath, "utf8");
    } catch {
      captured = null;
    }
    return { result, captured };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

test("accepts redirected secret file without a trailing newline", () => {
  const secret = "s3cr3t-without-newline";
  const { result, captured } = runWithStubSsh(["TEST_API_KEY"], secret);

  assert.equal(result.status, 0, result.stderr);
  assert.equal(captured, `${secret}\n`);
  assert.doesNotMatch(result.stdout + result.stderr, new RegExp(secret));
  assert.match(result.stderr, /Wrote TEST_API_KEY to vault default on vault-host\./);
});

test("accepts redirected secret file with a trailing newline", () => {
  const secret = "s3cr3t-with-newline";
  const { result, captured } = runWithStubSsh(["TEST_API_KEY"], `${secret}\n`);

  assert.equal(result.status, 0, result.stderr);
  assert.equal(captured, `${secret}\n`);
});

test("rejects empty secret input without writing", () => {
  const { result, captured } = runWithStubSsh(["TEST_API_KEY"], "");

  assert.equal(result.status, 2);
  assert.equal(captured, null);
  assert.match(result.stderr, /empty value - nothing written for TEST_API_KEY/);
});
