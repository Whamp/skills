import { execFile, spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export const CONFIG_PATH = `${
  process.env.XDG_CONFIG_HOME || `${process.env.HOME}/.config`
}/agent-vault-secret/config`;

export const SETTINGS = [
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

/** Parse graphical secret-intake arguments without performing I/O. */
export function parseAddSecretArgs(argv) {
  const opts = { dryRun: false, keys: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const take = () => {
      const value = argv[index + 1];
      if (value === undefined) throw new Error(`${arg} needs a value`);
      index += 1;
      return value;
    };

    if (arg === "--key") opts.keys.push(take());
    else if (arg === "--host") opts.host = take();
    else if (arg === "--user") opts.ssh_user = take();
    else if (arg === "--container") opts.container = take();
    else if (arg === "--vault") opts.vault = take();
    else if (arg === "--proxy-url") opts.proxy_url = take();
    else if (arg === "--dry-run") opts.dryRun = true;
    else if (arg === "--check") opts.check = true;
    else if (arg === "--help" || arg === "-h") opts.help = true;
    else if (arg.startsWith("--key=")) opts.keys.push(arg.slice(6));
    else if (arg.startsWith("--host=")) opts.host = arg.slice(7);
    else if (arg.startsWith("--user=")) opts.ssh_user = arg.slice(7);
    else if (arg.startsWith("--container=")) opts.container = arg.slice(12);
    else if (arg.startsWith("--vault=")) opts.vault = arg.slice(8);
    else if (arg.startsWith("--proxy-url=")) opts.proxy_url = arg.slice(12);
    else throw new Error(`unknown argument: ${arg}`);
  }

  opts.keys = opts.keys.map(requireCredentialName);
  const seen = new Set();
  for (const key of opts.keys) {
    if (seen.has(key)) throw new Error(`credential name repeated: ${key}`);
    seen.add(key);
  }
  return opts;
}

/** Read `key=value` lines, ignoring blanks and comments. */
export function readConfigFile(configPath = CONFIG_PATH) {
  if (!existsSync(configPath)) return {};
  const values = {};
  for (const line of readFileSync(configPath, "utf8").split("\n")) {
    const text = line.trim();
    if (!text || text.startsWith("#")) continue;
    const separator = text.indexOf("=");
    if (separator === -1) continue;
    values[text.slice(0, separator).trim()] = text.slice(separator + 1).trim();
  }
  return values;
}

/** Resolve settings from flags, environment variables, then the config file. */
export function resolveSettings(opts, env = process.env, configPath = CONFIG_PATH) {
  const config = readConfigFile(configPath);
  const missing = [];
  for (const setting of SETTINGS) {
    const value = opts[setting.key] ?? env[setting.env] ?? config[setting.key];
    if (value) opts[setting.key] = value;
    else if (!setting.optional) missing.push(setting);
  }
  if (missing.length) {
    throw new Error(
      [
        "this host is not configured for Agent Vault.",
        "",
        `Add these to ${configPath}:`,
        ...missing.map((setting) => `  ${setting.key}=<${setting.label}>`),
        "",
        `Or pass them as flags, or set ${missing.map((setting) => setting.env).join(", ")}.`,
      ].join("\n"),
    );
  }
  return opts;
}

/** Require the identifier syntax accepted by Agent Vault credential names. */
export function requireCredentialName(name) {
  const value = String(name ?? "").trim();
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(value)) {
    throw new Error(
      "credential name must start with a letter or underscore and contain only " +
        "letters, digits, and underscores",
    );
  }
  return value;
}

/** Require shell-safe consumer configuration tokens. */
export function requireSafeToken(value, label) {
  const text = String(value ?? "").trim();
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(text)) {
    throw new Error(`${label} must be letters, digits, dot, dash, or underscore`);
  }
  return text;
}

export function validateResolvedSettings(opts) {
  opts.vault = requireSafeToken(opts.vault, "vault");
  opts.container = requireSafeToken(opts.container, "container");
  opts.ssh_user = requireSafeToken(opts.ssh_user, "ssh user");
  opts.host = requireSafeToken(opts.host, "ssh host");
  return opts;
}

export const escapeHtml = (value) =>
  String(value).replace(/[&<>"']/g, (character) =>
    ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[character]);

/** Create the immutable state for a fixed sequence of credential names. */
export function createCredentialSequence(keys) {
  if (!Array.isArray(keys) || keys.length === 0) {
    throw new Error("credential sequence needs at least one key");
  }
  return { keys: [...keys], index: 0, complete: false };
}

/** Return the credential currently awaiting a value. */
export function currentCredential(sequence) {
  return {
    key: sequence.keys[sequence.index],
    index: sequence.index,
    count: sequence.keys.length,
  };
}

/** Advance a credential sequence only after a successful write. */
export function applyCredentialWriteResult(sequence, succeeded) {
  if (!succeeded || sequence.complete) return sequence;
  const nextIndex = sequence.index + 1;
  if (nextIndex >= sequence.keys.length) {
    return { ...sequence, complete: true };
  }
  return { ...sequence, index: nextIndex };
}

export function credentialSubtitle({ key, index, count }, vault) {
  if (count === 1) return `credential ${key} · vault ${vault}`;
  return `credential ${index + 1} of ${count}: ${key} · vault ${vault}`;
}

export function credentialButtonLabel({ index, count }) {
  return index + 1 < count ? "Add and continue" : "Add secret";
}

/** Remove a secret from any command output before reporting an error. */
export function redactSecret(text, secret) {
  const value = String(text ?? "");
  return secret ? value.split(secret).join("<redacted>") : value;
}

function clippedErrorText(error) {
  const text = String(error?.stderr || error?.message || error || "unknown error").trim();
  return text.slice(0, 400);
}

/** Verify SSH, the container, and the vault before the human enters a secret. */
export async function preflightVault(opts, exec = execFileAsync) {
  const host = requireSafeToken(opts.host, "ssh host");
  const sshUser = requireSafeToken(opts.ssh_user, "ssh user");
  const container = requireSafeToken(opts.container, "container");
  const vault = requireSafeToken(opts.vault, "vault");
  try {
    await exec(
      "ssh",
      [
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "ConnectTimeout=25",
        `${sshUser}@${host}`,
        "docker",
        "exec",
        container,
        "agent-vault",
        "vault",
        "credential",
        "list",
        "--vault",
        vault,
      ],
      { timeout: 30000 },
    );
  } catch (error) {
    const detail = clippedErrorText(error);
    throw new Error(
      [
        `Agent Vault preflight failed for ${sshUser}@${host}.`,
        `SSH access, container ${container}, and vault ${vault} must work before entering a secret.`,
        detail,
      ]
        .filter(Boolean)
        .join("\n"),
    );
  }
}

/** Write one credential, passing its value only through SSH standard input. */
export function writeCredential(opts, key, value, spawnProcess = spawn) {
  if (opts.dryRun) {
    return Promise.resolve({ ok: true, message: "dry run - nothing was written" });
  }

  const host = requireSafeToken(opts.host, "ssh host");
  const sshUser = requireSafeToken(opts.ssh_user, "ssh user");
  const container = requireSafeToken(opts.container, "container");
  const vault = requireSafeToken(opts.vault, "vault");
  const credentialName = requireCredentialName(key);
  const remote =
    `read -r __v && docker exec ${container} ` +
    `agent-vault vault credential set --vault ${vault} ` +
    `"${credentialName}=$__v"`;

  return new Promise((resolve) => {
    const child = spawnProcess(
      "ssh",
      [
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "ConnectTimeout=25",
        `${sshUser}@${host}`,
        remote,
      ],
      { stdio: ["pipe", "pipe", "pipe"] },
    );

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (data) => {
      stdout += data;
    });
    child.stderr.on("data", (data) => {
      stderr += data;
    });
    child.on("error", (error) => resolve({ ok: false, message: redactSecret(error.message, value) }));
    child.on("close", (code) => {
      const output = (code === 0 ? stdout : stderr || stdout).trim();
      resolve({ ok: code === 0, message: redactSecret(output, value).slice(0, 400) });
    });

    child.stdin.end(`${value}\n`);
  });
}

/** Render the value-entry window for only the current credential. */
export function buildSecretWindowHtml({ vault, credential, clipboardAvailable, needsName }) {
  const fixedCredential = credential
    ? `<span id="credential-progress">${escapeHtml(credentialSubtitle(credential, vault))}</span>`
    : `<span id="credential-progress">vault ${escapeHtml(vault)}</span>`;
  const nameField = needsName
    ? `
<label for="k">Credential name</label>
<input id="k" type="text" autocomplete="off" spellcheck="false"
       placeholder="e.g. OPENAI_API_KEY" autofocus />
`
    : "";
  const buttonLabel = credential ? credentialButtonLabel(credential) : "Add secret";

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
<div class="sub">${fixedCredential}</div>
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
  <button id="add" disabled>${escapeHtml(buttonLabel)}</button>
</div>
<div id="status"></div>

<script>
  var needsName = ${needsName ? "true" : "false"};
  var k = document.getElementById('k');
  var v = document.getElementById('v');
  var add = document.getElementById('add');
  var status = document.getElementById('status');
  var hint = document.getElementById('hint');
  var progress = document.getElementById('credential-progress');
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
  v.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !add.disabled) submit();
    if (event.key === 'Escape') cancel();
  });

  function cancel() { if (!busy) window.glimpse.send({ action: 'cancel' }); }

  var clipBtn = document.getElementById('useclip');
  if (clipBtn) {
    clipBtn.addEventListener('click', function () {
      setStatus('Reading clipboard...', 'busy');
      window.glimpse.send({ action: 'readClipboard' });
    });
  }

  document.getElementById('cancel').addEventListener('click', cancel);

  function submit() {
    if (busy || !v.value) return;
    if (needsName && !(k && k.value.trim())) return;
    busy = true;
    add.disabled = true;
    setStatus('Writing to the vault...', 'busy');
    window.glimpse.send({
      action: 'add',
      key: needsName ? k.value.trim() : undefined,
      value: v.value,
    });
  }
  add.addEventListener('click', submit);
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') cancel();
  });

  window.__receiveClipboard = function (value) {
    if (value) {
      v.value = value;
      refresh();
      setStatus('Loaded from clipboard. Press the add button to store it.', '');
    } else {
      setStatus('Could not read the clipboard.', 'err');
    }
  };

  window.__reportResult = function (result) {
    busy = false;
    if (result && result.ok) {
      v.value = '';
      if (result.next) {
        progress.textContent = result.next.subtitle;
        add.textContent = result.next.buttonLabel;
        setStatus('Added. Enter the next secret.', 'ok');
        refresh();
        v.focus();
      } else {
        setStatus(result.message, 'ok');
      }
    } else {
      setStatus('Failed: ' + ((result && result.message) || 'unknown error'), 'err');
      refresh();
    }
  };

  refresh();
</script>
</body>`;
}
