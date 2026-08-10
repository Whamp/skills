#!/bin/bash
# shellcheck disable=SC2016

set -euo pipefail

SKILL_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
FIXTURE_ROOT=$(mktemp -d)
trap 'rm -rf -- "$FIXTURE_ROOT"' EXIT

TEST_HOME="$FIXTURE_ROOT/home"
TEST_BIN="$FIXTURE_ROOT/bin"
TEST_RUNTIME="$FIXTURE_ROOT/runtime"
TEST_ACTION_LOG="$FIXTURE_ROOT/action.log"
TEST_PACMAN_CACHE="$FIXTURE_ROOT/pacman cache"
TEST_COREDUMPS="$FIXTURE_ROOT/coredumps"

mkdir -p \
  "$TEST_HOME/projects" \
  "$TEST_HOME/Downloads" \
  "$TEST_HOME/.cache/thumbnails" \
  "$TEST_HOME/.cache/huggingface" \
  "$TEST_HOME/.cache/pnpm" \
  "$TEST_HOME/.cache/npm" \
  "$TEST_HOME/.cache/uv" \
  "$TEST_HOME/.cache/pip" \
  "$TEST_HOME/.cache/yarn" \
  "$TEST_HOME/.cache/go-build" \
  "$TEST_HOME/.local/share/Trash/files" \
  "$TEST_HOME/.local/share/Trash/info" \
  "$TEST_HOME/.local/share/omarchy/bin" \
  "$TEST_RUNTIME" \
  "$TEST_BIN" \
  "$TEST_PACMAN_CACHE" \
  "$TEST_COREDUMPS"
: >"$TEST_ACTION_LOG"

printf 'snapshot\n' >"$TEST_HOME/.cache/thumbnails/thumb 1"
printf 'trash\n' >"$TEST_HOME/.local/share/Trash/files/trashed item"
printf '[Trash Info]\n' >"$TEST_HOME/.local/share/Trash/info/trashed item.trashinfo"
printf 'model\n' >"$TEST_HOME/.cache/huggingface/model.safetensors"
printf 'update\n' >"$TEST_HOME/.local/share/omarchy/bin/omarchy-update"
printf 'omarchy-migrate\nomarchy-update-aur-pkgs\nomarchy-update-orphan-pkgs\n' \
  >"$TEST_HOME/.local/share/omarchy/bin/omarchy-update-perform"
chmod 0755 "$TEST_HOME/.local/share/omarchy/bin/omarchy-update-orphan-pkgs" 2>/dev/null || true

declare -a WEIRD_PARENTS=(
  "$TEST_HOME/projects/space parent"
  "$TEST_HOME/projects/"$'line\nbreak'
  "$TEST_HOME/projects/glob[*?]"
  "$TEST_HOME/projects/-leading"
)
for parent in "${WEIRD_PARENTS[@]}"; do
  mkdir -p "$parent/.next"
  printf 'artifact\n' >"$parent/.next/output.bin"
done

truncate -s 501M "$TEST_HOME/Downloads/"$'large\ninstaller[*?].iso'

create_stub() {
  local name=$1
  shift
  {
    printf '%s\n' '#!/bin/bash'
    printf '%s\n' "$@"
  } >"$TEST_BIN/$name"
  chmod 0755 "$TEST_BIN/$name"
}

create_stub omarchy \
  'case "${1-} ${2-}" in' \
  '  "version channel") echo edge ;;' \
  '  "version branch") echo master ;;' \
  '  "version "*) echo 3.8.4 ;;' \
  '  *) exit 1 ;;' \
  'esac'

create_stub pacman-conf 'printf "%s\n" "$OMARCHY_DISK_PACMAN_CACHE"'
create_stub paccache 'exit 0'
create_stub pacman \
  'case "${1-}" in' \
  '  -Qdtq) exit 0 ;;' \
  '  -Qq) echo linux ;;' \
  '  *) exit 0 ;;' \
  'esac'
create_stub snapper 'exit 1'
create_stub btrfs \
  'printf "%s\n" "Overall:" "    Device size: 10.00GiB" "    Used: 4.00GiB" "    Free (estimated): 6.00GiB"'
create_stub journalctl \
  'if [[ ${1-} == "--disk-usage" ]]; then echo "Archived and active journals take up 100.0M in the file system."; fi'
create_stub systemctl \
  'if [[ ${1-} == "is-active" && ${2-} == "--quiet" ]]; then exit 0; fi' \
  'if [[ ${1-} == "is-enabled" ]]; then echo enabled; else echo active; fi'
create_stub docker \
  'case "${1-} ${2-}" in' \
  '  "ps -aq") echo stopped-container ;;' \
  '  "image ls") echo image-id ;;' \
  '  "volume ls") echo volume-id ;;' \
  '  "system df") printf "%s\n" "TYPE TOTAL ACTIVE SIZE RECLAIMABLE" "Images 1 0 1GB 1GB" ;;' \
  'esac'
create_stub flatpak \
  'printf "%s\0" "$@" >>"$TEST_ACTION_LOG"' \
  'exit 0'
create_stub gio \
  'printf "%s\0" "$@" >>"$TEST_ACTION_LOG"' \
  'exit 0'

create_stub pnpm \
  'if [[ ${1-} == "store" && ${2-} == "path" ]]; then echo "$OMARCHY_DISK_HOME/.cache/pnpm"; else printf "%s\0" "$@" >>"$TEST_ACTION_LOG"; fi'
create_stub npm \
  'if [[ ${1-} == "config" ]]; then echo "$OMARCHY_DISK_HOME/.cache/npm"; else printf "%s\0" "$@" >>"$TEST_ACTION_LOG"; fi'
create_stub uv \
  'if [[ ${1-} == "cache" && ${2-} == "dir" ]]; then echo "$OMARCHY_DISK_HOME/.cache/uv"; else printf "%s\0" "$@" >>"$TEST_ACTION_LOG"; fi'
create_stub pip \
  'if [[ ${1-} == "cache" && ${2-} == "dir" ]]; then echo "$OMARCHY_DISK_HOME/.cache/pip"; else printf "%s\0" "$@" >>"$TEST_ACTION_LOG"; fi'
create_stub yarn \
  'if [[ ${1-} == "cache" && ${2-} == "dir" ]]; then echo "$OMARCHY_DISK_HOME/.cache/yarn"; else printf "%s\0" "$@" >>"$TEST_ACTION_LOG"; fi'
create_stub go \
  'if [[ ${1-} == "env" ]]; then echo "$OMARCHY_DISK_HOME/.cache/go-build"; else printf "%s\0" "$@" >>"$TEST_ACTION_LOG"; fi'

export PATH="$TEST_BIN:$PATH"
export XDG_RUNTIME_DIR="$TEST_RUNTIME"
export OMARCHY_DISK_HOME="$TEST_HOME"
export OMARCHY_DISK_PACMAN_CACHE="$TEST_PACMAN_CACHE"
export OMARCHY_DISK_COREDUMP_DIR="$TEST_COREDUMPS"
export TEST_ACTION_LOG

fixture_digest() {
  find "$TEST_HOME" -xdev -printf '%P\0%y\0%s\0%T@\0' | sort -z | sha256sum | awk '{print $1}'
}

manifest_field_for_target() {
  local manifest=$1
  local target=$2
  local field_offset=$3
  local -a fields
  local record_count base i
  mapfile -d '' -t fields <"$manifest"
  record_count=${fields[5]}
  for ((i = 0; i < record_count; i++)); do
    base=$((6 + i * 12))
    if [[ ${fields[$((base + 4))]} == "$target" ]]; then
      printf '%s' "${fields[$((base + field_offset))]}"
      return 0
    fi
  done
  return 1
}

assert_fails() {
  if "$@" >/dev/null 2>&1; then
    printf 'expected failure: %q ' "$@" >&2
    echo >&2
    exit 1
  fi
}

echo "1. audit is read-only"
before_digest=$(fixture_digest)
"$SKILL_DIR/scripts/audit.sh" audit --workspace-root "$TEST_HOME/projects" >"$FIXTURE_ROOT/audit.out"
after_digest=$(fixture_digest)
[[ $before_digest == "$after_digest" ]]
[[ ! -e "$TEST_RUNTIME/manifest" ]]

echo "2. deep planning creates a private manifest without cleanup"
"$SKILL_DIR/scripts/plan.sh" deep --workspace-root "$TEST_HOME/projects" >"$FIXTURE_ROOT/plan.out"
mapfile -t manifests < <(find "$TEST_RUNTIME" -maxdepth 1 -type f -name '*.manifest' -print)
((${#manifests[@]} == 1))
MANIFEST=${manifests[0]}
[[ $(stat -c '%a' "$MANIFEST") == "600" ]]
[[ ! -s $TEST_ACTION_LOG ]]

echo "3. approval is mandatory and blanket approval is unavailable"
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST"
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST" --all

echo "4. manifest roundtrips difficult Linux paths"
declare -a WEIRD_TARGETS=()
declare -a WEIRD_IDS=()
for parent in "${WEIRD_PARENTS[@]}"; do
  WEIRD_TARGETS+=("$parent/.next")
  id=$(manifest_field_for_target "$MANIFEST" "$parent/.next" 0)
  [[ $id =~ ^D[0-9]{3}$ ]]
  WEIRD_IDS+=("$id")
done
download_target="$TEST_HOME/Downloads/"$'large\ninstaller[*?].iso'
[[ $(manifest_field_for_target "$MANIFEST" "$download_target" 0) =~ ^D[0-9]{3}$ ]]

echo "5. exact approvals preserve spaces, newlines, globs, and leading dashes"
declare -a weird_approval_args=()
for id in "${WEIRD_IDS[@]}"; do
  weird_approval_args+=(--approve "$id")
done
"$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST" "${weird_approval_args[@]}" >/dev/null
for target in "${WEIRD_TARGETS[@]}"; do
  grep -azFq "$target" "$TEST_ACTION_LOG"
done

echo "6. stale manifests are rejected"
STALE_MANIFEST="$TEST_RUNTIME/stale.manifest"
cp -- "$MANIFEST" "$STALE_MANIFEST"
perl -0777 -pi -e '@fields=split(/\0/,$_,-1); $fields[1]=1; $_=join("\0",@fields)' "$STALE_MANIFEST"
stale_id=$(manifest_field_for_target "$STALE_MANIFEST" "${WEIRD_TARGETS[0]}" 0)
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$STALE_MANIFEST" --approve "$stale_id"

echo "7. protected roots and symlink components are rejected"
home_size=$(du -s -B1 --apparent-size -- "$TEST_HOME" | awk '{print $1}')
home_mtime=$(stat -c '%Y' -- "$TEST_HOME")
home_device=$(stat -c '%d' -- "$TEST_HOME")
home_mount=$(findmnt -T "$TEST_HOME" -n -o TARGET)
assert_fails "$SKILL_DIR/scripts/validate-target.sh" \
  --target "$TEST_HOME" --type directory --size "$home_size" \
  --mtime "$home_mtime" --device "$home_device" --mount "$home_mount"

mkdir -p "$TEST_HOME/projects/real/.next"
ln -s "$TEST_HOME/projects/real" "$TEST_HOME/projects/link"
assert_fails "$SKILL_DIR/scripts/validate-target.sh" \
  --target "$TEST_HOME/projects/link/.next" --type directory --size 0 \
  --mtime 0 --device 0 --mount "$home_mount"

echo "8. changed file types and meaningful size drift are rejected"
type_target=${WEIRD_TARGETS[0]}
type_id=$(manifest_field_for_target "$MANIFEST" "$type_target" 0)
rm -rf -- "$type_target"
printf 'changed type\n' >"$type_target"
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST" --approve "$type_id"

drift_target=${WEIRD_TARGETS[1]}
drift_id=$(manifest_field_for_target "$MANIFEST" "$drift_target" 0)
drift_mtime=$(manifest_field_for_target "$MANIFEST" "$drift_target" 7)
truncate -s 2M "$drift_target/large.bin"
touch -d "@$drift_mtime" "$drift_target"
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST" --approve "$drift_id"

echo "9. report-only models and Docker volumes cannot reach deletion"
model_id=$(manifest_field_for_target "$MANIFEST" "$TEST_HOME/.cache/huggingface" 0)
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST" --approve "$model_id"
docker_volume_id=$(manifest_field_for_target "$MANIFEST" "docker-volumes" 0)
assert_fails "$SKILL_DIR/scripts/apply.sh" --manifest "$MANIFEST" --approve "$docker_volume_id"
grep -azFq "$TEST_HOME/.cache/huggingface" "$TEST_ACTION_LOG" && exit 1 || true

echo "10. one rejected item does not corrupt another exact approval"
valid_target=${WEIRD_TARGETS[2]}
valid_id=$(manifest_field_for_target "$MANIFEST" "$valid_target" 0)
: >"$TEST_ACTION_LOG"
assert_fails "$SKILL_DIR/scripts/apply.sh" \
  --manifest "$MANIFEST" \
  --approve "$type_id" \
  --approve "$valid_id"
grep -azFq "$valid_target" "$TEST_ACTION_LOG"
grep -azFq "$type_target" "$TEST_ACTION_LOG" && exit 1 || true

echo "11. manifest payload and skill scripts remain syntax-valid"
bash -n "$SKILL_DIR"/scripts/*.sh "$SKILL_DIR"/tests/*.sh

echo "All fixture tests passed"
