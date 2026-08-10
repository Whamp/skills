#!/bin/bash

set -uo pipefail
export GIT_OPTIONAL_LOCKS=0

MODE="audit"
MANIFEST_OUT=""
DISK_HOME=${OMARCHY_DISK_HOME:-$HOME}
PACMAN_CACHE_OVERRIDE=${OMARCHY_DISK_PACMAN_CACHE:-}
COREDUMP_DIR=${OMARCHY_DISK_COREDUMP_DIR:-/var/lib/systemd/coredump}
MANIFEST_MAGIC="omarchy-free-disk-space-manifest-v1"
PACCACHE_KEEP=3
JOURNAL_KEEP_BYTES=$((1024 * 1024 * 1024))
LARGE_FILE_BYTES=$((500 * 1024 * 1024))

declare -a WORKSPACE_ROOTS=()
declare -a ROW_LABELS=()
declare -a ROW_COUNTS=()
declare -a ROW_CURRENT=()
declare -a ROW_RECLAIM=()
declare -a ROW_SAFETY=()
declare -a ROW_MECHANISMS=()
declare -a ROW_CONSEQUENCES=()
declare -a OPTIONAL_MISSING=()
declare -a DETAIL_LINES=()

RECORD_COUNT=0
RECORD_FILE=""
MANIFEST_TEMP=""

usage() {
  echo "Usage: audit.sh [audit|quick|deep] [--workspace-root PATH] [--emit-manifest PATH]" >&2
}

while (($#)); do
  case "$1" in
    audit|quick|deep)
      MODE=$1
      shift
      ;;
    --workspace-root)
      (($# >= 2)) || { usage; exit 2; }
      WORKSPACE_ROOTS+=("$2")
      shift 2
      ;;
    --emit-manifest)
      (($# >= 2)) || { usage; exit 2; }
      MANIFEST_OUT=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Audit argument rejected: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ $MODE == "audit" && -n $MANIFEST_OUT ]]; then
  echo "Audit mode is read-only and cannot emit a manifest" >&2
  exit 2
fi

human_bytes() {
  local bytes=$1
  if [[ $bytes == "unknown" || $bytes == "-" ]]; then
    printf '%s' "$bytes"
  elif command -v numfmt >/dev/null 2>&1; then
    numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null || printf '%sB' "$bytes"
  else
    printf '%sB' "$bytes"
  fi
}

apparent_size_bytes() {
  local target=$1
  local size output
  if ! output=$(du -s -B1 --apparent-size -- "$target" 2>/dev/null); then
    printf 'unknown'
    return
  fi
  size=$(awk 'NR==1 {print $1}' <<<"$output")
  [[ $size =~ ^[0-9]+$ ]] && printf '%s' "$size" || printf 'unknown'
}

count_children() {
  local target=$1
  local count
  count=$(find "$target" -xdev -mindepth 1 -maxdepth 1 -printf '.' 2>/dev/null | wc -c)
  printf '%s' "$count"
}

add_report_row() {
  ROW_LABELS+=("$1")
  ROW_COUNTS+=("$2")
  ROW_CURRENT+=("$3")
  ROW_RECLAIM+=("$4")
  ROW_SAFETY+=("$5")
  ROW_MECHANISMS+=("$6")
  ROW_CONSEQUENCES+=("$7")
}

append_detail() {
  DETAIL_LINES+=("$1")
}

record_missing_tool() {
  local description=$1
  local existing
  for existing in "${OPTIONAL_MISSING[@]}"; do
    [[ $existing != "$description" ]] || return 0
  done
  OPTIONAL_MISSING+=("$description")
}

discover_workspace_roots() {
  local candidate canonical home_mount candidate_mount
  local -a defaults=(
    "$DISK_HOME/projects"
    "$DISK_HOME/worktrees"
    "$DISK_HOME/tools"
    "$DISK_HOME/src"
    "$DISK_HOME/evals"
    "$DISK_HOME/utils"
    "$DISK_HOME/work"
    "$DISK_HOME/business"
  )

  WORKSPACE_ROOTS+=("${defaults[@]}")
  home_mount=$(findmnt -T "$DISK_HOME" -n -o TARGET 2>/dev/null || true)

  declare -A seen=()
  local -a accepted=()
  for candidate in "${WORKSPACE_ROOTS[@]}"; do
    [[ -d $candidate && ! -L $candidate ]] || continue
    canonical=$(realpath -e -- "$candidate" 2>/dev/null || true)
    [[ -n $canonical ]] || continue
    candidate_mount=$(findmnt -T "$canonical" -n -o TARGET 2>/dev/null || true)
    [[ -z $home_mount || $candidate_mount == "$home_mount" ]] || continue
    [[ -z ${seen[$canonical]+x} ]] || continue
    seen[$canonical]=1
    accepted+=("$canonical")
  done
  WORKSPACE_ROOTS=("${accepted[@]}")
}

initialize_manifest() {
  [[ -n $MANIFEST_OUT ]] || return 0
  local parent
  parent=$(dirname -- "$MANIFEST_OUT")
  [[ -d $parent && ! -L $parent ]] || {
    echo "Manifest parent is unsafe: $parent" >&2
    exit 2
  }
  [[ -f $MANIFEST_OUT && ! -L $MANIFEST_OUT &&
     $(stat -c '%u' -- "$MANIFEST_OUT" 2>/dev/null) == "$UID" &&
     $(stat -c '%a' -- "$MANIFEST_OUT" 2>/dev/null) == "600" &&
     ! -s $MANIFEST_OUT ]] || {
    echo "Manifest destination must be a new empty mode-0600 file owned by this user" >&2
    exit 2
  }
  umask 077
  RECORD_FILE=$(mktemp --tmpdir="$parent" .omarchy-free-disk-space.records.XXXXXX)
  MANIFEST_TEMP=$(mktemp --tmpdir="$parent" .omarchy-free-disk-space.manifest.XXXXXX)
  trap '[[ -n ${RECORD_FILE:-} ]] && rm -f -- "$RECORD_FILE"; [[ -n ${MANIFEST_TEMP:-} ]] && rm -f -- "$MANIFEST_TEMP"' EXIT
}

emit_manifest_record() {
  [[ -n $MANIFEST_OUT ]] || return 0
  local category=$1
  local safety=$2
  local action=$3
  local target=$4
  local original_type=$5
  local size=$6
  local reclaim=$7
  local consequence=$8
  local supplied_mtime=${9:-0}
  local canonical mtime device mount_target item_id prefix

  if [[ $original_type == "file" || $original_type == "directory" ]]; then
    canonical=$(realpath -e -- "$target" 2>/dev/null || true)
    [[ -n $canonical ]] || return 0
    target=$canonical
    mtime=$(stat -c '%Y' -- "$target" 2>/dev/null || printf '0')
    device=$(stat -c '%d' -- "$target" 2>/dev/null || printf '0')
    mount_target=$(findmnt -T "$target" -n -o TARGET 2>/dev/null || printf 'unknown')
  else
    mtime=$supplied_mtime
    device=0
    mount_target="tool"
  fi

  RECORD_COUNT=$((RECORD_COUNT + 1))
  [[ $MODE == "quick" ]] && prefix="Q" || prefix="D"
  printf -v item_id '%s%03d' "$prefix" "$RECORD_COUNT"
  printf '%s\0' \
    "$item_id" "$category" "$safety" "$action" "$target" "$original_type" \
    "$size" "$mtime" "$device" "$mount_target" "$reclaim" "$consequence" >>"$RECORD_FILE"
  printf '  %s  %-12s %-11s %q\n' "$item_id" "$safety" "$category" "$target"
}

finalize_manifest() {
  [[ -n $MANIFEST_OUT ]] || return 0
  local machine_id boot_id created_epoch
  machine_id=$(cat /etc/machine-id 2>/dev/null || printf 'unknown')
  boot_id=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || printf 'unknown')
  created_epoch=$(date +%s)

  {
    printf '%s\0' "$MANIFEST_MAGIC" "$created_epoch" "$MODE" "$machine_id" "$boot_id" "$RECORD_COUNT"
    cat -- "$RECORD_FILE"
  } >"$MANIFEST_TEMP"
  chmod 0600 -- "$MANIFEST_TEMP"
  mv -f -- "$MANIFEST_TEMP" "$MANIFEST_OUT"
  MANIFEST_TEMP=""
  rm -f -- "$RECORD_FILE"
  RECORD_FILE=""
}

audit_filesystem_and_omarchy() {
  local used available total omarchy_version omarchy_channel omarchy_branch omarchy_source
  read -r total used available < <(df -B1 --output=size,used,avail / 2>/dev/null | awk 'NR==2 {print $1, $2, $3}')
  total=${total:-unknown}
  used=${used:-unknown}
  available=${available:-unknown}
  add_report_row "Filesystem allocation" "1" "$used" "-" "report-only" \
    "df + btrfs filesystem usage" "Available: $(human_bytes "$available"); total: $(human_bytes "$total")"

  omarchy_version=$(omarchy version 2>/dev/null || printf 'not installed')
  omarchy_channel=$(omarchy version channel 2>/dev/null || printf 'unknown')
  omarchy_branch=$(omarchy version branch 2>/dev/null || printf 'unknown')
  append_detail "Omarchy: version=$omarchy_version channel=$omarchy_channel branch=$omarchy_branch"
  append_detail "Kernel: $(uname -r 2>/dev/null || printf 'unknown')"
  omarchy_source="$DISK_HOME/.local/share/omarchy"
  if [[ -r "$omarchy_source/bin/omarchy-update" && -r "$omarchy_source/bin/omarchy-update-perform" ]]; then
    append_detail "Omarchy update source: $(printf '%q' "$omarchy_source")"
    append_detail "Omarchy update pipeline (installed source): snapshot=$(grep -q 'omarchy-snapshot create' "$omarchy_source/bin/omarchy-update" && echo yes || echo no), migrations=$(grep -q 'omarchy-migrate' "$omarchy_source/bin/omarchy-update-perform" && echo yes || echo no), AUR=$(grep -q 'omarchy-update-aur-pkgs' "$omarchy_source/bin/omarchy-update-perform" && echo yes || echo no), orphans=$(grep -q 'omarchy-update-orphan-pkgs' "$omarchy_source/bin/omarchy-update-perform" && echo yes || echo no)"
  else
    append_detail "Omarchy update source: unavailable; raw Arch upgrades are not proposed"
  fi
}

audit_btrfs_and_snapper() {
  local root_fstype snapshot_count=0 live_limit="unknown" expected_limit="unknown"
  local snapper_status="permission-limited" migration_status="unknown" snapper_csv cleanup_classes timeline_create="unknown"
  root_fstype=$(findmnt -n -o FSTYPE / 2>/dev/null || true)
  if [[ $root_fstype != "btrfs" ]]; then
    add_report_row "Btrfs/Snapper recovery" "0" "0" "unknown" "report-only" \
      "not applicable" "Root filesystem is ${root_fstype:-unknown}"
    return
  fi

  if [[ -r /etc/snapper/configs/root ]]; then
    live_limit=$(awk -F= '$1=="NUMBER_LIMIT" {gsub(/"/,"",$2); print $2}' /etc/snapper/configs/root)
    timeline_create=$(awk -F= '$1=="TIMELINE_CREATE" {gsub(/"/,"",$2); print $2}' /etc/snapper/configs/root)
  fi
  if [[ -r "$DISK_HOME/.local/share/omarchy/default/snapper/root" ]]; then
    expected_limit=$(awk -F= '$1=="NUMBER_LIMIT" {gsub(/"/,"",$2); print $2}' \
      "$DISK_HOME/.local/share/omarchy/default/snapper/root")
  fi
  if snapper_csv=$(snapper -c root --csvout list 2>/dev/null); then
    snapshot_count=$(awk -F, 'NR>1 && $1 != "0" {count++} END {print count+0}' <<<"$snapper_csv")
    cleanup_classes=$(awk -F, 'NR>1 && $1 != "0" {count[$12]++} END {for (class in count) printf "%s=%d ", class, count[class]}' <<<"$snapper_csv")
    snapper_status="readable"
    append_detail "Snapper cleanup classes: ${cleanup_classes:-unknown}"
  elif [[ -r /boot/limine.conf ]]; then
    snapshot_count=$(awk '/comment: [0-9]+ \/ [0-9]+ snapshots/ {print $2; exit}' /boot/limine.conf)
    snapshot_count=${snapshot_count:-0}
    snapper_status="boot-menu evidence only"
  fi

  if [[ -e "$DISK_HOME/.local/state/omarchy/migrations/1776927490.sh" ]]; then
    migration_status="retention migration recorded"
  else
    migration_status="retention migration not recorded"
  fi

  add_report_row "Btrfs/Snapper recovery" "$snapshot_count" "unknown" "unknown" "report-only" \
    "Snapper/Omarchy-supported cleanup only" \
    "Exclusive bytes unknown; live limit=$live_limit expected=$expected_limit; $snapper_status; $migration_status"

  append_detail "Btrfs mounts:"
  while IFS= read -r line; do append_detail "  $line"; done < <(
    findmnt -rn -t btrfs -o TARGET,SOURCE,OPTIONS 2>/dev/null
  )
  append_detail "Block devices:"
  while IFS= read -r line; do append_detail "  $line"; done < <(
    lsblk -e7 -o NAME,TYPE,SIZE,FSTYPE,FSUSE%,MOUNTPOINTS 2>/dev/null
  )
  append_detail "Snapper configurations:"
  while IFS= read -r line; do append_detail "  $line"; done < <(
    snapper list-configs 2>&1
  )
  append_detail "Snapper timers: timeline=$(systemctl is-enabled snapper-timeline.timer 2>/dev/null || true)/$(systemctl is-active snapper-timeline.timer 2>/dev/null || true), cleanup=$(systemctl is-enabled snapper-cleanup.timer 2>/dev/null || true)/$(systemctl is-active snapper-cleanup.timer 2>/dev/null || true)"
  append_detail "Snapper root policy: NUMBER_LIMIT=$live_limit TIMELINE_CREATE=$timeline_create (an enabled timeline timer does not create timeline snapshots when this setting is no)"
  append_detail "Btrfs filesystem usage:"
  while IFS= read -r line; do append_detail "  $line"; done < <(
    btrfs filesystem usage / 2>&1 | sed -n '1,24p'
  )
  if [[ $snapper_status == "permission-limited" || $snapper_status == "boot-menu evidence only" ]]; then
    append_detail "Permission-limited snapshot audit; exact manual reads: sudo snapper -c root list; sudo btrfs subvolume list -t /"
  fi

  if [[ -e /home/.snapshots || -r /etc/snapper/configs/home || $live_limit != "$expected_limit" ]]; then
    append_detail "Retention warning: legacy /home snapshot evidence or a live/default limit mismatch exists. Prefer omarchy update and its installed migration before manual repair."
  fi
}

audit_pacman_cache() {
  local -a cache_dirs=()
  local cache_dir current=0 count=0 reclaim=0 candidate candidate_size
  local raw_size unreadable_dirs=0 consequence

  if [[ -n $PACMAN_CACHE_OVERRIDE ]]; then
    cache_dirs=("$PACMAN_CACHE_OVERRIDE")
  elif command -v pacman-conf >/dev/null 2>&1; then
    mapfile -t cache_dirs < <(pacman-conf CacheDir 2>/dev/null)
  else
    cache_dirs=("/var/cache/pacman/pkg")
  fi

  for cache_dir in "${cache_dirs[@]}"; do
    [[ -d $cache_dir ]] || continue
    raw_size=$(find "$cache_dir" -xdev -maxdepth 1 -type f -name '*.pkg.tar.*' -printf '%s\n' 2>/dev/null |
      awk '{sum += $1} END {printf "%.0f", sum+0}')
    current=$((current + raw_size))
    unreadable_dirs=$((unreadable_dirs + $(find "$cache_dir" -xdev -mindepth 1 -maxdepth 1 -type d ! -readable -printf '.' 2>/dev/null | wc -c)))
    count=$((count + $(find "$cache_dir" -xdev -maxdepth 1 -type f -name '*.pkg.tar.*' -printf '.' 2>/dev/null | wc -c)))
    if command -v paccache >/dev/null 2>&1; then
      while IFS= read -r candidate; do
        [[ -f $candidate ]] || continue
        candidate_size=$(stat -c '%s' -- "$candidate" 2>/dev/null || printf '0')
        reclaim=$((reclaim + candidate_size))
      done < <(paccache -d -k "$PACCACHE_KEEP" -v -c "$cache_dir" 2>/dev/null || true)
      if ((reclaim > 0)) && [[ $raw_size =~ ^[0-9]+$ ]]; then
        emit_manifest_record "pacman-cache" "safe" "paccache-keep-three" "$cache_dir" \
          "directory" "$raw_size" "$reclaim" "Removes cached package versions beyond three"
      fi
    else
      record_missing_tool "paccache (pacman-contrib)"
    fi
  done

  local mechanism="paccache -d/-r -k 3" display_reclaim=$reclaim
  if ! command -v paccache >/dev/null 2>&1; then
    mechanism="install pacman-contrib separately, then paccache -k 3"
    display_reclaim="unknown"
  fi
  consequence="Retains three versions; never uses pacman -Scc"
  ((unreadable_dirs > 0)) && consequence+="; $unreadable_dirs unreadable temporary directories excluded"
  add_report_row "Pacman package cache" "$count" "$current" "$display_reclaim" "safe" "$mechanism" \
    "$consequence"
}

audit_aur_cache() {
  local helper="none" build_dir="" current=0 count=0 package_cache package_size
  if command -v yay >/dev/null 2>&1; then
    helper="yay"
    if command -v jq >/dev/null 2>&1; then
      build_dir=$(yay -Pg 2>/dev/null | jq -r '.buildDir // empty' 2>/dev/null)
    fi
    [[ -n $build_dir ]] || build_dir="$DISK_HOME/.cache/yay"
  elif command -v paru >/dev/null 2>&1; then
    helper="paru"
    build_dir="$DISK_HOME/.cache/paru/clone"
  fi

  if [[ -d $build_dir && ! -L $build_dir ]]; then
    current=$(apparent_size_bytes "$build_dir")
    count=$(find "$build_dir" -xdev -mindepth 1 -maxdepth 1 -type d -printf '.' 2>/dev/null | wc -c)
    while IFS= read -r -d '' package_cache; do
      package_size=$(apparent_size_bytes "$package_cache")
      [[ $package_size =~ ^[0-9]+$ ]] || package_size=0
      emit_manifest_record "aur-cache" "review" "trash-path" "$package_cache" \
        "directory" "$package_size" "$package_size" "AUR sources and build products must be downloaded or rebuilt"
    done < <(find "$build_dir" -xdev -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
  fi
  add_report_row "AUR helper build cache" "$count" "$current" "$current" "review" \
    "Review detected $helper build directory; trash exact package caches" \
    "Sources and compiled packages must be downloaded or rebuilt"
  [[ -n $build_dir ]] && append_detail "AUR cache: helper=$helper path=$(printf '%q' "$build_dir")"
}

parse_journal_bytes() {
  local output amount
  output=$(journalctl --disk-usage 2>/dev/null || true)
  amount=$(sed -nE 's/.*take up ([0-9.]+[KMGTPE]?) in.*/\1/p' <<<"$output")
  [[ -n $amount ]] || { printf 'unknown'; return; }
  numfmt --from=iec "$amount" 2>/dev/null || numfmt --from=si "$amount" 2>/dev/null || printf 'unknown'
}

audit_journal_and_coredumps() {
  local journal_bytes journal_reclaim=0 journal_type="tool"
  local coredump_size=0 coredump_count=0
  journal_bytes=$(parse_journal_bytes)
  if [[ $journal_bytes =~ ^[0-9]+$ ]] && ((journal_bytes > JOURNAL_KEEP_BYTES)); then
    journal_reclaim=$((journal_bytes - JOURNAL_KEEP_BYTES))
    emit_manifest_record "journal" "safe" "journal-vacuum-one-gib" "systemd-journal" \
      "$journal_type" "$journal_bytes" "$journal_reclaim" "Older diagnostic history is removed"
  fi
  add_report_row "Systemd journal" "1" "$journal_bytes" "$journal_reclaim" "safe" \
    "journalctl --vacuum-size=1G" "Older diagnostic history is removed"

  if [[ -d $COREDUMP_DIR ]]; then
    coredump_size=$(apparent_size_bytes "$COREDUMP_DIR")
    coredump_count=$(find "$COREDUMP_DIR" -xdev -maxdepth 1 -type f -printf '.' 2>/dev/null | wc -c)
  fi
  add_report_row "Coredumps" "$coredump_count" "$coredump_size" "$coredump_size" "review" \
    "Review coredump/tmpfiles policy" "Crash diagnostics disappear; report-only in the manifest"
}

audit_user_quick_categories() {
  local target current count
  target="$DISK_HOME/.cache/thumbnails"
  current=0
  count=0
  if [[ -d $target && ! -L $target ]]; then
    current=$(apparent_size_bytes "$target")
    count=$(count_children "$target")
    [[ $current =~ ^[0-9]+$ ]] && ((current > 0)) && emit_manifest_record "thumbnails" "safe" "trash-path" "$target" \
      "directory" "$current" "$current" "Thumbnail previews regenerate"
  fi
  add_report_row "Thumbnails" "$count" "$current" "$current" "safe" \
    "gio trash exact thumbnail directory" "Previews regenerate"

  target="$DISK_HOME/.local/share/Trash"
  current=0
  count=0
  if [[ -d $target && ! -L $target ]]; then
    current=$(apparent_size_bytes "$target")
    count=$(count_children "$target/files")
    [[ $current =~ ^[0-9]+$ ]] && ((current > 0)) && emit_manifest_record "trash" "safe" "empty-home-trash" "$target" \
      "directory" "$current" "$current" "Trashed files become unrecoverable"
  fi
  add_report_row "Trash" "$count" "$current" "$current" "safe" \
    "Purge this home Trash only" "Recovery from Trash is lost"

  if command -v flatpak >/dev/null 2>&1; then
    emit_manifest_record "flatpak" "safe" "flatpak-unused" "flatpak-unused-runtimes" \
      "tool" "0" "unknown" "Unused runtimes may need downloading later"
    add_report_row "Flatpak unused runtimes" "unknown" "unknown" "unknown" "safe" \
      "flatpak uninstall --unused" "Unused runtimes may need downloading later"
  else
    record_missing_tool "flatpak"
    add_report_row "Flatpak unused runtimes" "0" "0" "0" "safe" "not installed" "No action"
  fi

  if command -v systemd-tmpfiles >/dev/null 2>&1; then
    emit_manifest_record "temporary-files" "safe" "tmpfiles-clean" "systemd-tmpfiles-policy" \
      "tool" "0" "unknown" "Configured age policies decide what is removed"
    add_report_row "Policy-governed temporary files" "unknown" "unknown" "unknown" "safe" \
      "systemd-tmpfiles --clean" "Configured age policies decide what is removed"
  else
    record_missing_tool "systemd-tmpfiles"
  fi
}

LANGUAGE_CACHE_TOTAL=0
LANGUAGE_CACHE_COUNT=0

audit_manager_cache() {
  local label=$1
  local command_name=$2
  local action=$3
  local target=$4
  local current=0
  [[ -d $target && ! -L $target ]] || return 1
  current=$(apparent_size_bytes "$target")
  [[ $current =~ ^[0-9]+$ ]] || current=0
  LANGUAGE_CACHE_TOTAL=$((LANGUAGE_CACHE_TOTAL + current))
  LANGUAGE_CACHE_COUNT=$((LANGUAGE_CACHE_COUNT + 1))
  append_detail "Language cache: manager=$command_name apparent=$(human_bytes "$current") path=$(printf '%q' "$target")"
  ((current > 0)) && emit_manifest_record "language-cache" "safe" "$action" "$target" \
    "directory" "$current" "$current" "$label cache; manager decides what remains"
}

audit_language_caches() {
  local cache_path
  if command -v pnpm >/dev/null 2>&1; then
    cache_path=$(pnpm store path 2>/dev/null || true)
    [[ -n $cache_path ]] && audit_manager_cache "pnpm store" "pnpm" "pnpm-store-prune" "$cache_path"
  fi
  if command -v npm >/dev/null 2>&1; then
    cache_path=$(npm config get cache 2>/dev/null || true)
    [[ -n $cache_path ]] && audit_manager_cache "npm cache" "npm" "npm-cache-clean" "$cache_path"
  fi
  if command -v uv >/dev/null 2>&1; then
    cache_path=$(uv cache dir 2>/dev/null || true)
    [[ -n $cache_path ]] && audit_manager_cache "uv cache" "uv" "uv-cache-prune" "$cache_path"
  fi
  if command -v pip >/dev/null 2>&1; then
    cache_path=$(pip cache dir 2>/dev/null || true)
    [[ -n $cache_path ]] && audit_manager_cache "pip cache" "pip" "pip-cache-purge" "$cache_path"
  fi
  if command -v yarn >/dev/null 2>&1; then
    cache_path=$(yarn cache dir 2>/dev/null || true)
    [[ -n $cache_path ]] && audit_manager_cache "Yarn cache" "yarn" "yarn-cache-clean" "$cache_path"
  fi
  if command -v go >/dev/null 2>&1; then
    cache_path=$(go env GOCACHE 2>/dev/null || true)
    [[ -n $cache_path ]] && audit_manager_cache "Go build cache" "go" "go-cache-clean" "$cache_path"
  fi
  add_report_row "Language/package caches" "$LANGUAGE_CACHE_COUNT" "$LANGUAGE_CACHE_TOTAL" "$LANGUAGE_CACHE_TOTAL" "safe" \
    "Owning manager prune/clean command" "Upper-bound estimate; future builds/downloads cost time"
}

classify_build_artifact() {
  case "$(basename -- "$1")" in
    .next|.pytest_cache|__pycache__|.turbo)
      printf 'safe'
      ;;
    node_modules|.venv|venv|target|build|dist)
      printf 'review'
      ;;
    *)
      printf 'report-only'
      ;;
  esac
}

audit_project_artifacts() {
  local root target safety bytes
  local safe_count=0 safe_total=0 review_count=0 review_total=0
  for root in "${WORKSPACE_ROOTS[@]}"; do
    while IFS= read -r -d '' target; do
      safety=$(classify_build_artifact "$target")
      bytes=$(apparent_size_bytes "$target")
      [[ $bytes =~ ^[0-9]+$ ]] || bytes=0
      if [[ $safety == "safe" ]]; then
        safe_count=$((safe_count + 1))
        safe_total=$((safe_total + bytes))
      else
        review_count=$((review_count + 1))
        review_total=$((review_total + bytes))
      fi
      emit_manifest_record "project-artifact" "$safety" "trash-path" "$target" \
        "directory" "$bytes" "$bytes" "Project reinstall or rebuild required"
    done < <(
      find "$root" -xdev -mindepth 2 -maxdepth 7 -type d \
        \( -name .git -o -name .hg -o -name .svn \) -prune -o \
        \( -name .next -o -name .pytest_cache -o -name __pycache__ -o -name .turbo -o \
           -name node_modules -o -name .venv -o -name venv -o -name target -o \
           -name build -o -name dist \) -print0 -prune 2>/dev/null
    )
  done
  add_report_row "Framework build caches" "$safe_count" "$safe_total" "$safe_total" "safe" \
    "gio trash exact directories" "Rebuild required"
  add_report_row "Heavy project artifacts" "$review_count" "$review_total" "$review_total" "review" \
    "gio trash exact directories" "Dependency install or lengthy rebuild required"
}

audit_git_worktrees() {
  local root git_file worktree branch dirty ahead upstream merged registered remote_default
  local count=0 unsafe=0 dirty_count=0 ahead_count=0 no_upstream_count=0
  local unmerged_count=0 detached_count=0 unregistered_count=0
  for root in "${WORKSPACE_ROOTS[@]}"; do
    while IFS= read -r -d '' git_file; do
      worktree=$(dirname -- "$git_file")
      git -C "$worktree" rev-parse --is-inside-work-tree >/dev/null 2>&1 || continue
      count=$((count + 1))
      dirty=$(git -C "$worktree" status --porcelain=v1 --untracked-files=all 2>/dev/null | wc -l)
      ((dirty > 0)) && dirty_count=$((dirty_count + 1))
      branch=$(git -C "$worktree" symbolic-ref --short -q HEAD 2>/dev/null || printf 'detached')
      upstream=$(git -C "$worktree" rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || true)
      ahead="unknown"
      if [[ -n $upstream ]]; then
        ahead=$(git -C "$worktree" rev-list --count '@{upstream}..HEAD' 2>/dev/null || printf 'unknown')
        [[ $ahead =~ ^[0-9]+$ ]] && ((ahead > 0)) && ahead_count=$((ahead_count + 1))
      else
        no_upstream_count=$((no_upstream_count + 1))
      fi
      merged="unknown"
      if [[ $branch == "detached" ]]; then
        detached_count=$((detached_count + 1))
      else
        remote_default=$(git -C "$worktree" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || true)
        if [[ -n $remote_default ]]; then
          if git -C "$worktree" merge-base --is-ancestor HEAD "$remote_default" 2>/dev/null; then
            merged="yes"
          else
            merged="no"
            unmerged_count=$((unmerged_count + 1))
          fi
        fi
      fi
      registered="no"
      if git -C "$worktree" worktree list --porcelain 2>/dev/null |
          sed -n 's/^worktree //p' | grep -Fxq "$worktree"; then
        registered="yes"
      else
        unregistered_count=$((unregistered_count + 1))
      fi
      if ((dirty > 0)) || [[ $ahead != "0" || $merged != "yes" || $registered != "yes" ]]; then
        unsafe=$((unsafe + 1))
      fi
    done < <(find "$root" -xdev -mindepth 2 -maxdepth 6 -type f -name .git -print0 2>/dev/null)
  done
  add_report_row "Git worktrees" "$count" "unknown" "unknown" "report-only" \
    "git worktree inspection; never forced" "$unsafe require retention or more review; repositories are never deleted"
  append_detail "Git worktree summary: total=$count dirty=$dirty_count ahead_of_upstream=$ahead_count no_upstream=$no_upstream_count not_merged_to_origin_default=$unmerged_count detached=$detached_count unregistered=$unregistered_count"
}

audit_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    record_missing_tool "docker"
    add_report_row "Docker containers" "0" "0" "0" "review" "not installed" "No action"
    add_report_row "Docker images/build cache" "0" "0" "0" "review" "not installed" "No action"
    add_report_row "Docker volumes" "0" "unknown" "unknown" "high-risk" "not installed" "No action"
    return
  fi
  if command -v systemctl >/dev/null 2>&1 && ! systemctl is-active --quiet docker.service; then
    add_report_row "Docker stopped containers" "unknown" "unknown" "unknown" "review" \
      "Docker daemon inactive; no socket activation during audit" "Start Docker only with separate approval"
    add_report_row "Docker images/build cache" "unknown" "unknown" "unknown" "review" \
      "Docker daemon inactive; no socket activation during audit" "No estimate claimed"
    add_report_row "Docker volumes" "unknown" "unknown" "unknown" "high-risk" \
      "Docker daemon inactive; report-only" "May contain databases or unique state"
    return
  fi

  local stopped images volumes df_output="unavailable"
  local container_id container_status container_size container_created container_epoch
  local image_id image_size image_created image_epoch build_cache_reclaim="unknown"
  local -a stopped_container_ids=()
  local -a all_image_ids=()
  declare -A used_image_ids=()

  if df_output=$(timeout 15 docker system df 2>/dev/null); then
    append_detail "Docker system df:"
    while IFS= read -r line; do append_detail "  $line"; done <<<"$df_output"
    build_cache_reclaim=$(awk '$1=="Build" && $2=="Cache" {print $NF; exit}' <<<"$df_output")
    build_cache_reclaim=${build_cache_reclaim:-unknown}
  else
    append_detail "Docker system df: timed out or unavailable; no reclaim estimate claimed"
  fi

  mapfile -t stopped_container_ids < <(
    timeout 10 docker ps -aq --filter status=exited --filter status=dead 2>/dev/null
  )
  stopped=${#stopped_container_ids[@]}
  mapfile -t all_image_ids < <(timeout 10 docker image ls -q --no-trunc 2>/dev/null | sort -u)
  images=${#all_image_ids[@]}
  volumes=$(timeout 10 docker volume ls -q 2>/dev/null | wc -l)

  if [[ -n $MANIFEST_OUT ]]; then
    while IFS= read -r container_id; do
      [[ -n $container_id ]] || continue
      image_id=$(timeout 5 docker inspect --format '{{.Image}}' "$container_id" 2>/dev/null || true)
      [[ -n $image_id ]] && used_image_ids[$image_id]=1
    done < <(timeout 10 docker ps -aq 2>/dev/null)

    for container_id in "${stopped_container_ids[@]}"; do
      container_status=$(timeout 5 docker inspect --format '{{.State.Status}}' "$container_id" 2>/dev/null || true)
      [[ $container_status == "exited" || $container_status == "dead" ]] || continue
      container_size=$(timeout 5 docker inspect --size --format '{{.SizeRw}}' "$container_id" 2>/dev/null || printf '0')
      [[ $container_size =~ ^-?[0-9]+$ ]] || container_size=0
      ((container_size < 0)) && container_size=0
      container_created=$(timeout 5 docker inspect --format '{{.Created}}' "$container_id" 2>/dev/null || true)
      container_epoch=$(date -d "$container_created" +%s 2>/dev/null || printf '0')
      emit_manifest_record "docker-container" "review" "docker-container-remove" "$container_id" \
        "tool" "$container_size" "$container_size" "Stopped container writable state and debugging context disappear" "$container_epoch"
    done

    for image_id in "${all_image_ids[@]}"; do
      [[ -z ${used_image_ids[$image_id]+x} ]] || continue
      image_size=$(timeout 5 docker image inspect --format '{{.Size}}' "$image_id" 2>/dev/null || printf '0')
      [[ $image_size =~ ^[0-9]+$ ]] || image_size=0
      image_created=$(timeout 5 docker image inspect --format '{{.Created}}' "$image_id" 2>/dev/null || true)
      image_epoch=$(date -d "$image_created" +%s 2>/dev/null || printf '0')
      emit_manifest_record "docker-image" "review" "docker-image-remove" "$image_id" \
        "tool" "$image_size" "$image_size" "Image may be expensive to rebuild or download" "$image_epoch"
    done

    emit_manifest_record "docker-build-cache" "review" "docker-builder-prune" "docker-build-cache" \
      "tool" "0" "$build_cache_reclaim" "Unused build layers disappear and may be expensive to recreate"
  fi

  add_report_row "Docker stopped containers" "$stopped" "unknown" "unknown" "review" \
    "Inspect exact containers, then docker container rm" "Writable layers and debugging state disappear"
  add_report_row "Docker images/build cache" "$images total" "unknown" "unknown" "review" \
    "Inspect unused images and builder cache separately" "Unused count unknown; images may be expensive to rebuild/download"
  add_report_row "Docker volumes" "$volumes" "unknown" "unknown" "high-risk" \
    "report-only; inspect every volume" "May contain databases or unique state"
  emit_manifest_record "docker-volumes" "high-risk" "none" "docker-volumes" \
    "tool" "0" "unknown" "Never part of blanket approval"
}

audit_downloads_logs_models_and_apps() {
  local target bytes
  local downloads_count=0 downloads_total=0 logs_count=0 logs_total=0
  local models_count=0 models_total=0 apps_count=0 apps_total=0
  local -a model_roots=(
    "$DISK_HOME/.cache/huggingface"
    "$DISK_HOME/.ollama"
    "$DISK_HOME/.cache/llama.cpp"
    "$DISK_HOME/.cache/vllm"
    "$DISK_HOME/.lmstudio"
    "$DISK_HOME/.local/share/lmstudio"
    "$DISK_HOME/.unsloth"
    "$DISK_HOME/models"
    "$DISK_HOME/Models"
    "$DISK_HOME/datasets"
    "$DISK_HOME/Datasets"
  )

  if [[ -d "$DISK_HOME/Downloads" ]]; then
    while IFS= read -r -d '' target; do
      bytes=$(stat -c '%s' -- "$target" 2>/dev/null || printf '0')
      downloads_count=$((downloads_count + 1))
      downloads_total=$((downloads_total + bytes))
      emit_manifest_record "downloads" "review" "trash-path" "$target" "file" "$bytes" "$bytes" \
        "Downloaded file becomes recoverable only from Trash"
    done < <(find "$DISK_HOME/Downloads" -xdev -maxdepth 2 -type f -size +"$((LARGE_FILE_BYTES / 1024))"k -print0 2>/dev/null)
  fi
  add_report_row "Large Downloads/installers" "$downloads_count" "$downloads_total" "$downloads_total" "review" \
    "gio trash each approved file" "May be unique or costly to download again"

  for target in "$DISK_HOME/.local/state" "$DISK_HOME/.cache"; do
    [[ -d $target ]] || continue
    while IFS= read -r -d '' target; do
      bytes=$(stat -c '%s' -- "$target" 2>/dev/null || printf '0')
      logs_count=$((logs_count + 1))
      logs_total=$((logs_total + bytes))
    done < <(find "$target" -xdev -type f \( -name '*.log' -o -name '*.log.*' \) -mtime +30 -size +50M -print0 2>/dev/null)
  done
  add_report_row "Old application logs" "$logs_count" "$logs_total" "$logs_total" "review" \
    "Review individually; prefer owning policy" "Diagnostics disappear; report-only in the manifest"

  for target in "${model_roots[@]}"; do
    [[ -e $target && ! -L $target ]] || continue
    bytes=$(apparent_size_bytes "$target")
    [[ $bytes =~ ^[0-9]+$ ]] || bytes=0
    models_count=$((models_count + 1))
    models_total=$((models_total + bytes))
    emit_manifest_record "models-datasets" "high-risk" "none" "$target" "directory" "$bytes" "unknown" \
      "Model weights or datasets may be expensive or impossible to reproduce"
  done
  add_report_row "AI models and datasets" "$models_count" "$models_total" "unknown" "high-risk" \
    "report-only; identify exact model/dataset first" "Weights and datasets may be costly or unique"

  if [[ -d "$DISK_HOME/.cache" ]]; then
    while IFS= read -r -d '' target; do
      case "$target" in
        "$DISK_HOME/.cache/yay"|"$DISK_HOME/.cache/thumbnails"|"$DISK_HOME/.cache/huggingface"|"$DISK_HOME/.cache/uv"|"$DISK_HOME/.cache/pip"|"$DISK_HOME/.cache/go-build")
          continue
          ;;
      esac
      bytes=$(apparent_size_bytes "$target")
      [[ $bytes =~ ^[0-9]+$ ]] || bytes=0
      ((bytes >= 100 * 1024 * 1024)) || continue
      apps_count=$((apps_count + 1))
      apps_total=$((apps_total + bytes))
    done < <(find "$DISK_HOME/.cache" -xdev -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)
  fi
  add_report_row "Large/unknown application caches" "$apps_count" "$apps_total" "unknown" "report-only" \
    "Establish owning application and supported cleanup" "A directory named cache may still contain state"
}

audit_orphans_and_kernels() {
  local orphan_count=0 kernel_count=0 running installed boot_count=0 orphan_list=""
  if command -v pacman >/dev/null 2>&1; then
    orphan_list=$(pacman -Qdtq 2>/dev/null || true)
    orphan_count=$(grep -c . <<<"$orphan_list")
    kernel_count=$(pacman -Qq 2>/dev/null | grep -Ec '^(linux|linux-lts|linux-zen|linux-hardened|linux-cachyos)$' || true)
  fi
  if ((orphan_count > 0)); then
    append_detail "Orphan package list: $(tr '\n' ' ' <<<"$orphan_list")"
  else
    append_detail "Orphan package list: none"
  fi
  if [[ -x "$DISK_HOME/.local/share/omarchy/bin/omarchy-update-orphan-pkgs" ]]; then
    add_report_row "Orphan packages" "$orphan_count" "unknown" "unknown" "report-only" \
      "Prefer installed omarchy update orphan step" "Package removal is a separate approved maintenance action"
  else
    add_report_row "Orphan packages" "$orphan_count" "unknown" "unknown" "report-only" \
      "Review explicit pacman -Qdtq list, then separately approve pacman -Rns" "No query-to-removal command substitution"
  fi

  running=$(uname -r 2>/dev/null || printf 'unknown')
  installed=$(find /usr/lib/modules -mindepth 1 -maxdepth 1 -type d -printf '%f ' 2>/dev/null || true)
  [[ -r /boot/limine.conf ]] && boot_count=$(grep -c 'comment: Kernel version:' /boot/limine.conf 2>/dev/null || true)
  add_report_row "Installed kernels" "$kernel_count" "unknown" "unknown" "report-only" \
    "Compare packages, running kernel, and boot entries" "Running=$running; modules=${installed:-unknown}; boot entries=$boot_count"
}

audit_optional_tool_inventory() {
  local tool missing_description
  for tool in dua dust paccache flatpak docker journalctl gio pacman snapper btrfs yay paru shellcheck jq; do
    if command -v "$tool" >/dev/null 2>&1; then
      append_detail "Tool: $tool=$(command -v "$tool")"
    else
      case "$tool" in
        yay|paru)
          ;;
        paccache)
          record_missing_tool "paccache (pacman-contrib)"
          ;;
        *)
          missing_description=$tool
          record_missing_tool "$missing_description"
          ;;
      esac
    fi
  done
  if ! command -v yay >/dev/null 2>&1 && ! command -v paru >/dev/null 2>&1; then
    record_missing_tool "AUR helper (yay/paru)"
  fi
}

print_report() {
  local i current reclaim
  echo "# Omarchy disk-space ${MODE} report"
  echo
  echo "| Category | Items | Current size | Estimated reclaimable | Safety | Mechanism | Consequence |"
  echo "| --- | ---: | ---: | ---: | --- | --- | --- |"
  for ((i = 0; i < ${#ROW_LABELS[@]}; i++)); do
    current=$(human_bytes "${ROW_CURRENT[$i]}")
    reclaim=$(human_bytes "${ROW_RECLAIM[$i]}")
    printf '| %s | %s | %s | %s | %s | %s | %s |\n' \
      "${ROW_LABELS[$i]}" "${ROW_COUNTS[$i]}" "$current" "$reclaim" \
      "${ROW_SAFETY[$i]}" "${ROW_MECHANISMS[$i]}" "${ROW_CONSEQUENCES[$i]}"
  done
  echo
  echo "Measurement note: directory values are apparent sizes. Filesystem values are allocated/available bytes. Snapshot-exclusive usage is unknown unless reliable extent or qgroup data is available."
  echo
  echo "## Environment details"
  for i in "${DETAIL_LINES[@]}"; do
    printf '%s\n' "$i"
  done
  if ((${#OPTIONAL_MISSING[@]})); then
    echo
    printf 'Optional tools unavailable: '
    for ((i = 0; i < ${#OPTIONAL_MISSING[@]}; i++)); do
      ((i > 0)) && printf ', '
      printf '%s' "${OPTIONAL_MISSING[$i]}"
    done
    printf '\n'
  fi
  if [[ -n $MANIFEST_OUT ]]; then
    echo
    echo "Manifest: $MANIFEST_OUT"
    echo "Manifest expires 15 minutes after creation and accepts exact item IDs only."
  fi
}

discover_workspace_roots
initialize_manifest

if [[ -n $MANIFEST_OUT ]]; then
  echo "Plan items:"
fi

audit_filesystem_and_omarchy
audit_optional_tool_inventory
audit_btrfs_and_snapper
audit_pacman_cache
audit_aur_cache
audit_journal_and_coredumps
audit_user_quick_categories
audit_language_caches

if [[ $MODE == "audit" || $MODE == "deep" ]]; then
  audit_project_artifacts
  audit_git_worktrees
  audit_docker
  audit_downloads_logs_models_and_apps
  audit_orphans_and_kernels
fi

finalize_manifest
print_report
