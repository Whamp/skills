import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { chmodSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  applyCredentialWriteResult,
  buildSecretWindowHtml,
  createCredentialSequence,
  credentialButtonLabel,
  credentialSubtitle,
  currentCredential,
  parseAddSecretArgs,
  preflightVault,
  writeCredential,
} from "../scripts/agent-vault-add-secret-core.mjs";
import { runAddSecret } from "../scripts/agent-vault-add-secret.mjs";

const TEST_SETTINGS = [
  "--host",
  "vault-host",
  "--user",
  "vault-user",
  "--container",
  "Agent-Vault",
  "--vault",
  "default",
];

test("repeated key flags preserve their declared order", () => {
  const opts = parseAddSecretArgs([
    "--key",
    "CREDITSIGHTS_USERNAME",
    "--key=CREDITSIGHTS_PASSWORD",
  ]);
  assert.deepEqual(opts.keys, ["CREDITSIGHTS_USERNAME", "CREDITSIGHTS_PASSWORD"]);
});

test("duplicate keys fail before preflight or window import", async () => {
  let preflightCalls = 0;
  let importCalls = 0;

  await assert.rejects(
    runAddSecret(
      [
        ...TEST_SETTINGS,
        "--key",
        "CREDITSIGHTS_USERNAME",
        "--key=CREDITSIGHTS_USERNAME",
      ],
      {
        preflightVault: async () => {
          preflightCalls += 1;
        },
        importGlimpse: async () => {
          importCalls += 1;
          return { open() {} };
        },
      },
    ),
    /credential name repeated: CREDITSIGHTS_USERNAME/,
  );
  assert.equal(preflightCalls, 0);
  assert.equal(importCalls, 0);
});

test("credential sequence advances only after successful writes", () => {
  const initial = createCredentialSequence(["USERNAME", "PASSWORD"]);
  assert.deepEqual(currentCredential(initial), { key: "USERNAME", index: 0, count: 2 });

  const failed = applyCredentialWriteResult(initial, false);
  assert.strictEqual(failed, initial);
  assert.equal(failed.complete, false);

  const second = applyCredentialWriteResult(initial, true);
  assert.deepEqual(currentCredential(second), { key: "PASSWORD", index: 1, count: 2 });
  assert.equal(second.complete, false);

  const complete = applyCredentialWriteResult(second, true);
  assert.equal(complete.complete, true);
  assert.deepEqual(currentCredential(complete), { key: "PASSWORD", index: 1, count: 2 });
});

test("graphical workflow advances after success and retries the same key after failure", async () => {
  const messages = [];
  const writes = [];
  let messageHandler;
  const win = {
    close() {},
    on(event, handler) {
      assert.equal(event, "message");
      messageHandler = handler;
    },
    send(message) {
      messages.push(message);
    },
  };
  const outcomes = [{ ok: true, message: "" }, { ok: false, message: "try again" }];

  await runAddSecret(
    [
      ...TEST_SETTINGS,
      "--dry-run",
      "--key",
      "CREDITSIGHTS_USERNAME",
      "--key",
      "CREDITSIGHTS_PASSWORD",
    ],
    {
      importGlimpse: async () => ({ open: () => win }),
      readClipboard: async () => null,
      knownGlimpseAddresses: async () => new Set(),
      floatOwnWindow: async () => {},
      writeCredential: async (_opts, key, value) => {
        writes.push({ key, value });
        return outcomes.shift();
      },
    },
  );

  await messageHandler({ action: "add", value: "username-secret" });
  await messageHandler({ action: "add", value: "password-secret" });

  assert.deepEqual(writes, [
    { key: "CREDITSIGHTS_USERNAME", value: "username-secret" },
    { key: "CREDITSIGHTS_PASSWORD", value: "password-secret" },
  ]);
  assert.match(messages[0], /credential 2 of 2: CREDITSIGHTS_PASSWORD/);
  assert.match(messages[0], /Add secret/);
  assert.match(messages[1], /try again/);
  assert.doesNotMatch(messages.join("\n"), /username-secret|password-secret/);
});

test("window HTML renders only the current fixed key and escapes display data", () => {
  const credential = { key: "CURRENT<KEY>", index: 0, count: 2 };
  const html = buildSecretWindowHtml({
    vault: "vault<&>",
    credential,
    clipboardAvailable: false,
    needsName: false,
  });

  assert.match(html, /credential 1 of 2: CURRENT&lt;KEY&gt; · vault vault&lt;&amp;&gt;/);
  assert.doesNotMatch(html, /NEXT_KEY/);
  assert.doesNotMatch(html, /CURRENT<KEY>/);
  assert.match(html, />Add and continue<\/button>/);
  assert.equal(credentialSubtitle(credential, "default"), "credential 1 of 2: CURRENT<KEY> · vault default");
  assert.equal(credentialButtonLabel(credential), "Add and continue");
  assert.equal(
    credentialButtonLabel({ key: "NEXT_KEY", index: 1, count: 2 }),
    "Add secret",
  );
});

test("preflight checks the configured container and vault over SSH", async () => {
  let call;
  await preflightVault(
    {
      container: "Agent-Vault",
      vault: "default",
      ssh_user: "vault-user",
      host: "vault-host",
    },
    async (...args) => {
      call = args;
      return { stdout: "", stderr: "" };
    },
  );

  assert.deepEqual(call, [
    "ssh",
    [
      "-o",
      "BatchMode=yes",
      "-o",
      "IdentitiesOnly=yes",
      "-o",
      "ConnectTimeout=25",
      "vault-user@vault-host",
      "docker",
      "exec",
      "Agent-Vault",
      "agent-vault",
      "vault",
      "credential",
      "list",
      "--vault",
      "default",
    ],
    { timeout: 30000 },
  ]);
});

test("preflight rejects shell metacharacters before invoking SSH", async () => {
  let execCalls = 0;
  await assert.rejects(
    preflightVault(
      {
        container: "Agent-Vault;touch-pwned",
        vault: "default",
        ssh_user: "vault-user",
        host: "vault-host",
      },
      async () => {
        execCalls += 1;
      },
    ),
    /container must be letters, digits, dot, dash, or underscore/,
  );
  assert.equal(execCalls, 0);
});

test("preflight failure occurs before Glimpse import", async () => {
  let importCalls = 0;
  await assert.rejects(
    runAddSecret([...TEST_SETTINGS, "--key", "API_KEY"], {
      preflightVault: async () => {
        throw new Error(
          "Agent Vault preflight failed for vault-user@vault-host.\n" +
            "SSH access, container Agent-Vault, and vault default must work before entering a secret.",
        );
      },
      importGlimpse: async () => {
        importCalls += 1;
        return { open() {} };
      },
    }),
    /^Error: Agent Vault preflight failed for vault-user@vault-host\./,
  );
  assert.equal(importCalls, 0);
});

test("remote write failures redact the secret value", async () => {
  const secret = "private-value";
  const fakeSpawn = () => {
    const child = new EventEmitter();
    child.stdout = new EventEmitter();
    child.stderr = new EventEmitter();
    child.stdin = {
      end() {
        queueMicrotask(() => {
          child.stderr.emit("data", Buffer.from(`remote rejected ${secret}`));
          child.emit("close", 1);
        });
      },
    };
    return child;
  };

  const result = await writeCredential(
    {
      container: "Agent-Vault",
      vault: "default",
      ssh_user: "vault-user",
      host: "vault-host",
      dryRun: false,
    },
    "API_KEY",
    secret,
    fakeSpawn,
  );

  assert.deepEqual(result, { ok: false, message: "remote rejected <redacted>" });
  assert.doesNotMatch(result.message, new RegExp(secret));
});

test("terminal intake handles several credential names after one preflight", () => {
  const testDirectory = mkdtempSync(join(tmpdir(), "agent-vault-secret-test-"));
  const fakeSsh = join(testDirectory, "ssh");
  const sshLog = join(testDirectory, "ssh.log");
  writeFileSync(
    fakeSsh,
    [
      "#!/usr/bin/env bash",
      "printf '%s\\n' \"$*\" >> \"$SSH_LOG\"",
      "case \"$*\" in",
      "  *'credential list'*) exit 0 ;;",
      "esac",
      "cat >/dev/null",
      "",
    ].join("\n"),
  );
  chmodSync(fakeSsh, 0o755);

  const testsDirectory = dirname(fileURLToPath(import.meta.url));
  const script = join(testsDirectory, "..", "scripts", "agent-vault-set-secret.sh");
  const result = spawnSync(
    "bash",
    [script, "USERNAME", "PASSWORD", ...TEST_SETTINGS],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        PATH: `${testDirectory}:${process.env.PATH}`,
        SSH_LOG: sshLog,
      },
      input: "first-secret\nsecond-secret\n",
    },
  );
  const calls = readFileSync(sshLog, "utf8").trim().split("\n");
  rmSync(testDirectory, { recursive: true, force: true });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stderr, /Secret value for USERNAME:/);
  assert.match(result.stderr, /Secret value for PASSWORD:/);
  assert.match(result.stderr, /Wrote USERNAME to vault default on vault-host\./);
  assert.match(result.stderr, /Wrote PASSWORD to vault default on vault-host\./);
  assert.equal(calls.length, 3);
  assert.match(calls[0], /credential list --vault default/);
  assert.match(calls[1], /USERNAME=/);
  assert.match(calls[2], /PASSWORD=/);
  assert.doesNotMatch(result.stderr, /first-secret|second-secret/);
});

test("terminal intake preflight fails before either interactive prompt", () => {
  const testDirectory = mkdtempSync(join(tmpdir(), "agent-vault-secret-test-"));
  const fakeSsh = join(testDirectory, "ssh");
  writeFileSync(fakeSsh, "#!/usr/bin/env bash\necho 'no SSH identity' >&2\nexit 42\n");
  chmodSync(fakeSsh, 0o755);

  const testsDirectory = dirname(fileURLToPath(import.meta.url));
  const script = join(testsDirectory, "..", "scripts", "agent-vault-set-secret.sh");
  const result = spawnSync(
    "bash",
    [
      script,
      "--host",
      "vault-host",
      "--user",
      "vault-user",
      "--container",
      "Agent-Vault",
      "--vault",
      "default",
    ],
    {
      encoding: "utf8",
      env: { ...process.env, PATH: `${testDirectory}:${process.env.PATH}` },
      input: "this-must-not-be-read\n",
    },
  );
  rmSync(testDirectory, { recursive: true, force: true });

  assert.equal(result.status, 1);
  assert.match(
    result.stderr,
    /agent-vault-set-secret: Agent Vault preflight failed for vault-user@vault-host\./,
  );
  assert.doesNotMatch(result.stderr, /Credential name/);
  assert.doesNotMatch(result.stderr, /Secret value/);
  assert.doesNotMatch(result.stderr, /this-must-not-be-read/);
});
