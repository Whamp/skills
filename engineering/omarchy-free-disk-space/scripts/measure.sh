#!/bin/bash

set -uo pipefail

if (($# == 0)); then
  echo "Usage: measure.sh PATH [PATH ...] (read-only; select candidates, not whole filesystems)" >&2
  exit 2
fi

for requested_path in "$@"; do
  target=$(realpath -e -- "$requested_path" 2>/dev/null) || {
    printf 'Measurement unavailable: %q does not resolve\n' "$requested_path" >&2
    exit 1
  }
  printf '\n## Candidate %q\n' "$target"
  mount_target=$(findmnt -T "$target" -n -o TARGET 2>/dev/null || printf 'unknown')
  fstype=$(findmnt -T "$target" -n -o FSTYPE 2>/dev/null || printf 'unknown')
  printf 'Filesystem: %s (%s)\n' "$mount_target" "$fstype"

  if output=$(timeout 30 du -x -s -B1 --apparent-size -- "$target" 2>/dev/null); then
    printf 'Apparent bytes: %s\n' "$(awk 'NR==1 {print $1}' <<<"$output")"
  else
    echo "Apparent bytes: unknown (unreadable or 30-second limit)"
  fi
  if output=$(timeout 30 du -x -s -B1 -- "$target" 2>/dev/null); then
    printf 'Allocated file blocks (bytes, not exclusive): %s\n' "$(awk 'NR==1 {print $1}' <<<"$output")"
  else
    echo "Allocated file blocks: unknown (unreadable or 30-second limit)"
  fi

  if [[ $fstype == btrfs ]]; then
    echo "Btrfs extent evidence (Total / Exclusive / Set shared; not compressed physical savings):"
    if command -v btrfs >/dev/null 2>&1; then
      if ! timeout 30 btrfs filesystem du -s --raw "$target"; then
        echo "Extent evidence: unknown (permission, tool error, or 30-second limit)"
        printf 'Manual read: sudo btrfs filesystem du -s --raw %q\n' "$target"
      fi
    else
      echo "Extent evidence: unknown (btrfs tool unavailable)"
    fi
    echo "Compression evidence (Disk Usage includes extents that other paths may also reference):"
    if command -v compsize >/dev/null 2>&1; then
      if ! timeout 30 compsize -b -x "$target"; then
        echo "Compression evidence: unknown (permission, tool error, or 30-second limit)"
        printf 'Manual read: sudo compsize -b -x %q\n' "$target"
      fi
    else
      echo "Compression evidence: unknown (compsize unavailable; no installation attempted)"
    fi
  fi
  echo "Physical recovery: unknown until an approved removal is measured on this filesystem."
  echo "Shared extents, snapshots, hardlinks, compression, open files, and metadata affect recovery."
  echo "Moving to Trash normally releases no space; emptying it is a separate permanent action."
done
