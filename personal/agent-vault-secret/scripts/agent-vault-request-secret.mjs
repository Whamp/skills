#!/usr/bin/env node
/**
 * Ask a human for secrets through an Agent Vault approval page.
 *
 * The command creates a proposal with empty credential slots and prints its
 * approval link. The human opens the link in any browser, signs in, enters each
 * value, and approves. Values go from the browser to the vault, never through
 * this process. `--wait` blocks until the proposal is no longer pending.
 */

import { spawn } from "node:child_process";
import { readFileSync, realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  CONFIG_PATH,
  requireCredentialName,
  resolveSettings,
  validateResolvedSettings,
} from "./agent-vault-add-secret-core.mjs";

const USAGE = `agent-vault-request-secret --key <NAME[=description]> ... [options]
agent-vault-request-secret --file <proposal.json> [options]
agent-vault-request-secret --wait <proposal-id> [--timeout <seconds>] [options]

  --key <name>          credential slot to request; repeat for several values.
                        Add =description to tell the human what the value is.
  --message <text>      why the agent needs the values (shown with the proposal)
  --note <text>         extra explanation for the human on the approval page
  --file <path>         send a complete proposal JSON file instead of --key
                        (use this to request a service and its credentials together)
  --wait <id>           wait until the proposal is approved, rejected, or expired
  --timeout <seconds>   how long --wait waits (default 1800)
  --host <ssh-host>     SSH host running the vault
  --user <ssh-user>     SSH user
  --container <name>    container name
  --vault <name>        vault the proposal targets

Settings fall back to the environment, then to ${CONFIG_PATH}. See SKILL.md.
Exit status for --wait: 0 applied, 1 rejected or expired, 3 still pending.
`;

const DEFAULT_TIMEOUT_SECONDS = 1800;
const POLL_INTERVAL_MS = 5000;

/** Parse arguments without performing I/O. */
export function parseRequestArgs(argv) {
  const opts = { keys: [], timeout: DEFAULT_TIMEOUT_SECONDS };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const take = () => {
      const value = argv[index + 1];
      if (value === undefined) throw new Error(`${arg} needs a value`);
      index += 1;
      return value;
    };

    if (arg === "--key") opts.keys.push(parseKeySlot(take()));
    else if (arg === "--message") opts.message = take();
    else if (arg === "--note") opts.note = take();
    else if (arg === "--file") opts.file = take();
    else if (arg === "--wait") opts.wait = requireProposalId(take());
    else if (arg === "--timeout") opts.timeout = requirePositiveInteger(take(), "--timeout");
    else if (arg === "--host") opts.host = take();
    else if (arg === "--user") opts.ssh_user = take();
    else if (arg === "--container") opts.container = take();
    else if (arg === "--vault") opts.vault = take();
    else if (arg === "--help" || arg === "-h") opts.help = true;
    else throw new Error(`unknown argument: ${arg}`);
  }

  if (opts.help) return opts;
  const modes = [opts.keys.length > 0, opts.file !== undefined, opts.wait !== undefined];
  if (modes.filter(Boolean).length !== 1) {
    throw new Error("use exactly one of --key, --file, or --wait");
  }
  const seen = new Set();
  for (const { key } of opts.keys) {
    if (seen.has(key)) throw new Error(`credential name repeated: ${key}`);
    seen.add(key);
  }
  return opts;
}

function parseKeySlot(text) {
  const separator = text.indexOf("=");
  if (separator === -1) return { key: requireCredentialName(text) };
  const description = text.slice(separator + 1).trim();
  return {
    key: requireCredentialName(text.slice(0, separator)),
    ...(description ? { description } : {}),
  };
}

function requireProposalId(text) {
  if (!/^[1-9][0-9]*$/.test(text)) throw new Error("--wait needs a proposal number");
  return Number(text);
}

function requirePositiveInteger(text, label) {
  if (!/^[1-9][0-9]*$/.test(text)) throw new Error(`${label} needs a whole number of seconds`);
  return Number(text);
}

/** Build the proposal JSON that asks the human for each credential value. */
export function buildCredentialProposal({ keys, message, note }) {
  return {
    credentials: keys.map((slot) => ({ action: "set", ...slot })),
    message: message || `Agent requests ${keys.map((slot) => slot.key).join(", ")}`,
    ...(note ? { user_message: note } : {}),
  };
}

/**
 * Remote command that creates a proposal from JSON on standard input.
 *
 * Agent Vault accepts proposals only from a vault-scoped session. The command
 * mints a five-minute session from the owner login inside the container and
 * uses it there, so the session token never leaves the container.
 */
export function createProposalCommand({ container, vault }) {
  return (
    `docker exec -i ${container} sh -c '` +
    `AGENT_VAULT_TOKEN=$(agent-vault vault token --vault ${vault} --ttl 300) ` +
    `AGENT_VAULT_VAULT=${vault} ` +
    "exec agent-vault vault proposal create -f - --json'"
  );
}

export function showProposalCommand({ container, vault }, id) {
  return `docker exec ${container} agent-vault vault proposal show ${id} --vault ${vault}`;
}

/** Read the status word from `agent-vault vault proposal show` output. */
export function parseProposalStatus(text) {
  // The CLI colours its output; drop the colour codes first.
  const plain = String(text).replace(/\x1b\[[0-9;]*m/g, "");
  const match = plain.match(/^Status:\s+(\S+)/m);
  if (!match) throw new Error("could not read the proposal status");
  return match[1];
}

/** Run one SSH command and collect its output. */
export function runSsh(opts, remoteCommand, input) {
  return new Promise((resolve) => {
    const child = spawn(
      "ssh",
      [
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "ConnectTimeout=25",
        ...(input === undefined ? ["-n"] : []),
        `${opts.ssh_user}@${opts.host}`,
        remoteCommand,
      ],
      { stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"] },
    );
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data) => {
      stdout += data;
    });
    child.stderr.on("data", (data) => {
      stderr += data;
    });
    child.on("error", (error) => resolve({ code: 1, stdout, stderr: error.message }));
    child.on("close", (code) => resolve({ code, stdout, stderr }));
    if (input !== undefined) child.stdin.end(input);
  });
}

async function createProposal(opts, ssh, readFile) {
  const proposal = opts.file
    ? readFile(opts.file, "utf8")
    : JSON.stringify(buildCredentialProposal(opts));
  const result = await ssh(opts, createProposalCommand(opts), proposal);
  if (result.code !== 0) {
    throw new Error(`could not create the proposal\n${(result.stderr || result.stdout).trim().slice(0, 400)}`);
  }
  const created = JSON.parse(result.stdout);
  return {
    exitCode: 0,
    text: [
      `Proposal ${created.id} is ${created.status} in vault ${created.vault}.`,
      `Approval link: ${created.approval_url}`,
      `Wait for the human with: agent-vault-request-secret --wait ${created.id}`,
      "",
    ].join("\n"),
  };
}

async function waitForProposal(opts, ssh, sleep, now) {
  const deadline = now() + opts.timeout * 1000;
  for (;;) {
    const result = await ssh(opts, showProposalCommand(opts, opts.wait));
    if (result.code !== 0) {
      throw new Error(`could not read proposal ${opts.wait}\n${result.stderr.trim().slice(0, 400)}`);
    }
    const status = parseProposalStatus(result.stdout);
    if (status !== "pending") {
      return { exitCode: status === "applied" ? 0 : 1, text: `Proposal ${opts.wait}: ${status}\n` };
    }
    if (now() >= deadline) {
      return { exitCode: 3, text: `Proposal ${opts.wait}: still pending after ${opts.timeout}s\n` };
    }
    await sleep(POLL_INTERVAL_MS);
  }
}

/** Run the command with injectable boundaries for tests. */
export async function runRequestSecret(argv, dependencies = {}) {
  const opts = parseRequestArgs(argv);
  if (opts.help) return { exitCode: 0, text: USAGE };

  resolveSettings(opts, dependencies.env ?? process.env, dependencies.configPath ?? CONFIG_PATH);
  validateResolvedSettings(opts);

  const ssh = dependencies.ssh ?? runSsh;
  if (opts.wait !== undefined) {
    return waitForProposal(
      opts,
      ssh,
      dependencies.sleep ?? ((ms) => new Promise((resolve) => setTimeout(resolve, ms))),
      dependencies.now ?? Date.now,
    );
  }
  return createProposal(opts, ssh, dependencies.readFile ?? readFileSync);
}

async function main() {
  try {
    const result = await runRequestSecret(process.argv.slice(2));
    process.stdout.write(result.text);
    process.exitCode = result.exitCode;
  } catch (error) {
    process.stderr.write(`agent-vault-request-secret: ${error.message}\n`);
    process.exitCode = 2;
  }
}

if (process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await main();
}
