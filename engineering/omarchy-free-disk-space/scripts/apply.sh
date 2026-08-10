#!/bin/bash

set -uo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
MANIFEST_MAGIC="omarchy-free-disk-space-manifest-v1"
MAX_MANIFEST_AGE=900
MANIFEST=""
declare -a APPROVED_IDS=()
declare -A APPROVED_SET=()
declare -A SEEN_APPROVED=()

usage() {
  echo "Usage: apply.sh --manifest PATH --approve ITEM_ID [--approve ITEM_ID ...]" >&2
}

while (($#)); do
  case "$1" in
    --manifest)
      MANIFEST=${2-}
      shift 2
      ;;
    --approve)
      APPROVED_IDS+=("${2-}")
      shift 2
      ;;
    --all|--approve-all)
      echo "Blanket approval is intentionally unsupported; name exact item IDs" >&2
      exit 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Apply argument rejected: $1" >&2
      usage
      exit 2
      ;;
  esac
done

[[ -n $MANIFEST && ${#APPROVED_IDS[@]} -gt 0 ]] || {
  echo "Application requires a manifest and at least one exact approved item ID" >&2
  usage
  exit 2
}

for item_id in "${APPROVED_IDS[@]}"; do
  [[ $item_id =~ ^[QD][0-9]{3}$ ]] || {
    echo "Invalid approval item ID: $item_id" >&2
    exit 2
  }
  APPROVED_SET[$item_id]=1
done

[[ -f $MANIFEST && ! -L $MANIFEST ]] || {
  echo "Manifest is missing, not regular, or symlinked" >&2
  exit 1
}
manifest_owner=$(stat -c '%u' -- "$MANIFEST")
manifest_mode=$(stat -c '%a' -- "$MANIFEST")
[[ $manifest_owner == "$UID" && $manifest_mode == "600" ]] || {
  echo "Manifest ownership or mode rejected: owner=$manifest_owner mode=$manifest_mode" >&2
  exit 1
}

mapfile -d '' -t fields <"$MANIFEST"
((${#fields[@]} >= 6)) || {
  echo "Manifest header is truncated" >&2
  exit 1
}

magic=${fields[0]}
created_epoch=${fields[1]}
mode=${fields[2]}
machine_id=${fields[3]}
boot_id=${fields[4]}
record_count=${fields[5]}

[[ $magic == "$MANIFEST_MAGIC" && $created_epoch =~ ^[0-9]+$ &&
   $mode =~ ^(quick|deep)$ && $record_count =~ ^[0-9]+$ ]] || {
  echo "Manifest header is malformed" >&2
  exit 1
}

current_machine_id=$(cat /etc/machine-id 2>/dev/null || printf 'unknown')
current_boot_id=$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || printf 'unknown')
[[ $machine_id == "$current_machine_id" && $boot_id == "$current_boot_id" ]] || {
  echo "Manifest belongs to another machine or boot" >&2
  exit 1
}

now_epoch=$(date +%s)
manifest_age=$((now_epoch - created_epoch))
((manifest_age >= 0 && manifest_age <= MAX_MANIFEST_AGE)) || {
  echo "Manifest is stale or has a future timestamp: age=${manifest_age}s" >&2
  exit 1
}

record_fields=$(( ${#fields[@]} - 6 ))
((record_fields == record_count * 12)) || {
  echo "Manifest record count does not match its payload" >&2
  exit 1
}

declare -A MANIFEST_ITEM_IDS=()
expected_prefix="D"
[[ $mode == "quick" ]] && expected_prefix="Q"
for ((record_index = 0; record_index < record_count; record_index++)); do
  base=$((6 + record_index * 12))
  item_id=${fields[$base]}
  category=${fields[$((base + 1))]}
  safety=${fields[$((base + 2))]}
  action=${fields[$((base + 3))]}
  original_type=${fields[$((base + 5))]}
  size=${fields[$((base + 6))]}
  mtime=${fields[$((base + 7))]}
  device=${fields[$((base + 8))]}
  mount_target=${fields[$((base + 9))]}
  reclaim=${fields[$((base + 10))]}

  [[ $item_id =~ ^${expected_prefix}[0-9]{3}$ && -n $category &&
     $safety =~ ^(safe|review|high-risk|report-only)$ &&
     $original_type =~ ^(file|directory|tool)$ &&
     $size =~ ^[0-9]+$ && $mtime =~ ^[0-9]+$ && $device =~ ^[0-9]+$ &&
     -n $mount_target && $reclaim =~ ^([0-9]+|unknown)$ ]] || {
    echo "Manifest record schema rejected at index $record_index" >&2
    exit 1
  }
  [[ -z ${MANIFEST_ITEM_IDS[$item_id]+x} ]] || {
    echo "Manifest contains duplicate item ID: $item_id" >&2
    exit 1
  }
  MANIFEST_ITEM_IDS[$item_id]=1
  case "$action" in
    trash-path|empty-home-trash|paccache-keep-three|journal-vacuum-one-gib|\
    flatpak-unused|tmpfiles-clean|pnpm-store-prune|npm-cache-clean|\
    uv-cache-prune|pip-cache-purge|yarn-cache-clean|go-cache-clean|\
    docker-container-remove|docker-image-remove|docker-builder-prune|none)
      ;;
    *)
      echo "Manifest contains unknown action: $action" >&2
      exit 1
      ;;
  esac
  if [[ $safety == "high-risk" || $safety == "report-only" ]]; then
    [[ $action == "none" ]] || {
      echo "Manifest gives an executable action to a protected safety level: $item_id" >&2
      exit 1
    }
  fi
done

before_available=$(df -B1 --output=avail / 2>/dev/null | awk 'NR==2 {print $1}')
before_available=${before_available:-unknown}
success_count=0
failure_count=0

run_root_action() {
  if ((EUID != 0)); then
    printf 'requires elevation; exact manual command: sudo --' >&2
    printf ' %q' "$@" >&2
    printf '\n' >&2
    return 77
  fi
  "$@"
}

validate_tool_target() {
  local action=$1
  local target=$2
  local expected_size=$3
  local expected_mtime=$4
  local current_size current_created current_mtime current_status container_id referenced_image
  local size_delta size_tolerance
  case "$action:$target" in
    flatpak-unused:flatpak-unused-runtimes|\
    tmpfiles-clean:systemd-tmpfiles-policy)
      return 0
      ;;
    journal-vacuum-one-gib:systemd-journal)
      current_size=$(journalctl --disk-usage 2>/dev/null |
        sed -nE 's/.*take up ([0-9.]+[KMGTPE]?) in.*/\1/p')
      current_size=$(numfmt --from=iec "$current_size" 2>/dev/null || printf 'unknown')
      [[ $current_size =~ ^[0-9]+$ && $expected_size =~ ^[0-9]+$ ]] || return 1
      size_delta=$((current_size - expected_size))
      ((size_delta < 0)) && size_delta=$((-size_delta))
      size_tolerance=$((expected_size / 20))
      ((size_tolerance < 67108864)) && size_tolerance=67108864
      ((size_delta <= size_tolerance))
      ;;
    docker-container-remove:*)
      [[ $target =~ ^[a-f0-9]{12,64}$ ]] || return 1
      current_status=$(docker inspect --format '{{.State.Status}}' -- "$target" 2>/dev/null || true)
      [[ $current_status == "exited" || $current_status == "dead" ]] || return 1
      current_size=$(docker inspect --size --format '{{.SizeRw}}' -- "$target" 2>/dev/null || printf 'unknown')
      [[ $current_size =~ ^-?[0-9]+$ && $expected_size =~ ^[0-9]+$ ]] || return 1
      ((current_size < 0)) && current_size=0
      current_created=$(docker inspect --format '{{.Created}}' -- "$target" 2>/dev/null || true)
      current_mtime=$(date -d "$current_created" +%s 2>/dev/null || printf 'unknown')
      [[ $current_mtime == "$expected_mtime" && $current_size == "$expected_size" ]]
      ;;
    docker-image-remove:sha256:*)
      docker image inspect -- "$target" >/dev/null 2>&1 || return 1
      current_size=$(docker image inspect --format '{{.Size}}' -- "$target" 2>/dev/null || printf 'unknown')
      current_created=$(docker image inspect --format '{{.Created}}' -- "$target" 2>/dev/null || true)
      current_mtime=$(date -d "$current_created" +%s 2>/dev/null || printf 'unknown')
      [[ $current_size == "$expected_size" && $current_mtime == "$expected_mtime" ]] || return 1
      while IFS= read -r container_id; do
        [[ -n $container_id ]] || continue
        referenced_image=$(docker inspect --format '{{.Image}}' -- "$container_id" 2>/dev/null || true)
        [[ $referenced_image != "$target" ]] || return 1
      done < <(docker ps -aq 2>/dev/null)
      return 0
      ;;
    docker-builder-prune:docker-build-cache)
      command -v docker >/dev/null 2>&1 &&
        (! command -v systemctl >/dev/null 2>&1 || systemctl is-active --quiet docker.service)
      ;;
    *)
      echo "Tool target/action pair rejected: $action / $target" >&2
      return 1
      ;;
  esac
}

run_allowlisted_action() {
  local action=$1
  local target=$2
  case "$action" in
    trash-path)
      command -v gio >/dev/null 2>&1 || {
        echo "gio is unavailable; permanent deletion was not attempted" >&2
        return 69
      }
      gio trash -- "$target"
      ;;
    empty-home-trash)
      [[ -d "$target/files" && ! -L "$target/files" &&
         -d "$target/info" && ! -L "$target/info" ]] || {
        echo "Home Trash structure changed" >&2
        return 1
      }
      find "$target/files" -xdev -mindepth 1 -delete &&
        find "$target/info" -xdev -mindepth 1 -delete
      ;;
    paccache-keep-three)
      command -v paccache >/dev/null 2>&1 || return 69
      run_root_action paccache -r -k 3 -c "$target"
      ;;
    journal-vacuum-one-gib)
      run_root_action journalctl --vacuum-size=1G
      ;;
    flatpak-unused)
      command -v flatpak >/dev/null 2>&1 || return 69
      flatpak uninstall --unused --noninteractive
      ;;
    tmpfiles-clean)
      command -v systemd-tmpfiles >/dev/null 2>&1 || return 69
      run_root_action systemd-tmpfiles --clean
      ;;
    pnpm-store-prune)
      command -v pnpm >/dev/null 2>&1 || return 69
      pnpm --store-dir "$target" store prune
      ;;
    npm-cache-clean)
      command -v npm >/dev/null 2>&1 || return 69
      npm --cache "$target" cache clean --force
      ;;
    uv-cache-prune)
      command -v uv >/dev/null 2>&1 || return 69
      UV_CACHE_DIR="$target" uv cache prune
      ;;
    pip-cache-purge)
      command -v pip >/dev/null 2>&1 || return 69
      pip cache --cache-dir "$target" purge
      ;;
    yarn-cache-clean)
      command -v yarn >/dev/null 2>&1 || return 69
      yarn cache clean --cache-folder "$target"
      ;;
    go-cache-clean)
      command -v go >/dev/null 2>&1 || return 69
      GOCACHE="$target" go clean -cache
      ;;
    docker-container-remove)
      command -v docker >/dev/null 2>&1 || return 69
      docker container rm -- "$target"
      ;;
    docker-image-remove)
      command -v docker >/dev/null 2>&1 || return 69
      docker image rm -- "$target"
      ;;
    docker-builder-prune)
      command -v docker >/dev/null 2>&1 || return 69
      docker builder prune --force
      ;;
    none)
      echo "Report-only action cannot be applied" >&2
      return 64
      ;;
    *)
      echo "Unknown action rejected: $action" >&2
      return 64
      ;;
  esac
}

echo "Disk available before: $before_available bytes"

for ((record_index = 0; record_index < record_count; record_index++)); do
  base=$((6 + record_index * 12))
  item_id=${fields[$base]}
  category=${fields[$((base + 1))]}
  safety=${fields[$((base + 2))]}
  action=${fields[$((base + 3))]}
  target=${fields[$((base + 4))]}
  original_type=${fields[$((base + 5))]}
  size=${fields[$((base + 6))]}
  mtime=${fields[$((base + 7))]}
  device=${fields[$((base + 8))]}
  mount_target=${fields[$((base + 9))]}
  reclaim=${fields[$((base + 10))]}
  consequence=${fields[$((base + 11))]}

  [[ -n ${APPROVED_SET[$item_id]+x} ]] || continue
  SEEN_APPROVED[$item_id]=1
  printf '\n[%s] %s (%s): %q\n' "$item_id" "$category" "$safety" "$target"
  printf 'Estimated reclaimable: %s bytes\n' "$reclaim"
  printf 'Consequence: %s\n' "$consequence"

  if [[ $safety == "high-risk" || $safety == "report-only" || $action == "none" ||
        $category == "docker-volumes" || $category == "models-datasets" ]]; then
    echo "Result: REJECTED — policy keeps this item report-only"
    failure_count=$((failure_count + 1))
    continue
  fi

  if [[ $original_type == "file" || $original_type == "directory" ]]; then
    if ! "$SCRIPT_DIR/validate-target.sh" \
      --target "$target" \
      --type "$original_type" \
      --size "$size" \
      --mtime "$mtime" \
      --device "$device" \
      --mount "$mount_target"; then
      echo "Result: REJECTED — target revalidation failed"
      failure_count=$((failure_count + 1))
      continue
    fi
  elif [[ $original_type == "tool" ]]; then
    if ! validate_tool_target "$action" "$target" "$size" "$mtime"; then
      echo "Result: REJECTED — tool target revalidation failed"
      failure_count=$((failure_count + 1))
      continue
    fi
  else
    echo "Result: REJECTED — unknown original type"
    failure_count=$((failure_count + 1))
    continue
  fi

  if run_allowlisted_action "$action" "$target"; then
    echo "Result: SUCCEEDED"
    success_count=$((success_count + 1))
  else
    status=$?
    echo "Result: FAILED — action exit status $status"
    failure_count=$((failure_count + 1))
  fi
done

for item_id in "${APPROVED_IDS[@]}"; do
  if [[ -z ${SEEN_APPROVED[$item_id]+x} ]]; then
    echo "Approved item was not present in the manifest: $item_id" >&2
    failure_count=$((failure_count + 1))
  fi
done

after_available=$(df -B1 --output=avail / 2>/dev/null | awk 'NR==2 {print $1}')
after_available=${after_available:-unknown}
echo
echo "Disk available after: $after_available bytes"
if [[ $before_available =~ ^[0-9]+$ && $after_available =~ ^[0-9]+$ ]]; then
  echo "Measured available-space change: $((after_available - before_available)) bytes"
else
  echo "Measured available-space change: unknown"
fi
echo "Actions succeeded: $success_count; failed/rejected: $failure_count"
echo "Btrfs note: snapshots may still reference removed extents, and reclamation may be asynchronous."

((failure_count == 0))
