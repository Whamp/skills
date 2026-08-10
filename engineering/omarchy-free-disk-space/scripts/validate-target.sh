#!/bin/bash

set -euo pipefail

TARGET=""
EXPECTED_TYPE=""
EXPECTED_SIZE=""
EXPECTED_MTIME=""
EXPECTED_DEVICE=""
EXPECTED_MOUNT=""
DISK_HOME=${OMARCHY_DISK_HOME:-$HOME}

usage() {
  echo "Usage: validate-target.sh --target PATH --type TYPE --size BYTES --mtime EPOCH --device ID --mount TARGET" >&2
}

while (($#)); do
  case "$1" in
    --target) TARGET=${2-}; shift 2 ;;
    --type) EXPECTED_TYPE=${2-}; shift 2 ;;
    --size) EXPECTED_SIZE=${2-}; shift 2 ;;
    --mtime) EXPECTED_MTIME=${2-}; shift 2 ;;
    --device) EXPECTED_DEVICE=${2-}; shift 2 ;;
    --mount) EXPECTED_MOUNT=${2-}; shift 2 ;;
    *) echo "Target validation argument rejected: $1" >&2; usage; exit 2 ;;
  esac
done

[[ -n $TARGET && -n $EXPECTED_TYPE && $EXPECTED_SIZE =~ ^[0-9]+$ &&
   $EXPECTED_MTIME =~ ^[0-9]+$ && $EXPECTED_DEVICE =~ ^[0-9]+$ && -n $EXPECTED_MOUNT ]] || {
  echo "Target validation arguments are incomplete or malformed" >&2
  exit 2
}

[[ $TARGET == /* ]] || {
  echo "Target validation rejected non-absolute path: $(printf '%q' "$TARGET")" >&2
  exit 1
}

check_symlink_components() {
  local path=$1
  local remainder component current="/"
  remainder=${path#/}
  while [[ -n $remainder ]]; do
    if [[ $remainder == */* ]]; then
      component=${remainder%%/*}
      remainder=${remainder#*/}
    else
      component=$remainder
      remainder=""
    fi
    [[ -n $component ]] || continue
    if [[ $current == "/" ]]; then
      current="/$component"
    else
      current="$current/$component"
    fi
    [[ ! -L $current ]] || {
      echo "Target validation rejected symlink component: $(printf '%q' "$current")" >&2
      return 1
    }
  done
}

check_symlink_components "$TARGET"

canonical=$(realpath -e -- "$TARGET" 2>/dev/null || true)
[[ -n $canonical && $canonical == "$TARGET" ]] || {
  echo "Target validation rejected vanished or non-canonical path: $(printf '%q' "$TARGET")" >&2
  exit 1
}

case "$EXPECTED_TYPE" in
  file) [[ -f $TARGET && ! -L $TARGET ]] ;;
  directory) [[ -d $TARGET && ! -L $TARGET ]] ;;
  *) echo "Target validation rejected unsupported type: $EXPECTED_TYPE" >&2; exit 1 ;;
esac || {
  echo "Target validation rejected changed type: $(printf '%q' "$TARGET")" >&2
  exit 1
}

declare -a protected_roots=(
  "/"
  "/home"
  "$DISK_HOME"
  "$DISK_HOME/projects"
  "$DISK_HOME/worktrees"
  "$DISK_HOME/tools"
  "$DISK_HOME/src"
  "$DISK_HOME/evals"
  "$DISK_HOME/utils"
  "$DISK_HOME/work"
  "$DISK_HOME/business"
)

for protected_root in "${protected_roots[@]}"; do
  [[ $TARGET != "$protected_root" ]] || {
    echo "Target validation rejected protected root: $(printf '%q' "$TARGET")" >&2
    exit 1
  }
done

current_mount=$(findmnt -T "$TARGET" -n -o TARGET 2>/dev/null || printf 'unknown')
[[ $current_mount == "$EXPECTED_MOUNT" ]] || {
  echo "Target validation rejected mount change: expected=$EXPECTED_MOUNT actual=$current_mount" >&2
  exit 1
}
[[ $TARGET != "$current_mount" ]] || {
  echo "Target validation rejected mounted filesystem root: $(printf '%q' "$TARGET")" >&2
  exit 1
}

current_device=$(stat -c '%d' -- "$TARGET")
[[ $current_device == "$EXPECTED_DEVICE" ]] || {
  echo "Target validation rejected device change: expected=$EXPECTED_DEVICE actual=$current_device" >&2
  exit 1
}

current_mtime=$(stat -c '%Y' -- "$TARGET")
[[ $current_mtime == "$EXPECTED_MTIME" ]] || {
  echo "Target validation rejected timestamp change: expected=$EXPECTED_MTIME actual=$current_mtime" >&2
  exit 1
}

current_size=$(du -s -B1 --apparent-size -- "$TARGET" 2>/dev/null | awk 'NR==1 {print $1}')
[[ $current_size =~ ^[0-9]+$ ]] || {
  echo "Target validation could not remeasure apparent size" >&2
  exit 1
}

size_delta=$((current_size - EXPECTED_SIZE))
((size_delta < 0)) && size_delta=$((-size_delta))
size_tolerance=$((EXPECTED_SIZE / 20))
((size_tolerance < 65536)) && size_tolerance=65536
((size_delta <= size_tolerance)) || {
  echo "Target validation rejected meaningful size drift: expected=$EXPECTED_SIZE actual=$current_size" >&2
  exit 1
}

printf 'validated %q\n' "$TARGET"
