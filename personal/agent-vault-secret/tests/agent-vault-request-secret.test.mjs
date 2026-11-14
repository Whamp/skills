import assert from "node:assert/strict";
import { mkdtempSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  parseProposalStatus,
  parseRequestArgs,
  runRequestSecret,
} from "../scripts/agent-vault-request-secret.mjs";

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

const NO_CONFIG = { env: {}, configPath: "/nonexistent/agent-vault-secret/config" };

function recordingSsh(responses) {
  const calls = [];
  const ssh = async (opts, command, input) => {
    calls.push({ target: `${opts.ssh_user}@${opts.host}`, command, input });
    return responses.shift();
  };
  return { calls, ssh };
}

test("request command runs when invoked through an installed symlink", () => {
  const testDirectory = mkdtempSync(join(tmpdir(), "agent-vault-request-test-"));
  const testsDirectory = dirname(fileURLToPath(import.meta.url));
  const script = join(testsDirectory, "..", "scripts", "agent-vault-request-secret.mjs");
  const command = join(testDirectory, "agent-vault-request-secret");
  symlinkSync(script, command);

  const result = spawnSync(process.execPath, [command, "--help"], { encoding: "utf8" });
  rmSync(testDirectory, { recursive: true, force: true });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /agent-vault-request-secret --key <NAME\[=description\]>/);
});

test("a request sends credential slots as proposal JSON and prints the approval link", async () => {
  const { calls, ssh } = recordingSsh([
    {
      code: 0,
      stdout: JSON.stringify({
        approval_url: "http://vault.example:14321/approve/14?token=read-only",
        id: 14,
        status: "pending",
        vault: "default",
      }),
      stderr: "",
    },
  ]);

  const result = await runRequestSecret(
    [
      "--key",
      "SERVICE_USERNAME",
      "--key",
      "SERVICE_PASSWORD=Password for the reporting site",
      "--message",
      "Store the reporting site login",
      ...SETTINGS,
    ],
    { ...NO_CONFIG, ssh },
  );

  assert.equal(calls.length, 1);
  assert.equal(calls[0].target, "vault-user@vault-host");
  assert.match(calls[0].command, /^docker exec -i Agent-Vault sh -c '/);
  assert.match(calls[0].command, /proposal create -f - --json/);
  assert.deepEqual(JSON.parse(calls[0].input), {
    credentials: [
      { action: "set", key: "SERVICE_USERNAME" },
      { action: "set", key: "SERVICE_PASSWORD", description: "Password for the reporting site" },
    ],
    message: "Store the reporting site login",
  });
  assert.equal(result.exitCode, 0);
  assert.match(result.text, /Approval link: http:\/\/vault\.example:14321\/approve\/14\?token=read-only/);
  assert.match(result.text, /agent-vault-request-secret --wait 14/);
});

test("a proposal file is sent unchanged", async () => {
  const proposal = '{"services":[{"name":"example"}],"credentials":[]}';
  const { calls, ssh } = recordingSsh([
    { code: 0, stdout: '{"id":3,"status":"pending","vault":"default","approval_url":"u"}', stderr: "" },
  ]);

  await runRequestSecret(["--file", "proposal.json", ...SETTINGS], {
    ...NO_CONFIG,
    ssh,
    readFile: (path) => {
      assert.equal(path, "proposal.json");
      return proposal;
    },
  });

  assert.equal(calls[0].input, proposal);
});

test("waiting polls until the proposal leaves pending and maps its status to an exit code", async (t) => {
  const cases = [
    { final: "applied", exitCode: 0 },
    { final: "rejected", exitCode: 1 },
  ];
  for (const { final, exitCode } of cases) {
    await t.test(final, async () => {
      const show = (status) => ({
        code: 0,
        stdout: `Proposal #7\n\u001b[1mStatus:\u001b[0m      ${status}\nCreated: x\n`,
        stderr: "",
      });
      const { calls, ssh } = recordingSsh([show("pending"), show(final)]);
      let sleeps = 0;

      const result = await runRequestSecret(["--wait", "7", ...SETTINGS], {
        ...NO_CONFIG,
        ssh,
        sleep: async () => {
          sleeps += 1;
        },
        now: () => 0,
      });

      assert.equal(calls.length, 2);
      assert.equal(calls[0].input, undefined);
      assert.equal(
        calls[0].command,
        "docker exec Agent-Vault agent-vault vault proposal show 7 --vault default",
      );
      assert.equal(sleeps, 1);
      assert.equal(result.exitCode, exitCode);
      assert.equal(result.text, `Proposal 7: ${final}\n`);
    });
  }
});

test("waiting stops with exit code 3 when the timeout passes", async () => {
  const pending = { code: 0, stdout: "Status:      pending\n", stderr: "" };
  const { ssh } = recordingSsh([pending, pending, pending]);
  let clock = 0;

  const result = await runRequestSecret(["--wait", "7", "--timeout", "10", ...SETTINGS], {
    ...NO_CONFIG,
    ssh,
    sleep: async (ms) => {
      clock += ms;
    },
    now: () => clock,
  });

  assert.equal(result.exitCode, 3);
  assert.match(result.text, /still pending after 10s/);
});

test("arguments must choose exactly one mode and name each credential once", () => {
  assert.throws(() => parseRequestArgs([]), /exactly one of --key, --file, or --wait/);
  assert.throws(() => parseRequestArgs(["--key", "A", "--wait", "3"]), /exactly one/);
  assert.throws(() => parseRequestArgs(["--key", "A", "--key", "A=again"]), /repeated: A/);
  assert.throws(() => parseRequestArgs(["--key", "BAD-NAME"]), /credential name/);
  assert.throws(() => parseRequestArgs(["--wait", "7;rm"]), /proposal number/);
});

test("unsafe container names are rejected before SSH runs", async () => {
  const { calls, ssh } = recordingSsh([]);
  await assert.rejects(
    runRequestSecret(
      ["--key", "A", "--host", "h", "--user", "u", "--container", "x'; id", "--vault", "default"],
      { ...NO_CONFIG, ssh },
    ),
    /container must be/,
  );
  assert.equal(calls.length, 0);
});

test("status parsing fails loudly when the CLI output changes", () => {
  assert.equal(parseProposalStatus("Status:      applied\n"), "applied");
  assert.throws(() => parseProposalStatus("no status here"), /could not read the proposal status/);
});
