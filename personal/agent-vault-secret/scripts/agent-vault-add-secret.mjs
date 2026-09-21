#!/usr/bin/env node
/**
 * Open a native window where a human can send one or more secrets to Agent Vault.
 * Secret values travel from the window to the vault over SSH and never reach stdout.
 */

import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { promisify } from "node:util";

import {
  CONFIG_PATH,
  SETTINGS,
  applyCredentialWriteResult,
  buildSecretWindowHtml,
  createCredentialSequence,
  credentialButtonLabel,
  credentialSubtitle,
  currentCredential,
  parseAddSecretArgs,
  preflightVault,
  requireCredentialName,
  resolveSettings,
  validateResolvedSettings,
  writeCredential,
} from "./agent-vault-add-secret-core.mjs";

const GLIMPSE_CANDIDATES = [
  `${process.env.HOME}/.pi/agent/npm/node_modules/glimpseui/src/glimpse.mjs`,
  "/usr/lib/node_modules/glimpseui/src/glimpse.mjs",
  "/usr/local/lib/node_modules/glimpseui/src/glimpse.mjs",
];

const execFileAsync = promisify(execFile);

const USAGE = `agent-vault-add-secret [--key <CREDENTIAL_NAME> ...] [options]

  --key <name>        credential name to create or update; repeat for a guided sequence
  --dry-run           show the window but do not connect to or write to the vault
  --check             print the resolved settings and exit
  --host <ssh-host>   SSH host running the vault
  --user <ssh-user>   SSH user
  --container <name>  container name
  --vault <name>      vault to write into
  --proxy-url <url>   proxy address, used by the verification step

--host, --user, --container, and --vault fall back to the environment, then to
${CONFIG_PATH}. See SKILL.md.
`;

function resolveGlimpse() {
  for (const path of GLIMPSE_CANDIDATES) {
    if (existsSync(path)) return path;
  }
  throw new Error(
    `glimpseui not found. Install it with: npm install -g glimpseui\nLooked in:\n  ` +
      GLIMPSE_CANDIDATES.join("\n  "),
  );
}

async function readClipboard() {
  try {
    const { stdout } = await execFileAsync("wl-paste", ["--no-newline"], { timeout: 3000 });
    return stdout || null;
  } catch {
    return null;
  }
}

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function hyprctl(args) {
  const { stdout } = await execFileAsync("hyprctl", args, { timeout: 4000 });
  return stdout.trim();
}

async function glimpseWindowAddresses() {
  return JSON.parse(await hyprctl(["-j", "clients"]))
    .filter((client) => String(client.class ?? "").startsWith("chrome-_text_html"))
    .map((client) => client.address);
}

async function knownGlimpseAddresses() {
  if (!process.env.HYPRLAND_INSTANCE_SIGNATURE) return new Set();
  try {
    return new Set(await glimpseWindowAddresses());
  } catch (error) {
    process.stderr.write(
      `agent-vault-add-secret: could not list existing windows: ${error.message}\n`,
    );
    return new Set();
  }
}

async function floatOwnWindow(width, height, knownAddresses) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    await sleep(100);
    const address = (await glimpseWindowAddresses()).find(
      (candidate) => !knownAddresses.has(candidate),
    );
    if (!address) continue;
    const target = `window = "address:${address}"`;
    await hyprctl(["dispatch", `hl.dsp.window.float({ action = "set", ${target} })`]);
    await hyprctl([
      "dispatch",
      `hl.dsp.window.resize({ x = ${width}, y = ${height}, ${target} })`,
    ]);
    await hyprctl(["dispatch", `hl.dsp.window.center({ ${target} })`]);
    return;
  }
}

function settingsOutput(opts) {
  return SETTINGS.filter((setting) => opts[setting.key])
    .map((setting) => `${setting.key}=${opts[setting.key]}`)
    .join("\n");
}

function sendWindowResult(win, result) {
  win.send(`window.__reportResult(${JSON.stringify(result)})`);
}

function createWindowMessageHandler({
  opts,
  win,
  initialSequence,
  clipboardReader,
  credentialWriter,
}) {
  let sequence = initialSequence;
  return async (data) => {
    if (!data || typeof data !== "object") return;
    if (data.action === "readClipboard") {
      const value = await clipboardReader();
      win.send(`window.__receiveClipboard(${JSON.stringify(value)})`);
      return;
    }
    if (data.action === "cancel") {
      win.close();
      return;
    }
    if (data.action !== "add") return;

    let key;
    try {
      key = sequence ? currentCredential(sequence).key : requireCredentialName(data.key);
    } catch (error) {
      sendWindowResult(win, { ok: false, message: error.message });
      return;
    }

    const result = await credentialWriter(opts, key, data.value);
    if (!result.ok) {
      sendWindowResult(win, result);
      return;
    }

    if (sequence) {
      sequence = applyCredentialWriteResult(sequence, true);
      if (!sequence.complete) {
        const next = currentCredential(sequence);
        sendWindowResult(win, {
          ok: true,
          next: {
            subtitle: credentialSubtitle(next, opts.vault),
            buttonLabel: credentialButtonLabel(next),
          },
        });
        return;
      }
    }

    const count = sequence?.keys.length ?? 1;
    const message = count === 1 ? "Added to the vault." : `Added ${count} secrets.`;
    sendWindowResult(win, { ok: true, message });
    setTimeout(() => win.close(), 1100);
  };
}

async function openSecretWindow(opts, dependencies) {
  const importGlimpse =
    dependencies.importGlimpse ?? (async () => import(resolveGlimpse()));
  const clipboardReader = dependencies.readClipboard ?? readClipboard;
  const addressesReader = dependencies.knownGlimpseAddresses ?? knownGlimpseAddresses;
  const floatWindow = dependencies.floatOwnWindow ?? floatOwnWindow;
  const credentialWriter = dependencies.writeCredential ?? writeCredential;
  const [{ open }, clipboard, knownAddresses] = await Promise.all([
    importGlimpse(),
    clipboardReader(),
    addressesReader(),
  ]);

  const sequence = opts.keys.length > 0 ? createCredentialSequence(opts.keys) : null;
  const initialCredential = sequence ? currentCredential(sequence) : null;
  const needsName = !sequence;
  const width = 470;
  const height = needsName ? 360 : 300;
  const title =
    sequence && sequence.keys.length > 1
      ? `Agent Vault - add ${sequence.keys.length} secrets`
      : sequence
        ? `Agent Vault - ${initialCredential.key}`
        : "Agent Vault - add secret";
  const win = open(
    buildSecretWindowHtml({
      vault: opts.vault,
      credential: initialCredential,
      clipboardAvailable: Boolean(clipboard),
      needsName,
    }),
    { width, height, title, floating: true },
  );

  if (process.env.HYPRLAND_INSTANCE_SIGNATURE) {
    floatWindow(width, height, knownAddresses).catch((error) => {
      process.stderr.write(
        `agent-vault-add-secret: could not float the window: ${error.message}\n`,
      );
    });
  }

  win.on(
    "message",
    createWindowMessageHandler({
      opts,
      win,
      initialSequence: sequence,
      clipboardReader,
      credentialWriter,
    }),
  );
  return { kind: "window", window: win };
}

/** Run graphical secret intake with injectable boundaries for tests. */
export async function runAddSecret(argv, dependencies = {}) {
  const opts = parseAddSecretArgs(argv);
  if (opts.help) return { kind: "help", text: USAGE };

  resolveSettings(opts, dependencies.env ?? process.env, dependencies.configPath ?? CONFIG_PATH);
  validateResolvedSettings(opts);
  if (opts.check) return { kind: "check", text: `${settingsOutput(opts)}\n` };

  const runPreflight = dependencies.preflightVault ?? preflightVault;
  if (!opts.dryRun) await runPreflight(opts);
  return openSecretWindow(opts, dependencies);
}

async function main() {
  try {
    const result = await runAddSecret(process.argv.slice(2));
    if (result.kind === "help" || result.kind === "check") process.stdout.write(result.text);
  } catch (error) {
    process.stderr.write(`agent-vault-add-secret: ${error.message}\n`);
    if (!String(error.message).startsWith("Agent Vault preflight failed")) {
      process.stderr.write(`\n${USAGE}`);
    }
    process.exitCode = 2;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  await main();
}
