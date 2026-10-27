# Space accounting

Use this reference for Btrfs, reflinks, snapshots, sparse files, shared package or
container stores, and unexplained differences between directory sizes and free
space. Measure the filesystem under pressure, not an unrelated `/tmp` tmpfs or
root partition.

## Keep four measurements separate

| Measurement | Source | What it establishes |
| --- | --- | --- |
| Apparent file bytes | `du -x -s -B1 --apparent-size PATH` | Logical file-tree size; sparse holes and shared copies can inflate it. |
| Allocated file blocks | `du -x -s -B1 PATH` | Blocks reported for those files; not exclusive ownership or deletion savings. |
| Sharing/compression evidence | Btrfs extent analysis, existing qgroups, `compsize` | Why file-tree totals differ from storage cost; each tool has limits below. |
| Filesystem available bytes | `df -B1 --output=avail PATH`, `btrfs filesystem usage MOUNT` | Available capacity and Btrfs allocation before/after an action. |

The audit's candidate bytes describe potentially affected contents, sometimes an
owning tool's estimate. A prune can retain part of that content. Overlapping
roots, hardlinks, reflinks, and shared Docker layers prevent adding the rows into
a physical-recovery promise. `unknown` is not zero. Provide a reason and a next
read-only check rather than a fabricated estimate.

## Inspect selected Btrfs candidates

Run `scripts/measure.sh PATH [PATH ...]` on the leading candidates, not the whole
home tree. It reads apparent/allocated sizes and, on Btrfs, attempts these bounded
reads without elevation:

```bash
btrfs filesystem du -s --raw "/exact/candidate"
compsize -b -x "/exact/candidate"
```

- **Btrfs `Total / Exclusive / Set shared`:** extent-sharing evidence, not a
  compression-adjusted forecast. Set-shared extents can also be referenced
  outside the set. Do not treat them as exclusively recoverable.
- **`compsize` Disk Usage:** compressed extent cost for the inspected set. Other
  paths or snapshots can still reference those extents, so deleting this set
  need not free that amount.
- **Qgroups:** if already enabled and consistent, inspect referenced/exclusive
  subvolume accounting with `btrfs qgroup show --raw MOUNT`. This is subvolume,
  not arbitrary-directory, evidence. Report warnings, stale accounting, and
  disabled quotas. Do not enable quotas or start a rescan merely to produce a
  cleanup number.

Inspect the actual mount layout and `snapper list-configs` before attributing
home contents to root snapshots. Nested subvolumes are not automatically part of
an ancestor snapshot. Map snapshot paths/IDs through the owning configuration;
keep current and promised rollback points. Summing individual exclusive values
omits extents shared only among snapshots in the deletion batch; it is not a
forecast of that batch's recovery.

If a read needs privileges, report the missing evidence and exact manual command.
Tool absence, permission failure, and timeout mean unavailable evidence, not an
empty tree. The measurement script does not install tools or change the system.

## Reversible removal is not reclamation

`gio trash` normally moves an entry into Trash on the same filesystem. The files
still occupy storage. Report **moved to Trash; planned immediate recovery 0**,
not deleted or freed. List pre-existing Trash contents before asking to empty
it; approval for a new artifact is not approval for everything already there.

For immediate permanent recovery, prefer the owning cleaner for a verified,
reproducible target and obtain approval for its exact scope. The supplied executor
uses Trash for ordinary paths; it does not silently substitute permanent deletion.
Snapshots can still pin blocks after permanent removal. Creating a new snapshot
before cleanup can pin exactly the artifacts intended for removal.

## Verify observed recovery

`apply.sh` measures root, home, approved path mounts, and repeated `--space-path`
locations. Resolve tool-owned storage separately, for example Docker's configured
root; a mount not listed in the measurement is unverified. Compare each mount
individually, never sum subvolume views of the same Btrfs filesystem.

Report the observation, not a causal per-item claim: concurrent writes, open
handles to unlinked files, transaction delay, and subvolume cleanup affect it.
For a large unexplained gap, inspect deleted-but-open files read-only before
proposing a separately approved process restart. After approved snapshot removal,
`btrfs subvolume sync MOUNT` can wait for that deletion; do not use balance,
defragmentation, or profile changes as routine cleanup substitutes.

## Authoritative references

- [Btrfs filesystem measurements](https://btrfs.readthedocs.io/en/latest/btrfs-filesystem.html)
- [Btrfs qgroup accounting](https://btrfs.readthedocs.io/en/latest/btrfs-qgroup.html)
- [Arch `compsize` manual](https://man.archlinux.org/man/extra/compsize/compsize.8.en)
- [Freedesktop Trash specification](https://specifications.freedesktop.org/trash-spec/latest/)
