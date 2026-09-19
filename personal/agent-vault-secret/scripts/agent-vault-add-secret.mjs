#!/usr/bin/env node
/**
 * agent-vault-add-secret — hand a secret to Agent Vault without it entering an
 * agent's context.
 *
 * Opens a small native window (Glimpse). The human pastes the secret there; the
 * value travels from the window straight to the vault over SSH. It is never
 * written to stdout, a log file, or the calling agent's conversation.
 *
 * Usage:
 *   agent-vault-add-secret --key OPENAI_API_KEY   # agent-driven: name is known
 *   agent-vault-add-secret                        # standalone: window asks for the name
 *   agent-vault-add-secret --key TEST_KEY --dry-run
 *
 * The agent supplies the credential *name*; the human supplies the *value*.
 *
 * Needs a graphical session on the host that runs it. Where there is none — a
 * laptop at a TTY, a remote host, an SSH session — use agent-vault-set-secret
 * instead and have the human run it in their own terminal.
 */

import { execFile, spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { promisify } from "node:util";

/** Glimpse ships as a Pi package; find it wherever this host installed it. */
const GLIMPSE_CANDIDATES = [
  `${process.env.HOME}/.pi/agent/npm/node_modules/glimpseui/src/glimpse.mjs`,
  "/usr/lib/node_modules/glimpseui/src/glimpse.mjs",
  "/usr/local/lib/node_modules/glimpseui/src/glimpse.mjs",
];

const execFileAsync = promisify(execFile);

/**
 * The host, user, container, and vault belong to the consumer, not to this
 * skill, so there are no built-in defaults. They come from a config file
 * outside the skill directory — reinstalling the skill cannot clobber it — or
 * from a flag, or from an environment variable.
 */
const CONFIG_PATH = `${
  process.env.XDG_CONFIG_HOME || `${process.env.HOME}/.config`
}/agent-vault-secret/config`;

const SETTINGS = [
  { key: "host", env: "AGENT_VAULT_SECRET_HOST", label: "SSH host running the vault" },
  { key: "ssh_user", env: "AGENT_VAULT_SECRET_SSH_USER", label: "SSH user" },
  { key: "container", env: "AGENT_VAULT_SECRET_CONTAINER", label: "container name" },
  { key: "vault", env: "AGENT_VAULT_SECRET_VAULT", label: "vault name" },
  {
    key: "proxy_url",
    env: "AGENT_VAULT_SECRET_PROXY_URL",
    label: "proxy address, used by the verification step",
    optional: true,
  },
];

const USAGE = `agent-vault-add-secret [--key <CREDENTIAL_NAME>] [options]

  --key <name>        credential name to create or update (omit to ask in the window)
  --dry-run           show the window but do not write to the vault
  --check             print the resolved settings and exit
  --host <ssh-host>   SSH host running the vault
  --user <ssh-user>   SSH user
  --container <name>  container name
  --vault <name>      vault to write into
  --proxy-url <url>   proxy address, used by the verification step

--host, --user, --container, and --vault fall back to the environment, then to
${CONFIG_PATH}. See SKILL.md.
`;

/** Read `key=value` lines, ignoring blanks and `#` comments. */
function readConfigFile() {
  if (!existsSync(CONFIG_PATH)) return {};
  const values = {};
  for (const line of readFileSync(CONFIG_PATH, "utf8").split("\n")) {
    const text = line.trim();
    if (!text || text.startsWith("#")) continue;
    const separator = text.indexOf("=");
    if (separator === -1) continue;
    values[text.slice(0, separator).trim()] = text.slice(separator + 1).trim();
  }
  return values;
}

function parseArgs(argv) {
  const opts = { dryRun: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const take = () => {
      const v = argv[i + 1];
      if (v === undefined) throw new Error(`${arg} needs a value`);
      i += 1;
      return v;
    };
    if (arg === "--key") opts.key = take();
    else if (arg === "--host") opts.host = take();
    else if (arg === "--user") opts.ssh_user = take();
    else if (arg === "--container") opts.container = take();
    else if (arg === "--vault") opts.vault = take();
    else if (arg === "--proxy-url") opts.proxy_url = take();
    else if (arg === "--dry-run") opts.dryRun = true;
    else if (arg === "--check") opts.check = true;
    else if (arg === "--help" || arg === "-h") opts.help = true;
    else if (arg.startsWith("--key=")) opts.key = arg.slice(6);
    else if (arg.startsWith("--host=")) opts.host = arg.slice(7);
    else if (arg.startsWith("--user=")) opts.ssh_user = arg.slice(7);
    else if (arg.startsWith("--container=")) opts.container = arg.slice(12);
    else if (arg.startsWith("--vault=")) opts.vault = arg.slice(8);
    else if (arg.startsWith("--proxy-url=")) opts.proxy_url = arg.slice(12);
    else throw new Error(`unknown argument: ${arg}`);
  }
  return opts;
}

/** Flag, then environment, then config file. Required settings must resolve. */
function resolveSettings(opts) {
  const config = readConfigFile();
  const missing = [];
  for (const setting of SETTINGS) {
    const value = opts[setting.key] ?? process.env[setting.env] ?? config[setting.key];
    if (value) {
      opts[setting.key] = value;
    } else if (!setting.optional) {
      missing.push(setting);
    }
  }
  if (missing.length) {
    throw new Error(
      [
        "this host is not configured for Agent Vault.",
        "",
        `Add these to ${CONFIG_PATH}:`,
        ...missing.map((s) => `  ${s.key}=<${s.label}>`),
        "",
        `Or pass them as flags, or set ${missing.map((s) => s.env).join(", ")}.`,
      ].join("\n"),
    );
  }
  return opts;
}

function resolveGlimpse() {
  for (const path of GLIMPSE_CANDIDATES) {
    if (existsSync(path)) return path;
  }
  throw new Error(
    `glimpseui not found. Install it with: npm install -g glimpseui\nLooked in:\n  ` +
      GLIMPSE_CANDIDATES.join("\n  "),
  );
}

/**
 * Credential names are interpolated into a shell command on the remote host, so
 * they must be plain identifiers. Reject anything else rather than escaping it.
 */
function requireCredentialName(name) {
  const value = String(name ?? "").trim();
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(value)) {
    throw new Error(
      "credential name must start with a letter or underscore and contain only " +
        "letters, digits, and underscores",
    );
  }
  return value;
}

/**
 * The vault, container, user, and host are interpolated into the same remote
 * shell command. They must be plain identifiers or hostnames too — the caller
 * may be an agent working from text it did not write.
 */
function requireSafeToken(value, label) {
  const text = String(value ?? "").trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(text)) {
    throw new Error(`${label} must be letters, digits, dot, dash, or underscore`);
  }
  return text;
}

const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/** Read the Wayland clipboard. Returns null when unavailable or empty. */
async function readClipboard() {
  try {
    const { stdout } = await execFileAsync("wl-paste", ["--no-newline"], { timeout: 3000 });
    return stdout || null;
  } catch {
    return null;
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function hyprctl(args) {
  const { stdout } = await execFileAsync("hyprctl", args, { timeout: 4000 });
  return stdout.trim();
}

/** Addresses of the Glimpse windows currently open. */
async function glimpseWindowAddresses() {
  return JSON.parse(await hyprctl(["-j", "clients"]))
    .filter((c) => String(c.class ?? "").startsWith("chrome-_text_html"))
    .map((c) => c.address);
}

/**
 * Addresses of the Glimpse windows already open, so the new one can be told
 * apart from them. Off Hyprland there is nothing to float, and if hyprctl
 * cannot answer there is nothing to distinguish either, so an empty set is the
 * honest answer in both cases.
 */
async function knownGlimpseAddresses() {
  if (!process.env.HYPRLAND_INSTANCE_SIGNATURE) return new Set();
  try {
    return new Set(await glimpseWindowAddresses());
  } catch (e) {
    process.stderr.write(
      `agent-vault-add-secret: could not list existing windows: ${e.message}\n`,
    );
    return new Set();
  }
}

/**
 * Hyprland tiles the Glimpse window at full size. Chromium sets the window's
 * class and title only after it is mapped, so no Hyprland window rule has
 * anything to match on and the window cannot be floated by rule. Float, size,
 * and centre it ourselves once it appears.
 *
 * Every dispatch names its window explicitly: without a selector these
 * dispatchers act on whichever window happens to be focused.
 */
async function floatOwnWindow(width, height, knownAddresses) {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    await sleep(100);
    const address = (await glimpseWindowAddresses()).find((a) => !knownAddresses.has(a));
    if (!address) continue;
    const target = `window = "address:${address}"`;
    await hyprctl(["dispatch", `hl.dsp.window.float({ action = "set", ${target} })`]);
    await hyprctl(["dispatch", `hl.dsp.window.resize({ x = ${width}, y = ${height}, ${target} })`]);
    await hyprctl(["dispatch", `hl.dsp.window.center({ ${target} })`]);
    return;
  }
}

/**
 * Write one credential into the vault.
 *
 * The value reaches the remote host on stdin and is only interpolated into the
 * remote command's argv, so it never appears in this host's process list.
 * Any error text is redacted before it leaves this function.
 */
function writeCredential(opts, key, value) {
  if (opts.dryRun) {
    return Promise.resolve({ ok: true, message: "dry run — nothing was written" });
  }

  const remote =
    `read -r __v && docker exec ${opts.container} ` +
    `agent-vault vault credential set --vault ${opts.vault} ` +
    `"${key}=$__v"`;

  return new Promise((resolve) => {
    const child = spawn(
      "ssh",
      ["-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o", "ConnectTimeout=25",
       `${opts.ssh_user}@${opts.host}`, remote],
      { stdio: ["pipe", "pipe", "pipe"] },
    );

    let out = "";
    let err = "";
    child.stdout.on("data", (d) => { out += d; });
    child.stderr.on("data", (d) => { err += d; });
    child.on("error", (e) => resolve({ ok: false, message: e.message }));
    child.on("close", (code) => {
      const redact = (s) => (value ? s.split(value).join("<redacted>") : s);
      const text = redact((code === 0 ? out : err || out).trim());
      resolve({ ok: code === 0, message: text.slice(0, 400) });
    });

    child.stdin.end(`${value}\n`);
  });
}

function buildHtml(opts, clipboardAvailable) {
  const vault = escapeHtml(opts.vault);
  const fixedKey = opts.key ? escapeHtml(requireCredentialName(opts.key)) : "";
  const needsName = !fixedKey;
  const subtitle = needsName
    ? `vault <code>${vault}</code>`
    : `credential <code>${fixedKey}</code> &middot; vault <code>${vault}</code>`;
  const nameField = needsName
    ? `
<label for="k">Credential name</label>
<input id="k" type="text" autocomplete="off" spellcheck="false"
       placeholder="e.g. OPENAI_API_KEY" autofocus />
`
    : "";

  return `
<body>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    margin: 0; padding: 20px 22px;
    background: #1e1e2e; color: #cdd6f4;
    -webkit-user-select: none; user-select: none;
  }
  h1 { font-size: 15px; margin: 0 0 3px; font-weight: 600; }
  .sub { font-size: 12px; color: #7f849c; margin-bottom: 16px; }
  .sub code { color: #a6adc8; font-family: ui-monospace, monospace; }
  label { display: block; font-size: 11px; text-transform: uppercase;
          letter-spacing: .06em; color: #7f849c; margin-bottom: 6px; }
  input {
    width: 100%; padding: 10px 12px; font-size: 14px;
    font-family: ui-monospace, monospace;
    background: #11111b; color: #cdd6f4;
    border: 1px solid #313244; border-radius: 8px;
  }
  input:focus { outline: none; border-color: #89b4fa;
                box-shadow: 0 0 0 3px rgba(137,180,250,.15); }
  #k { margin-bottom: 14px; }
  .row { display: flex; gap: 8px; align-items: center; margin-top: 8px; min-height: 16px; }
  .hint { font-size: 11px; color: #6c7086; flex: 1; }
  .link { font-size: 11px; color: #89b4fa; background: none; border: none;
          cursor: pointer; padding: 0; text-decoration: underline; font-family: inherit; }
  .actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 18px; }
  button { padding: 9px 18px; font-size: 13px; border-radius: 8px;
           border: none; cursor: pointer; font-family: inherit; }
  #add { background: #89b4fa; color: #1e1e2e; font-weight: 600; }
  #add:disabled { background: #45475a; color: #7f849c; cursor: default; }
  #cancel { background: #313244; color: #cdd6f4; }
  #status { margin-top: 14px; font-size: 12px; min-height: 16px; line-height: 1.35; }
  .ok { color: #a6e3a1; } .err { color: #f38ba8; } .busy { color: #f9e2af; }
</style>

<h1>Add secret to Agent Vault</h1>
<div class="sub">${subtitle}</div>
${nameField}
<label for="v">Secret value</label>
<input id="v" type="password" autocomplete="off" spellcheck="false"
       placeholder="paste the secret here" ${needsName ? "" : "autofocus"} />

<div class="row">
  <span class="hint" id="hint"></span>
  ${clipboardAvailable ? '<button class="link" id="useclip">use clipboard</button>' : ""}
</div>

<div class="actions">
  <button id="cancel">Cancel</button>
  <button id="add" disabled>Add secret</button>
</div>
<div id="status"></div>

<script>
  var needsName = ${needsName ? "true" : "false"};
  var k = document.getElementById('k');
  var v = document.getElementById('v');
  var add = document.getElementById('add');
  var status = document.getElementById('status');
  var hint = document.getElementById('hint');
  var busy = false;

  function setStatus(text, cls) { status.textContent = text; status.className = cls || ''; }

  function refresh() {
    var named = !needsName || (k && k.value.trim().length > 0);
    var filled = v.value.length > 0;
    add.disabled = !(named && filled) || busy;
    if (filled && !busy) hint.textContent = v.value.length + ' characters';
    else if (!busy) hint.textContent = '${clipboardAvailable ? "Clipboard has content." : "Clipboard looks empty."}';
  }

  if (k) k.addEventListener('input', refresh);
  v.addEventListener('input', refresh);
  v.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !add.disabled) submit();
    if (e.key === 'Escape') cancel();
  });

  function cancel() { if (!busy) window.glimpse.send({ action: 'cancel' }); }

  var clipBtn = document.getElementById('useclip');
  if (clipBtn) {
    clipBtn.addEventListener('click', function () {
      setStatus('Reading clipboard…', 'busy');
      window.glimpse.send({ action: 'readClipboard' });
    });
  }

  document.getElementById('cancel').addEventListener('click', cancel);

  function submit() {
    if (busy || !v.value) return;
    if (needsName && !(k && k.value.trim())) return;
    busy = true; add.disabled = true;
    setStatus('Writing to the vault…', 'busy');
    window.glimpse.send({
      action: 'add',
      key: needsName ? k.value.trim() : undefined,
      value: v.value,
    });
  }
  add.addEventListener('click', submit);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') cancel(); });

  // Node calls back into these.
  window.__receiveClipboard = function (value) {
    if (value) {
      v.value = value;
      refresh();
      setStatus('Loaded from clipboard. Press Add secret to store it.', '');
    } else {
      setStatus('Could not read the clipboard.', 'err');
    }
  };

  window.__reportResult = function (res) {
    busy = false;
    if (res && res.ok) {
      v.value = '';
      setStatus('Added to the vault.', 'ok');
    } else {
      setStatus('Failed: ' + ((res && res.message) || 'unknown error'), 'err');
      refresh();
    }
  };

  refresh();
</script>
</body>`;
}

async function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    process.stderr.write(`${e.message}\n\n${USAGE}`);
    process.exit(2);
  }

  if (opts.help) { process.stdout.write(USAGE); return; }
  try {
    resolveSettings(opts);
    if (opts.key) opts.key = requireCredentialName(opts.key);
    opts.vault = requireSafeToken(opts.vault, "vault");
    opts.container = requireSafeToken(opts.container, "container");
    opts.ssh_user = requireSafeToken(opts.ssh_user, "ssh user");
    opts.host = requireSafeToken(opts.host, "ssh host");
  } catch (e) {
    process.stderr.write(`${e.message}\n\n${USAGE}`);
    process.exit(2);
  }

  if (opts.check) {
    const resolved = SETTINGS.filter((s) => opts[s.key]).map((s) => `${s.key}=${opts[s.key]}`);
    process.stdout.write(`${resolved.join("\n")}\n`);
    return;
  }

  const { open } = await import(resolveGlimpse());
  const clipboard = await readClipboard();

  const width = 470;
  const height = opts.key ? 300 : 360;
  const knownAddresses = await knownGlimpseAddresses();

  const win = open(buildHtml(opts, Boolean(clipboard)), {
    width,
    height,
    title: opts.key ? `Agent Vault — ${opts.key}` : "Agent Vault — add secret",
    floating: true,
  });

  if (process.env.HYPRLAND_INSTANCE_SIGNATURE) {
    floatOwnWindow(width, height, knownAddresses).catch((e) => {
      process.stderr.write(`agent-vault-add-secret: could not float the window: ${e.message}\n`);
    });
  }

  win.on("message", async (data) => {
    if (!data || typeof data !== "object") return;
    switch (data.action) {
      case "readClipboard": {
        const value = await readClipboard();
        win.send(`window.__receiveClipboard(${JSON.stringify(value)})`);
        break;
      }
      case "add": {
        let key;
        try {
          key = requireCredentialName(data.key ?? opts.key);
        } catch (e) {
          win.send(`window.__reportResult(${JSON.stringify({ ok: false, message: e.message })})`);
          break;
        }
        const res = await writeCredential(opts, key, data.value);
        win.send(`window.__reportResult(${JSON.stringify(res)})`);
        if (res.ok) setTimeout(() => win.close(), 1100);
        break;
      }
      case "cancel":
        win.close();
        break;
      default:
        break;
    }
  });
}

main().catch((e) => {
  process.stderr.write(`agent-vault-add-secret: ${e.message}\n`);
  process.exit(1);
});
