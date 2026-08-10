# Cleanup policy

Use this reference when converting audit findings into an approval request or
interpreting an apply result.

## Safety levels

| Level | Meaning | Application rule |
| --- | --- | --- |
| `safe` | Deterministically regenerable and removable through its owning tool | Exact approval still required |
| `review` | Probably regenerable, with rebuild time or inconvenience | Approve each item or narrow category |
| `high-risk` | May contain unique data or impair recovery | Keep report-only unless the user names the exact item and consequence |
| `report-only` | The skill never removes it automatically | Explain the supported manual workflow |

## Category policy

| Category | Default | Mechanism and consequence |
| --- | --- | --- |
| Pacman versions beyond retention | safe | `paccache -r -k 3`; older rollback packages disappear |
| Yay/Paru build caches | review | Review the detected build directory; rebuilding/redownloading may be slow |
| Journal archives | safe | `journalctl --vacuum-size=1G`; older diagnostics disappear |
| Language caches | safe | Manager command such as `pnpm store prune`, `uv cache prune`, `pip cache purge`, or `go clean -cache` |
| Thumbnails | safe | `gio trash`; previews regenerate |
| Trash | safe | Purge the exact home Trash tree; recovery is lost |
| Flatpak unused runtimes | safe | `flatpak uninstall --unused`; runtimes redownload when needed |
| Policy-governed temporary files | safe | `systemd-tmpfiles --clean`; only configured age rules apply |
| `.next`, `.pytest_cache`, `__pycache__`, `.turbo` | safe | Trash exact directory; project rebuild required |
| `node_modules`, virtual environments, Rust `target`, `build`, `dist` | review | Trash exact directory; dependency install or build required |
| Browser and large application caches | review | Report first; browser profiles and application state remain report-only |
| Large Downloads and old installers | review | Trash only the individually approved file |
| Old logs and coredumps | review | Prefer journal/coredump policy; diagnostics disappear |
| Docker stopped containers, unused images, build cache | review | Present separately; downloads/builds may be expensive |
| Docker volumes | high-risk | Report-only; may contain databases or unique state |
| Git repositories and worktrees | high-risk | Report-only until Git safety checks prove no unique work |
| Snapper snapshots | report-only | Use Snapper/Omarchy support; rollback points are lost on deletion |
| Installed kernels | report-only | Compare running kernel, installed packages, and boot entries |
| Orphan packages | report-only | Prefer installed Omarchy’s update orphan step; otherwise approve an explicit package list |
| Models and datasets | high-risk | Report-only; weights may be expensive or impossible to reproduce |
| `/etc`, documents, media, databases, configuration, unknown directories | report-only | Establish ownership and purpose before proposing anything |

## Omarchy interpretation

Detect commands and source from the installed checkout, usually
`~/.local/share/omarchy`. Record `omarchy version`, `omarchy version channel`,
and `omarchy version branch` when available.

An Omarchy update is its own approved operation. The supported update pipeline
normally creates a Snapper snapshot, pulls Omarchy, updates system and AUR
packages, runs migrations, removes orphans, executes hooks, and evaluates
restart needs. Confirm these steps from the installed source before relying on
them.

For current Omarchy 3.x retention, compare the live Snapper root config with
the installed default and inspect the applied migration state. Evidence of a
legacy `/home` Snapper config, `/home/.snapshots`, timeline snapshots, quotas,
or a retention value above the installed default may indicate an incomplete
old migration. Recommend the supported `omarchy update`/migration path before
manual repair.

## Btrfs interpretation

`du` reports file-tree size and shared extents can be counted in more than one
tree. `df` reports filesystem allocation visible to applications.
`btrfs filesystem usage` reports device allocation and estimated free space.
Snapshot-exclusive usage requires qgroup data or an explicit extent analysis;
if that data is absent or quotas are disabled, report the exclusive amount as
unknown.

Recently removed files may remain referenced by snapshots. Btrfs may also
reclaim space asynchronously. Re-run `df` and `btrfs filesystem usage` after
approved cleanup; do not promise that summed directory estimates equal the
measured free-space increase.

## Manifest schema

The binary manifest uses NUL-delimited UTF-8 fields so Linux filenames may
contain spaces, newlines, glob characters, or leading dashes.

Header fields:

1. literal `omarchy-free-disk-space-manifest-v1`
2. creation epoch
3. mode (`quick` or `deep`)
4. `/etc/machine-id`
5. current boot ID
6. record count

Each record contains 12 fields:

1. item ID
2. category
3. safety level
4. allowlisted action
5. exact target
6. original type
7. apparent size in bytes
8. modification epoch
9. device ID
10. containing mount target
11. estimated reclaimable bytes
12. consequence

The manifest contains data, never shell commands. Application rejects stale,
foreign-machine, foreign-boot, malformed, world-readable, symlinked, changed,
protected-root, report-only, high-risk, or unknown-action records.
