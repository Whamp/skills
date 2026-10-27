# Cleanup policy

Use this reference when converting audit findings into an approval request or
interpreting an apply result.

## Safety levels

| Level | Meaning | Application rule |
| --- | --- | --- |
| `safe` | Known cache or bounded retention cleanup with an understood consequence | Exact approval still required |
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
| Trash | review | Inspect existing contents, then approve permanent emptying separately; recovery is lost |
| Flatpak unused runtimes | safe | `flatpak uninstall --unused`; runtimes redownload when needed |
| Policy-governed temporary files | safe | `systemd-tmpfiles --clean`; only configured age rules apply |
| Project build caches, outputs, and dependency environments | review | Names are leads; prove ownership, reproducibility, and inactivity before recommending exact targets. Trash releases no space until emptied. |
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

## Decision report

Safety level and recommendation are different: a regenerable artifact can still
be expensive to rebuild or in use. The script's groups are starting points; the
agent resolves the evidence before recommending removal.

| Class | Evidence required / next action |
| --- | --- |
| Recommended | Ownership, disposable contents, inactivity where relevant, and a recovery path are established. Name exact IDs and explain the benefit. |
| Optional | Removal is supported but has a plausible retention purpose, rebuild cost, or permanent-loss choice for the user. |
| Keep | Active use, dirty/unique work, required rollback state, or irreplaceable contents are established. |
| Investigate | Evidence is missing or contradictory. State the smallest read-only check that can resolve it. |

Lead with at most five recommendations on the pressured filesystem. Provide a
complete grouped inventory afterward, not an undifferentiated log dump. Use:

| ID | Exact target / action | File or owner-reported bytes | Physical recovery + basis | Class / evidence | Consequence and recovery |
| --- | --- | ---: | --- | --- | --- |

Show known contents and rebuild/download consequences, not merely a path and
"safe". A stopped or merged project with proven recoverability can have a useful
bulk-cleanup recommendation; a current source directory called `build` cannot.
Do not infer stopped development from commit age or directory mtime alone.

## Omarchy interpretation

Detect commands and source from the active installation: `OMARCHY_PATH`, packaged
`/usr/share/omarchy`, or a legacy `~/.local/share/omarchy` checkout. Read only;
never edit packaged Omarchy files. Record `omarchy version`,
`omarchy version channel`, and `omarchy version branch` when available.

An Omarchy update is its own approved operation. The supported update pipeline
normally creates a Snapper snapshot, pulls Omarchy, updates system and AUR
packages, runs migrations, removes orphans, executes hooks, and evaluates
restart needs. Confirm these steps from the installed source before relying on
them.

Compare the live Snapper configuration with the installed defaults and applied
migrations, not a remote branch or assumed release. Legacy `/home` snapshot
configuration, timeline policy, or retention differences need investigation;
they do not alone prove wasted space. Check update headroom and obtain separate
approval before proposing the supported update/migration path. An update can
create a snapshot and consume more space.

## Space interpretation

Read [space-accounting.md](space-accounting.md) for measurement types, selected
Btrfs/compression reads, snapshot relationships, Trash, and per-filesystem
verification. The executor does not convert apparent size, owning-tool
reclaimability, or successful actions into physical bytes freed.

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
11. planned immediate physical recovery: `0` for a move to Trash, otherwise `unknown`
12. consequence

The manifest contains data, never shell commands. Application rejects stale,
foreign-machine, foreign-boot, malformed, world-readable, symlinked, changed,
protected-root, report-only, high-risk, or unknown-action records.
