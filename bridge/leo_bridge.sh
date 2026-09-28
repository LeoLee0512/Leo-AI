#!/bin/sh
# Leo AI Studio's Linux-side WSL2 bridge.  Keep this file LF-only.
set -u
umask 077

ACTION="${1:-}"
if [ -z "$ACTION" ]; then
  printf '%s\n' '{"schema":1,"ok":false,"action":"unknown","error":{"code":"INVALID_ACTION","message":"No bridge action was supplied.","guidance":[],"details":{}}}'
  exit 2
fi
shift

case "$ACTION" in
  preflight|install|install-runtime|stage-source|activate-source|status|start|url|stop|doctor|smoke|backup-data|restore-data|export|import) ;;
  *)
    printf '%s\n' '{"schema":1,"ok":false,"action":"unknown","error":{"code":"INVALID_ACTION","message":"The bridge action is not supported.","guidance":[],"details":{}}}'
    exit 2
    ;;
esac

BASE="$HOME/.local/share/leo-ai-studio"
RUNTIMES_DIR="$BASE/runtimes"
SOURCES_DIR="$BASE/sources"
DATA_DIR="$BASE/data"
BACKUPS_DIR="$BASE/backups"
TMP_DIR="$BASE/tmp"
DATA_TXN_DIR="$BASE/data-transaction"
DATA_TXN_LOCK="$BASE/data-transaction.lock"
ACTIVE_RUNTIME="$BASE/active-runtime"
ACTIVE_SOURCE="$BASE/active-source"
MIN_BWRAP_VERSION="0.8.0"
EMITTED=0
WORK_DIR=""
DATA_TXN_ACTIVE=0
SMOKE_SERVER_PID=""
SMOKE_SERVER_PORT=""
SMOKE_SERVER_START=""

json_ok() {
  python3 -I -c '
import json, sys
action = sys.argv[1]
data = {}
for item in sys.argv[2:]:
    key, kind, value = item.split("|", 2)
    if kind == "i":
        value = int(value)
    elif kind == "b":
        value = value == "1"
    elif kind == "n":
        value = None
    data[key] = value
print(json.dumps({"schema": 1, "ok": True, "action": action, "data": data}, separators=(",", ":")))
' "$ACTION" "$@"
  EMITTED=1
}

json_error() {
  code="$1"
  message="$2"
  shift 2
  if command -v python3 >/dev/null 2>&1; then
    python3 -I -c '
import json, sys
print(json.dumps({
    "schema": 1,
    "ok": False,
    "action": sys.argv[1],
    "error": {
        "code": sys.argv[2],
        "message": sys.argv[3],
        "guidance": sys.argv[4:],
        "details": {},
    },
}, separators=(",", ":")))
' "$ACTION" "$code" "$message" "$@"
  else
    # preflight must still have a valid contract on a minimal distribution.
    printf '{"schema":1,"ok":false,"action":"%s","error":{"code":"PYTHON_REQUIRED","message":"Python 3 is required inside WSL.","guidance":[],"details":{}}}\n' "$ACTION"
  fi
  EMITTED=1
}

die() {
  json_error "$@"
  exit 1
}

cleanup() {
  if [ -n "$WORK_DIR" ]; then
    case "$WORK_DIR" in
      "$TMP_DIR"/*) rm -rf -- "$WORK_DIR" ;;
    esac
  fi
}

path_present() {
  [ -e "$1" ] || [ -L "$1" ]
}

read_data_transaction_state() {
  DATA_TXN_STATE=""
  state_file="$DATA_TXN_DIR/state"
  if path_present "$state_file"; then
    [ -f "$state_file" ] && [ ! -L "$state_file" ] || return 1
    IFS= read -r DATA_TXN_STATE < "$state_file" || [ -n "$DATA_TXN_STATE" ] || return 1
    case "$DATA_TXN_STATE" in
      prepared|old-saved|committing|committed) ;;
      *) return 1 ;;
    esac
  fi
}

remove_data_transaction() {
  [ -d "$DATA_TXN_DIR" ] && [ ! -L "$DATA_TXN_DIR" ] || return 1
  # Keep the state marker until both trees are gone.  A signal during cleanup
  # can therefore replay the same committed/rollback decision safely.
  rm -rf -- "$DATA_TXN_DIR/old-data" "$DATA_TXN_DIR/new-data" || return 1
  rm -f -- "$DATA_TXN_DIR"/.state.*.tmp || return 1
  rm -f -- "$DATA_TXN_DIR/state" || return 1
  rmdir -- "$DATA_TXN_DIR" || return 1
  rm -f -- "$DATA_TXN_LOCK" || return 1
  DATA_TXN_ACTIVE=0
}

recover_data_transaction() {
  lock_exists=0
  if path_present "$DATA_TXN_LOCK"; then
    lock_exists=1
    [ -f "$DATA_TXN_LOCK" ] && [ ! -L "$DATA_TXN_LOCK" ] || return 3
    owner=""
    IFS= read -r owner < "$DATA_TXN_LOCK" || [ -n "$owner" ] || return 3
    case "$owner" in
      ''|*[!0-9]*) return 3 ;;
    esac
    if [ "$owner" != "$$" ] && kill -0 "$owner" 2>/dev/null; then
      return 2
    fi
  fi

  if ! path_present "$DATA_TXN_DIR"; then
    if [ "$lock_exists" -eq 1 ]; then
      rm -f -- "$DATA_TXN_LOCK" || return 3
    fi
    DATA_TXN_ACTIVE=0
    return 0
  fi
  [ -d "$DATA_TXN_DIR" ] && [ ! -L "$DATA_TXN_DIR" ] || return 3
  read_data_transaction_state || return 3

  old="$DATA_TXN_DIR/old-data"
  new="$DATA_TXN_DIR/new-data"
  old_exists=0
  new_exists=0
  data_exists=0
  if path_present "$old"; then
    [ -d "$old" ] && [ ! -L "$old" ] || return 3
    old_exists=1
  fi
  if path_present "$new"; then
    [ -d "$new" ] && [ ! -L "$new" ] || return 3
    new_exists=1
  fi
  if path_present "$DATA_DIR"; then
    [ -d "$DATA_DIR" ] && [ ! -L "$DATA_DIR" ] || return 3
    data_exists=1
  fi

  case "$DATA_TXN_STATE" in
    ""|prepared|old-saved)
      # Before the durable commit point, preserve or restore the old tree.
      if [ "$old_exists" -eq 1 ]; then
        [ "$data_exists" -eq 0 ] || return 3
        mv -- "$old" "$DATA_DIR" || return 3
        data_exists=1
      else
        [ "$data_exists" -eq 1 ] || return 3
      fi
      ;;
    committing|committed)
      # At/after the commit point, finish publishing the complete new tree.
      if [ "$data_exists" -eq 1 ] && [ "$new_exists" -eq 1 ]; then
        return 3
      fi
      if [ "$data_exists" -eq 0 ] && [ "$new_exists" -eq 1 ]; then
        mv -- "$new" "$DATA_DIR" || return 3
        data_exists=1
        new_exists=0
      elif [ "$data_exists" -eq 0 ] && [ "$new_exists" -eq 0 ]; then
        # A failed activation must still leave the previous complete tree usable.
        [ "$old_exists" -eq 1 ] || return 3
        mv -- "$old" "$DATA_DIR" || return 3
        data_exists=1
      fi
      [ "$data_exists" -eq 1 ] || return 3
      ;;
  esac

  remove_data_transaction || return 3
  return 0
}

write_data_transaction_state() {
  next_state="$1"
  case "$next_state" in
    prepared|old-saved|committing|committed) ;;
    *) return 1 ;;
  esac
  python3 -I - "$DATA_TXN_DIR" "$next_state" <<'PY'
import os
import sys
from pathlib import Path

directory = Path(sys.argv[1])
state = sys.argv[2]
temporary = directory / f".state.{os.getpid()}.tmp"
fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
try:
    with os.fdopen(fd, "w", encoding="ascii") as stream:
        stream.write(state + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, directory / "state")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_fd = os.open(directory, flags)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
finally:
    try:
        temporary.unlink()
    except FileNotFoundError:
        pass
PY
}

loopback_port_closed() {
  python3 -I - "$1" <<'PY'
import socket
import sys

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
    probe.settimeout(0.25)
    raise SystemExit(
        0 if probe.connect_ex(("127.0.0.1", int(sys.argv[1]))) != 0 else 1
    )
PY
}

stop_smoke_server() {
  pid="$SMOKE_SERVER_PID"
  port="$SMOKE_SERVER_PORT"
  expected_start="$SMOKE_SERVER_START"
  case "$pid" in ''|*[!0-9]*) return 1 ;; esac
  case "$port" in ''|*[!0-9]*) return 1 ;; esac
  case "$expected_start" in ''|*[!0-9]*) return 1 ;; esac

  actual_start="$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null || true)"
  if [ "$actual_start" = "$expected_start" ] && kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    count=0
    while [ "$count" -lt 50 ]; do
      actual_start="$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null || true)"
      [ "$actual_start" = "$expected_start" ] || break
      state="$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null || true)"
      [ "$state" != "Z" ] || break
      count=$((count + 1))
      sleep 0.1
    done
    actual_start="$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null || true)"
    state="$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null || true)"
    if [ "$actual_start" = "$expected_start" ] && [ "$state" != "Z" ]; then
      kill -KILL "$pid" 2>/dev/null || true
      count=0
      while [ "$count" -lt 50 ]; do
        actual_start="$(awk '{print $22}' "/proc/$pid/stat" 2>/dev/null || true)"
        [ "$actual_start" = "$expected_start" ] || break
        state="$(awk '{print $3}' "/proc/$pid/stat" 2>/dev/null || true)"
        [ "$state" != "Z" ] || break
        count=$((count + 1))
        sleep 0.1
      done
    fi
  fi
  wait "$pid" 2>/dev/null || true
  SMOKE_SERVER_PID=""
  SMOKE_SERVER_START=""

  count=0
  while [ "$count" -lt 30 ]; do
    if loopback_port_closed "$port"; then
      SMOKE_SERVER_PORT=""
      return 0
    fi
    count=$((count + 1))
    sleep 0.1
  done
  return 1
}

begin_data_transaction() {
  staged="$1"
  [ -n "$WORK_DIR" ] && [ -d "$staged" ] && [ ! -L "$staged" ] || return 1
  mkdir -p "$BASE" || return 1
  owner_file="$WORK_DIR/data-transaction-owner"
  printf '%s\n' "$$" > "$owner_file" || return 1
  if ! ln "$owner_file" "$DATA_TXN_LOCK" 2>/dev/null; then
    return 2
  fi
  DATA_TXN_ACTIVE=1
  mkdir "$DATA_TXN_DIR" || return 1
  mv -- "$staged" "$DATA_TXN_DIR/new-data" || return 1
  write_data_transaction_state "prepared" || return 1
}

activate_data_transaction() {
  [ "$DATA_TXN_ACTIVE" -eq 1 ] || return 1
  [ -d "$DATA_DIR" ] && [ ! -L "$DATA_DIR" ] || return 1
  [ -d "$DATA_TXN_DIR/new-data" ] && [ ! -L "$DATA_TXN_DIR/new-data" ] || return 1
  mv -- "$DATA_DIR" "$DATA_TXN_DIR/old-data" || return 1
  write_data_transaction_state "old-saved" || return 1
  # Recovery rolls back before this marker and completes the new tree after it.
  write_data_transaction_state "committing" || return 1
  mv -- "$DATA_TXN_DIR/new-data" "$DATA_DIR" || return 1
  write_data_transaction_state "committed" || return 1
  remove_data_transaction || return 1
}

on_exit() {
  rc=$?
  trap - EXIT HUP INT TERM
  smoke_stop_rc=0
  if [ -n "$SMOKE_SERVER_PID" ]; then
    stop_smoke_server || smoke_stop_rc=$?
    if [ "$rc" -eq 0 ] && [ "$smoke_stop_rc" -ne 0 ]; then
      rc=1
    fi
  fi
  recovery_rc=0
  if [ "$DATA_TXN_ACTIVE" -eq 1 ]; then
    recover_data_transaction || recovery_rc=$?
    if [ "$rc" -eq 0 ] && [ "$recovery_rc" -ne 0 ]; then
      rc=1
    fi
  fi
  if [ "$rc" -ne 0 ] && [ "$EMITTED" -eq 0 ]; then
    json_error "BRIDGE_INTERNAL_ERROR" "The WSL bridge failed unexpectedly." "Open Diagnostics and retry after reviewing the WSL checks."
  fi
  cleanup
  exit "$rc"
}
trap 'exit 130' HUP INT TERM
trap on_exit EXIT

new_work() {
  mkdir -p "$TMP_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its WSL temporary directory."
  if [ -n "$WORK_DIR" ]; then
    cleanup
    WORK_DIR=""
  fi
  WORK_DIR="$TMP_DIR/$ACTION.$$"
  [ ! -e "$WORK_DIR" ] || die "TEMP_COLLISION" "A stale WSL bridge transaction exists."
  mkdir "$WORK_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create a WSL transaction directory."
}

version_at_least() {
  awk -v have="$1" -v need="$2" 'BEGIN {
    split(have, h, "."); split(need, n, ".")
    for (i = 1; i <= 3; i++) {
      hv = h[i] + 0; nv = n[i] + 0
      if (hv > nv) exit 0
      if (hv < nv) exit 1
    }
    exit 0
  }'
}

require_non_root_wsl2() {
  [ "$(id -u)" -ne 0 ] || die "WSL_ROOT_USER" "Leo must run as a non-root WSL user." "Set a normal user as this distribution's default user, then retry."
  grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null || die "WSL2_REQUIRED" "This environment is not WSL2." "Install or convert an Ubuntu distribution to WSL2."
  [ "$(uname -m)" = "x86_64" ] || die "WSL_ARCH_UNSUPPORTED" "Leo requires an x86-64 WSL2 distribution."
  command -v python3 >/dev/null 2>&1 || die "PYTHON_REQUIRED" "Python 3 is required inside WSL." "Use Ubuntu 24.04 or install python3."
}

run_preflight() {
  require_non_root_wsl2
  for tool in awk grep tar sha256sum readlink; do
    command -v "$tool" >/dev/null 2>&1 || die "WSL_TOOL_MISSING" "A required WSL utility is missing." "Use Ubuntu 24.04 or install coreutils and tar."
  done
  command -v bwrap >/dev/null 2>&1 || die "BWRAP_MISSING" "bubblewrap is required for isolated scientific cells." "Run: sudo apt update && sudo apt install -y bubblewrap"
  BWRAP_VERSION="$(bwrap --version 2>/dev/null | awk '{print $NF}')"
  [ -n "$BWRAP_VERSION" ] || die "BWRAP_INVALID" "bubblewrap did not report a version."
  version_at_least "$BWRAP_VERSION" "$MIN_BWRAP_VERSION" || die "BWRAP_TOO_OLD" "bubblewrap 0.8.0 or newer is required." "Upgrade bubblewrap inside the selected WSL2 distribution."
  bwrap --die-with-parent --new-session --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
    --ro-bind / / --dev /dev --proc /proc -- /bin/true >/dev/null 2>&1 \
    || die "BWRAP_UNUSABLE" "bubblewrap is installed but cannot create the required WSL2 sandbox." "Confirm the distribution is WSL2 and user namespaces are enabled."
  json_ok "wsl|b|1" "non_root|b|1" "arch|s|x86_64" "bwrap_version|s|$BWRAP_VERSION" "home|s|$HOME"
}

valid_digest() {
  case "$1" in
    *[!0-9a-f]*|'') return 1 ;;
  esac
  [ "${#1}" -eq 64 ]
}

valid_revision() {
  case "$1" in
    *[!0-9a-f]*|'') return 1 ;;
  esac
  [ "${#1}" -ge 7 ] && [ "${#1}" -le 64 ]
}

valid_id() {
  case "$1" in
    ''|*[!A-Za-z0-9._-]*|.*) return 1 ;;
    *) [ "${#1}" -le 128 ] ;;
  esac
}

verify_archive() {
  archive="$1"
  expected="$2"
  [ -f "$archive" ] || die "ARCHIVE_MISSING" "A required archive is not readable from WSL."
  valid_digest "$expected" || die "ARCHIVE_METADATA_INVALID" "An archive checksum is invalid."
  actual="$(sha256sum "$archive" 2>/dev/null | awk '{print $1}')"
  [ "$actual" = "$expected" ] || die "ARCHIVE_CHECKSUM_MISMATCH" "An archive failed its SHA-256 integrity check." "Replace the damaged Leo AI Studio package and retry."
}

safe_extract() {
  archive="$1"
  destination="$2"
  mkdir "$destination" || return 1
  python3 -I - "$archive" "$destination" <<'PY'
import os
import posixpath
import shutil
import stat
import sys
import tarfile

archive, destination = sys.argv[1:]
root = os.path.realpath(destination)
max_members = 200_000
max_bytes = 8 * 1024 * 1024 * 1024

def clean_name(value):
    if not value or "\\" in value or value.startswith("/"):
        raise ValueError("unsafe archive path")
    normalized = posixpath.normpath(value)
    if normalized in ("", "."):
        return None
    if normalized == ".." or normalized.startswith("../") or "/../" in f"/{normalized}/":
        raise ValueError("archive path traversal")
    return normalized

def target_path(name):
    target = os.path.realpath(os.path.join(root, *name.split("/")))
    if target != root and not target.startswith(root + os.sep):
        raise ValueError("archive target escaped destination")
    return target

with tarfile.open(archive, "r:*") as tf:
    members = tf.getmembers()
    if len(members) > max_members or sum(max(0, m.size) for m in members) > max_bytes:
        raise ValueError("archive is too large")
    seen = set()
    normalized = []
    for member in members:
        name = clean_name(member.name)
        if name is None:
            continue
        if name in seen:
            raise ValueError("duplicate archive path")
        seen.add(name)
        if not (member.isdir() or member.isreg() or member.issym() or member.islnk()):
            raise ValueError("unsupported archive entry")
        if member.issym():
            link = member.linkname
            if not link or "\\" in link or link.startswith("/"):
                raise ValueError("unsafe symbolic link")
            combined = posixpath.normpath(posixpath.join(posixpath.dirname(name), link))
            clean_name(combined)
        elif member.islnk():
            clean_name(member.linkname)
        normalized.append((member, name))

    directories = sorted(
        ((member, name) for member, name in normalized if member.isdir()),
        key=lambda item: (item[1].count("/"), item[1]),
    )
    for member, name in directories:
        if member.isdir():
            os.makedirs(target_path(name), mode=0o700, exist_ok=True)
    for member, name in normalized:
        if not member.isreg():
            continue
        target = target_path(name)
        os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
        source = tf.extractfile(member)
        if source is None:
            raise ValueError("regular file has no data")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(target, flags, member.mode & 0o777 or 0o600)
        with source, os.fdopen(fd, "wb") as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
    for member, name in normalized:
        target = target_path(name)
        if member.issym():
            os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
            os.symlink(member.linkname, target)
        elif member.islnk():
            link_target = target_path(clean_name(member.linkname))
            if not os.path.isfile(link_target) or os.path.islink(link_target):
                raise ValueError("hard link target is not a regular file")
            os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
            os.link(link_target, target)
PY
}

single_child() {
  parent="$1"
  count="$(find "$parent" -mindepth 1 -maxdepth 1 -printf x 2>/dev/null | wc -c | tr -d ' ')"
  [ "$count" = "1" ] || return 1
  find "$parent" -mindepth 1 -maxdepth 1 -print
}

runtime_root() {
  extracted="$1"
  if [ -x "$extracted/runtime/bin/python3" ]; then
    printf '%s\n' "$extracted"
    return 0
  fi
  child="$(single_child "$extracted" || true)"
  if [ -n "$child" ] && [ -d "$child" ] && [ -x "$child/runtime/bin/python3" ]; then
    printf '%s\n' "$child"
    return 0
  fi
  return 1
}

source_root() {
  extracted="$1"
  if [ -d "$extracted/openai4s" ] && [ -f "$extracted/pyproject.toml" ]; then
    printf '%s\n' "$extracted"
    return 0
  fi
  child="$(single_child "$extracted" || true)"
  if [ -n "$child" ] && [ -d "$child/openai4s" ] && [ -f "$child/pyproject.toml" ]; then
    printf '%s\n' "$child"
    return 0
  fi
  return 1
}

atomic_link() {
  target="$1"
  link="$2"
  temp="$BASE/.link.$$"
  rm -f -- "$temp"
  ln -s "$target" "$temp" || die "ACTIVATION_FAILED" "A version snapshot could not be selected."
  mv -Tf -- "$temp" "$link" || die "ACTIVATION_FAILED" "A version snapshot could not be selected."
}

do_install_runtime() {
  archive="$1"
  digest="$2"
  version="$3"
  valid_id "$version" || die "RUNTIME_METADATA_INVALID" "The runtime version identifier is invalid."
  verify_archive "$archive" "$digest"
  short="$(printf '%s' "$digest" | cut -c1-12)"
  target="$RUNTIMES_DIR/$version-$short"
  if [ -f "$target/.leo-runtime-sha256" ] && [ "$(cat "$target/.leo-runtime-sha256")" = "$digest" ] && [ -x "$target/runtime/bin/python3" ]; then
    atomic_link "runtimes/$(basename "$target")" "$ACTIVE_RUNTIME"
    INSTALLED_RUNTIME="$target"
    return 0
  fi
  [ ! -e "$target" ] || die "RUNTIME_CORRUPT" "An existing versioned runtime is incomplete or has the wrong checksum."
  new_work
  extracted="$WORK_DIR/extracted"
  safe_extract "$archive" "$extracted" || die "ARCHIVE_UNSAFE" "The runtime archive contains an unsafe or invalid entry."
  selected="$(runtime_root "$extracted" || true)"
  [ -n "$selected" ] || die "RUNTIME_LAYOUT_INVALID" "The runtime archive does not contain runtime/bin/python3."
  mkdir -p "$RUNTIMES_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its versioned runtime directory."
  staged="$RUNTIMES_DIR/.new-$version-$$"
  [ ! -e "$staged" ] || die "TEMP_COLLISION" "A stale runtime installation transaction exists."
  mv -- "$selected" "$staged" || die "RUNTIME_INSTALL_FAILED" "The runtime could not be moved into WSL storage."
  [ ! -e "$staged/.leo-runtime-sha256" ] && [ ! -L "$staged/.leo-runtime-sha256" ] \
    || die "RUNTIME_LAYOUT_INVALID" "The runtime archive contains a reserved Leo marker."
  printf '%s\n' "$digest" > "$staged/.leo-runtime-sha256" || die "RUNTIME_INSTALL_FAILED" "The runtime marker could not be written."
  mv -- "$staged" "$target" || die "RUNTIME_INSTALL_FAILED" "The runtime could not be installed atomically."
  atomic_link "runtimes/$(basename "$target")" "$ACTIVE_RUNTIME"
  INSTALLED_RUNTIME="$target"
}

do_stage_source() {
  archive="$1"
  digest="$2"
  revision="$3"
  valid_revision "$revision" || die "SOURCE_METADATA_INVALID" "The source revision is invalid."
  verify_archive "$archive" "$digest"
  target="$SOURCES_DIR/$revision"
  if [ -f "$target/.leo-source-sha256" ] && [ "$(cat "$target/.leo-source-sha256")" = "$digest" ] && [ -d "$target/openai4s" ]; then
    STAGED_SOURCE="$target"
    return 0
  fi
  [ ! -e "$target" ] || die "SOURCE_CORRUPT" "An existing source snapshot is incomplete or has the wrong checksum."
  new_work
  extracted="$WORK_DIR/extracted"
  safe_extract "$archive" "$extracted" || die "ARCHIVE_UNSAFE" "The source archive contains an unsafe or invalid entry."
  selected="$(source_root "$extracted" || true)"
  [ -n "$selected" ] || die "SOURCE_LAYOUT_INVALID" "The source archive is not a complete OpenAI4S repository snapshot."
  mkdir -p "$SOURCES_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its versioned source directory."
  staged="$SOURCES_DIR/.new-$revision-$$"
  [ ! -e "$staged" ] || die "TEMP_COLLISION" "A stale source installation transaction exists."
  mv -- "$selected" "$staged" || die "SOURCE_INSTALL_FAILED" "The source could not be moved into WSL storage."
  [ ! -e "$staged/.leo-source-sha256" ] && [ ! -L "$staged/.leo-source-sha256" ] \
    || die "SOURCE_LAYOUT_INVALID" "The source archive contains a reserved Leo marker."
  printf '%s\n' "$digest" > "$staged/.leo-source-sha256" || die "SOURCE_INSTALL_FAILED" "The source marker could not be written."
  mv -- "$staged" "$target" || die "SOURCE_INSTALL_FAILED" "The source could not be installed atomically."
  STAGED_SOURCE="$target"
}

do_activate_source() {
  revision="$1"
  valid_revision "$revision" || die "SOURCE_METADATA_INVALID" "The source revision is invalid."
  target="$SOURCES_DIR/$revision"
  [ -f "$target/.leo-source-sha256" ] && [ -d "$target/openai4s" ] || die "SOURCE_NOT_STAGED" "The requested source revision has not been staged."
  atomic_link "sources/$revision" "$ACTIVE_SOURCE"
}

setup_environment() {
  requested_revision="${1:-}"
  requested_data="${2:-}"
  runtime="$(readlink -f "$ACTIVE_RUNTIME" 2>/dev/null || true)"
  if [ -n "$requested_revision" ]; then
    valid_revision "$requested_revision" || die "SOURCE_METADATA_INVALID" "The source revision is invalid."
    source="$SOURCES_DIR/$requested_revision"
  else
    source="$(readlink -f "$ACTIVE_SOURCE" 2>/dev/null || true)"
  fi
  case "$runtime/" in "$RUNTIMES_DIR"/*/) ;; *) die "RUNTIME_NOT_INSTALLED" "No valid Leo Linux runtime is active." ;; esac
  case "$source/" in "$SOURCES_DIR"/*/) ;; *) die "SOURCE_NOT_INSTALLED" "No valid OpenAI4S source snapshot is active." ;; esac
  [ -x "$runtime/runtime/bin/python3" ] || die "RUNTIME_NOT_INSTALLED" "The active Leo Linux runtime is incomplete."
  [ -d "$source/openai4s" ] || die "SOURCE_NOT_INSTALLED" "The active OpenAI4S source snapshot is incomplete."
  PY="$runtime/runtime/bin/python3"
  SOURCE="$source"
  RUNTIME="$runtime"
  if [ -n "$requested_data" ]; then
    OPENAI4S_DATA_DIR="$requested_data"
  else
    OPENAI4S_DATA_DIR="$DATA_DIR"
  fi
  mkdir -p "$OPENAI4S_DATA_DIR" "$BASE/python-user" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its WSL data directory."
  PATH="$runtime/runtime/bin:$runtime/bin:$PATH"
  PYTHONPATH="$source"
  PYTHONUSERBASE="$BASE/python-user"
  MPLBACKEND="Agg"
  OPENAI4S_HOST="127.0.0.1"
  OPENAI4S_PORT="8760"
  OPENAI4S_NO_OPEN="1"
  OPENAI4S_KERNEL_SANDBOX="enforce"
  OPENAI4S_SECRET_STORE="env"
  OPENAI4S_SECRET_ENV="1"
  OPENAI4S_SKILLS_DIR="$source/skills"
  export PATH PYTHONPATH PYTHONUSERBASE MPLBACKEND OPENAI4S_DATA_DIR OPENAI4S_HOST OPENAI4S_PORT OPENAI4S_NO_OPEN OPENAI4S_KERNEL_SANDBOX OPENAI4S_SECRET_STORE OPENAI4S_SECRET_ENV OPENAI4S_SKILLS_DIR
  unset PYTHONHOME
}

run_cli() {
  "$PY" -m openai4s "$@"
}

run_smoke_isolated() {
  clean_path="$RUNTIME/runtime/bin:$RUNTIME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  bwrap --die-with-parent --new-session --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
    --ro-bind / / --dev /dev --proc /proc \
    --tmpfs /home --tmpfs /root --tmpfs /mnt --tmpfs /media --tmpfs /run --tmpfs /tmp \
    --dir "$RUNTIME" --ro-bind "$RUNTIME" "$RUNTIME" \
    --dir "$SOURCE" --ro-bind "$SOURCE" "$SOURCE" \
    --dir /tmp/home --dir /tmp/python-user --dir /tmp/matplotlib --dir /tmp/data \
    --clearenv --setenv HOME /tmp/home --setenv TMPDIR /tmp \
    --setenv PATH "$clean_path" --setenv PYTHONPATH "$SOURCE" \
    --setenv PYTHONUSERBASE /tmp/python-user --setenv MPLBACKEND Agg \
    --setenv MPLCONFIGDIR /tmp/matplotlib --setenv OPENAI4S_DATA_DIR /tmp/data \
    --setenv OPENAI4S_HOST 127.0.0.1 --setenv OPENAI4S_PORT 8760 \
    --setenv OPENAI4S_NO_OPEN 1 --setenv OPENAI4S_KERNEL_SANDBOX enforce \
    --setenv OPENAI4S_SECRET_STORE env --setenv OPENAI4S_SECRET_ENV 1 \
    --setenv OPENAI4S_SKILLS_DIR "$SOURCE/skills" \
    -- "$@"
}

daemon_running() {
  out="$1"
  err="$2"
  run_cli status >"$out" 2>"$err"
}

refuse_running_daemon() {
  # Data actions remain fail-closed even if the active snapshot links were
  # damaged or removed.  A live recorded PID or any listener on Leo's fixed
  # loopback port means the data tree may still be in use; never guess at the
  # process identity and never terminate an unknown listener here.
  if [ -f "$DATA_DIR/openai4s.pid" ] && [ ! -L "$DATA_DIR/openai4s.pid" ]; then
    recorded_pid=""
    IFS= read -r recorded_pid < "$DATA_DIR/openai4s.pid" || true
    case "$recorded_pid" in
      ''|*[!0-9]*) ;;
      *)
        if kill -0 "$recorded_pid" 2>/dev/null; then
          die "DATA_IN_USE" "OpenAI4S must be stopped before changing its data." "Close Leo AI Studio and retry."
        fi
        ;;
    esac
  fi
  if python3 -I - <<'PY'
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
    probe.settimeout(0.25)
    raise SystemExit(0 if probe.connect_ex(("127.0.0.1", 8760)) == 0 else 1)
PY
  then
    die "DATA_IN_USE" "Port 8760 is active, so Leo will not change its WSL data." "Close Leo AI Studio or the conflicting listener and retry."
  fi
  if [ -L "$ACTIVE_RUNTIME" ] && [ -L "$ACTIVE_SOURCE" ]; then
    setup_environment "" ""
    check_out="$WORK_DIR/daemon-status.out"
    check_err="$WORK_DIR/daemon-status.err"
    daemon_running "$check_out" "$check_err"
    daemon_rc=$?
    if [ "$daemon_rc" -ne 1 ]; then
      die "DATA_IN_USE" "OpenAI4S must be stopped before changing its data." "Close Leo AI Studio and retry."
    fi
  fi
}

copy_clean_tree() {
  source="$1"
  destination="$2"
  python3 -I - "$source" "$destination" <<'PY'
import os
import shutil
import sys
from pathlib import Path

source, destination = map(Path, sys.argv[1:])

def excluded(relative):
    parts = [part.lower() for part in relative.parts]
    if not parts:
        return False
    if "logs" in parts:
        return True
    name = parts[-1]
    return (
        name in {
            ".env",
            "access-token",
            "worker-bootstrap-secret",
            "openai4s.pid",
            "daemon.json",
            "app.out",
            "app.err",
        }
        or name.startswith(".access-token.tmp-")
        or name.startswith(".worker-bootstrap-secret.tmp-")
        or name.endswith(".pid")
        or name.endswith(".log")
        or ".log." in name
        or name.startswith("app.out.")
        or name.startswith("app.err.")
    )

destination.mkdir(parents=True, exist_ok=False)
if not source.exists():
    raise SystemExit(0)
for item in sorted(source.rglob("*")):
    relative = item.relative_to(source)
    if excluded(relative) or item.is_symlink():
        continue
    target = destination / relative
    if item.is_dir():
        target.mkdir(parents=True, exist_ok=True)
    elif item.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
PY
}

emit_url() {
  client_url="$1"
  LEO_JSON_ACTION="$ACTION" LEO_JSON_URL="$client_url" python3 -I -c '
import json, os
print(json.dumps({"schema": 1, "ok": True, "action": os.environ["LEO_JSON_ACTION"], "data": {"client_url": os.environ["LEO_JSON_URL"]}}, separators=(",", ":")))
' || return 1
  EMITTED=1
}

recovery_rc=0
recover_data_transaction || recovery_rc=$?
case "$recovery_rc" in
  0) ;;
  2) die "DATA_TRANSACTION_BUSY" "Another Leo data transaction is still running." "Wait for the current import or restore operation to finish, then retry." ;;
  *) die "DATA_RECOVERY_REQUIRED" "Leo found an incomplete data transaction that could not be recovered safely." "Open Diagnostics and preserve the WSL data-transaction directory before retrying." ;;
esac

case "$ACTION" in
preflight)
  run_preflight
  ;;

install-runtime)
  require_non_root_wsl2
  [ "$#" -eq 3 ] || die "INVALID_ARGUMENT" "install-runtime needs archive, checksum, and version."
  do_install_runtime "$1" "$2" "$3"
  json_ok "state|s|installed" "runtime|s|$(basename "$INSTALLED_RUNTIME")"
  ;;

stage-source)
  require_non_root_wsl2
  [ "$#" -eq 3 ] || die "INVALID_ARGUMENT" "stage-source needs archive, checksum, and revision."
  do_stage_source "$1" "$2" "$3"
  json_ok "state|s|staged" "revision|s|$3"
  ;;

activate-source)
  require_non_root_wsl2
  [ "$#" -eq 1 ] || die "INVALID_ARGUMENT" "activate-source needs one revision."
  do_activate_source "$1"
  json_ok "state|s|active" "revision|s|$1"
  ;;

install)
  require_non_root_wsl2
  [ "$#" -eq 6 ] || die "INVALID_ARGUMENT" "install needs runtime and source archive metadata."
  do_install_runtime "$1" "$2" "$3"
  do_stage_source "$4" "$5" "$6"
  do_activate_source "$6"
  json_ok "state|s|installed" "runtime|s|$(basename "$INSTALLED_RUNTIME")" "revision|s|$6"
  ;;

status)
  require_non_root_wsl2
  if [ ! -L "$ACTIVE_RUNTIME" ] || [ ! -L "$ACTIVE_SOURCE" ]; then
    json_ok "state|s|not-installed" "running|b|0"
    exit 0
  fi
  new_work
  setup_environment "" ""
  out="$WORK_DIR/status.out"
  err="$WORK_DIR/status.err"
  daemon_running "$out" "$err"
  rc=$?
  revision="$(basename "$SOURCE")"
  runtime_version="$(basename "$RUNTIME")"
  case "$rc" in
    0)
      pid="$(sed -n 's/.*pid \([0-9][0-9]*\).*/\1/p' "$out" | head -n 1)"
      if [ -n "$pid" ]; then
        json_ok "state|s|running" "running|b|1" "pid|i|$pid" "revision|s|$revision" "runtime|s|$runtime_version"
      else
        json_ok "state|s|running" "running|b|1" "revision|s|$revision" "runtime|s|$runtime_version"
      fi
      ;;
    1) json_ok "state|s|stopped" "running|b|0" "revision|s|$revision" "runtime|s|$runtime_version" ;;
    *) die "DAEMON_UNHEALTHY" "The Leo daemon exists but did not pass its health check." "Open Diagnostics before restarting it." ;;
  esac
  ;;

start)
  require_non_root_wsl2
  [ "$#" -eq 3 ] || die "INVALID_ARGUMENT" "start needs provider, model, and base URL arguments."
  provider="$1"
  model="$2"
  base_url="$3"
  case "$provider" in ark|chatgpt|openai_responses|claude|gemini) ;; *) die "PROVIDER_INVALID" "The selected model provider is unsupported." ;; esac
  [ -n "$model" ] || die "MODEL_INVALID" "The selected model is empty."
  new_work
  setup_environment "" ""
  status_out="$WORK_DIR/status.out"
  status_err="$WORK_DIR/status.err"
  daemon_running "$status_out" "$status_err"
  daemon_rc=$?
  if [ "$daemon_rc" -eq 0 ]; then
    json_ok "state|s|already-running" "running|b|1"
    exit 0
  fi
  [ "$daemon_rc" -eq 1 ] || die "DAEMON_UNHEALTHY" "The existing Leo daemon did not pass its health check." "Stop it from Diagnostics before retrying."
  set -- init --provider "$provider" --model "$model" --non-interactive --json
  if [ -n "$base_url" ]; then
    set -- "$@" --base-url "$base_url"
  fi
  run_cli "$@" >"$WORK_DIR/init.out" 2>"$WORK_DIR/init.err" || die "MODEL_CONFIGURATION_FAILED" "OpenAI4S rejected the selected model configuration." "Review provider, model, and base URL in Settings."
  run_cli serve --host 127.0.0.1 --port 8760 --no-browser --detached >"$WORK_DIR/start.out" 2>"$WORK_DIR/start.err" \
    || die "DAEMON_START_FAILED" "The OpenAI4S daemon could not be started." "Open Diagnostics to inspect the redacted startup report."
  count=0
  while [ "$count" -lt 30 ]; do
    if daemon_running "$status_out" "$status_err"; then
      pid="$(sed -n 's/.*pid \([0-9][0-9]*\).*/\1/p' "$status_out" | head -n 1)"
      if [ -n "$pid" ]; then
        json_ok "state|s|running" "running|b|1" "pid|i|$pid"
      else
        json_ok "state|s|running" "running|b|1"
      fi
      exit 0
    fi
    count=$((count + 1))
    sleep 1
  done
  die "DAEMON_START_TIMEOUT" "OpenAI4S started but did not become healthy within 30 seconds." "Open Diagnostics and check the WSL runtime."
  ;;

url)
  require_non_root_wsl2
  new_work
  setup_environment "" ""
  run_cli url >"$WORK_DIR/url.out" 2>"$WORK_DIR/url.err" || die "CLIENT_URL_UNAVAILABLE" "OpenAI4S did not return its sign-in URL."
  client_url="$(sed -n '/^http:\/\//p' "$WORK_DIR/url.out" | tail -n 1)"
  [ -n "$client_url" ] || die "CLIENT_URL_UNAVAILABLE" "OpenAI4S did not return its sign-in URL."
  LEO_CLIENT_URL="$client_url" python3 -I -c '
import os
from urllib.parse import parse_qsl, urlsplit
u = os.environ["LEO_CLIENT_URL"]
p = urlsplit(u)
q = parse_qsl(p.query, keep_blank_values=True, strict_parsing=True)
assert p.scheme == "http"
assert p.hostname in {"127.0.0.1", "localhost"}
assert p.port == 8760 and p.path == "/" and not p.fragment
assert p.username is None and p.password is None
assert len(q) == 1 and q[0][0] == "token" and q[0][1]
' >/dev/null 2>&1 || die "CLIENT_URL_INVALID" "OpenAI4S returned an invalid local sign-in URL."
  emit_url "$client_url" || die "CLIENT_URL_INVALID" "The local sign-in URL could not be encoded safely."
  ;;

stop)
  require_non_root_wsl2
  if [ ! -L "$ACTIVE_RUNTIME" ] || [ ! -L "$ACTIVE_SOURCE" ]; then
    json_ok "state|s|not-installed" "running|b|0" "forced|b|0"
    exit 0
  fi
  new_work
  setup_environment "" ""
  run_cli stop >"$WORK_DIR/stop.out" 2>"$WORK_DIR/stop.err"
  rc=$?
  case "$rc" in
    0) json_ok "state|s|stopped" "running|b|0" "forced|b|0" ;;
    1) json_ok "state|s|already-stopped" "running|b|0" "forced|b|0" ;;
    *)
      run_cli stop --force >"$WORK_DIR/force.out" 2>"$WORK_DIR/force.err" \
        || die "DAEMON_STOP_FAILED" "The Leo daemon did not stop after its bounded force-stop." "Open Diagnostics; other WSL workloads were left untouched."
      json_ok "state|s|stopped" "running|b|0" "forced|b|1"
      ;;
  esac
  ;;

doctor)
  require_non_root_wsl2
  new_work
  setup_environment "" ""
  run_cli doctor --json >"$WORK_DIR/doctor.json" 2>"$WORK_DIR/doctor.err"
  verdict=$?
  [ "$verdict" -le 2 ] || die "DOCTOR_FAILED" "OpenAI4S doctor could not run."
  LEO_ACTION="$ACTION" LEO_REPORT="$WORK_DIR/doctor.json" LEO_VERDICT="$verdict" python3 -I -c '
import json, os
with open(os.environ["LEO_REPORT"], "r", encoding="utf-8") as f:
    report = json.load(f)
print(json.dumps({"schema": 1, "ok": True, "action": os.environ["LEO_ACTION"], "data": {"verdict": int(os.environ["LEO_VERDICT"]), "report": report}}, separators=(",", ":")))
' || die "DOCTOR_FAILED" "OpenAI4S doctor returned malformed data."
  EMITTED=1
  ;;

smoke)
  require_non_root_wsl2
  [ "$#" -eq 2 ] || die "INVALID_ARGUMENT" "smoke needs a revision selector and temporary-data flag."
  revision="$1"
  temporary="$2"
  [ -z "$revision" ] || valid_revision "$revision" || die "SOURCE_METADATA_INVALID" "The smoke-test source revision is invalid."
  case "$temporary" in 0|1) ;; *) die "INVALID_ARGUMENT" "The smoke-test data mode is invalid." ;; esac
  new_work
  if [ "$temporary" = "1" ]; then smoke_data="$WORK_DIR/data"; else smoke_data=""; fi
  setup_environment "$revision" "$smoke_data"
  run_smoke_isolated "$PY" -m openai4s --version \
    >"$WORK_DIR/version.out" 2>"$WORK_DIR/version.err" \
    || die "SOURCE_RUNTIME_INCOMPATIBLE" "The staged source is incompatible with the bundled runtime."
  run_smoke_isolated "$PY" -c '
import numpy as np
from scipy import linalg, optimize
import pandas as pd
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression
a = np.array([[2.0, 1.0], [1.0, 2.0]])
assert np.allclose(a @ np.linalg.inv(a), np.eye(2))
assert np.allclose(linalg.solve(a, np.array([3.0, 3.0])), [1.0, 1.0])
assert optimize.minimize(lambda x: float((x[0] - 2.0) ** 2), [0.0]).success
assert int(pd.DataFrame({"x": [1, 2, 3]}).x.sum()) == 6
png = Path("/tmp/leo-science.png")
fig = plt.figure(); plt.plot([0, 1], [0, 1]); fig.savefig(png, format="png"); plt.close(fig)
payload = png.read_bytes()
assert len(payload) > 100 and payload.startswith(b"\x89PNG\r\n\x1a\n")
model = LinearRegression().fit([[0], [1], [2]], [1, 3, 5])
assert abs(float(model.coef_[0]) - 2.0) < 1e-8
import openai4s
' >"$WORK_DIR/science.out" 2>"$WORK_DIR/science.err" || die "SCIENCE_SMOKE_FAILED" "The isolated scientific runtime smoke test failed."
  run_smoke_isolated /usr/bin/env OPENAI_API_KEY=leo-smoke-sentinel \
    LEO_CELL_WORKSPACE=/tmp/openai4s-cell "$PY" -c '
import json
import os
from pathlib import Path

from openai4s.kernel import Kernel

workspace = Path(os.environ["LEO_CELL_WORKSPACE"]).resolve()
workspace.mkdir(parents=True)
assert os.environ.get("OPENAI4S_KERNEL_SANDBOX") == "enforce"
with Kernel(cwd=str(workspace)) as kernel:
    status = kernel.sandbox_status
    assert status["mode"] == "enforce"
    assert status["state"] == "enabled"
    assert status["backend"] == "bubblewrap"
    assert status["enforced"] is True
    assert status["self_test_passed"] is True
    assert status["network_policy"] == "blocked"
    result = kernel.execute(
        "import os\n"
        "from pathlib import Path\n"
        "assert \"OPENAI_API_KEY\" not in os.environ\n"
        "value = sum(number * number for number in range(6))\n"
        "Path(\"cell-result.txt\").write_text(str(value), encoding=\"utf-8\")\n"
        "print(f\"leo-openai4s-cell:{value}\")\n",
        origin="user_repl",
    )
assert result.get("error") is None, result.get("error")
assert result.get("stdout", "").strip() == "leo-openai4s-cell:55"
assert (workspace / "cell-result.txt").read_text(encoding="utf-8") == "55"
print(json.dumps({"cell": "passed", "sandbox": status}, sort_keys=True))
' >"$WORK_DIR/openai4s-cell.out" 2>"$WORK_DIR/openai4s-cell.err" || die "OPENAI4S_CELL_SMOKE_FAILED" "A real OpenAI4S Cell did not execute inside the enforced sandbox."

  # Exercise the complete staged CLI lifecycle on a random non-production
  # loopback port.  Every candidate-code process sees a clean environment, a
  # hidden WSL home/Windows mount, and tmpfs-only state.  Bubblewrap remains the
  # trusted outer supervisor if status/url/stop are broken or the bridge dies.
  smoke_port=""
  selection_count=0
  while [ "$selection_count" -lt 10 ]; do
    candidate_port="$(python3 -I -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')" \
      || die "TEMP_SERVER_SMOKE_FAILED" "A temporary loopback port could not be selected."
    case "$candidate_port" in ''|*[!0-9]*) die "TEMP_SERVER_SMOKE_FAILED" "The temporary loopback port was invalid." ;; esac
    if [ "$candidate_port" -ge 1024 ] && [ "$candidate_port" -le 65535 ] \
      && [ "$candidate_port" -ne 8760 ] && loopback_port_closed "$candidate_port"; then
      smoke_port="$candidate_port"
      break
    fi
    selection_count=$((selection_count + 1))
  done
  [ -n "$smoke_port" ] \
    || die "TEMP_SERVER_SMOKE_FAILED" "No safe temporary loopback port was available."
  smoke_path="$RUNTIME/runtime/bin:$RUNTIME/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

  bwrap --die-with-parent --new-session --unshare-pid --unshare-ipc --unshare-uts --unshare-net \
    --ro-bind / / --dev /dev --proc /proc \
    --tmpfs /home --tmpfs /root --tmpfs /mnt --tmpfs /media --tmpfs /run --tmpfs /tmp \
    --dir "$RUNTIME" --ro-bind "$RUNTIME" "$RUNTIME" \
    --dir "$SOURCE" --ro-bind "$SOURCE" "$SOURCE" \
    --dir /tmp/home --dir /tmp/python-user --dir /tmp/matplotlib --dir /tmp/doctor-data \
    --clearenv --setenv HOME /tmp/home --setenv TMPDIR /tmp \
    --setenv PATH "$smoke_path" --setenv PYTHONPATH "$SOURCE" \
    --setenv PYTHONUSERBASE /tmp/python-user --setenv MPLBACKEND Agg \
    --setenv MPLCONFIGDIR /tmp/matplotlib --setenv OPENAI4S_DATA_DIR /tmp/doctor-data \
    --setenv OPENAI4S_HOST 127.0.0.1 --setenv OPENAI4S_PORT "$smoke_port" \
    --setenv OPENAI4S_NO_OPEN 1 --setenv OPENAI4S_KERNEL_SANDBOX enforce \
    --setenv OPENAI4S_SECRET_STORE env --setenv OPENAI4S_SECRET_ENV 1 \
    --setenv OPENAI4S_SKILLS_DIR "$SOURCE/skills" \
    --setenv OPENAI4S_LLM_PROVIDER chatgpt \
    --setenv OPENAI4S_LLM_MODEL leo-smoke-model \
    --setenv OPENAI4S_LLM_BASE_URL https://api.openai.com/v1 \
    --setenv OPENAI4S_LLM_API_KEY leo-smoke-synthetic-placeholder \
    -- "$PY" -m openai4s doctor --json \
    >"$WORK_DIR/smoke-doctor.json" 2>"$WORK_DIR/smoke-doctor.err"
  doctor_rc=$?
  [ "$doctor_rc" -le 1 ] || die "TEMP_DOCTOR_SMOKE_FAILED" "OpenAI4S doctor rejected the staged source."
  python3 -I -c '
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert isinstance(value, dict)
assert value.get("status") in {"ok", "warn"}
checks = value.get("checks")
assert isinstance(checks, list)
assert all(isinstance(check, dict) and check.get("status") != "fail" for check in checks)
' \
    "$WORK_DIR/smoke-doctor.json" >/dev/null 2>&1 \
    || die "TEMP_DOCTOR_SMOKE_FAILED" "OpenAI4S doctor returned a failed or malformed staged-source report."
  if grep -F "leo-smoke-synthetic-placeholder" "$WORK_DIR/smoke-doctor.json" "$WORK_DIR/smoke-doctor.err" >/dev/null 2>&1; then
    die "TEMP_DOCTOR_SMOKE_FAILED" "OpenAI4S doctor exposed credential material in its output."
  fi

  bwrap --die-with-parent --new-session --unshare-pid --unshare-ipc --unshare-uts \
    --ro-bind / / --dev /dev --proc /proc \
    --tmpfs /home --tmpfs /root --tmpfs /mnt --tmpfs /media --tmpfs /run --tmpfs /tmp \
    --dir "$RUNTIME" --ro-bind "$RUNTIME" "$RUNTIME" \
    --dir "$SOURCE" --ro-bind "$SOURCE" "$SOURCE" \
    --dir /tmp/home --dir /tmp/python-user --dir /tmp/matplotlib --dir /tmp/server-data \
    --clearenv --setenv HOME /tmp/home --setenv TMPDIR /tmp \
    --setenv PATH "$smoke_path" --setenv PYTHONPATH "$SOURCE" \
    --setenv PYTHONUSERBASE /tmp/python-user --setenv MPLBACKEND Agg \
    --setenv MPLCONFIGDIR /tmp/matplotlib --setenv OPENAI4S_DATA_DIR /tmp/server-data \
    --setenv OPENAI4S_HOST 127.0.0.1 --setenv OPENAI4S_PORT "$smoke_port" \
    --setenv OPENAI4S_NO_OPEN 1 --setenv OPENAI4S_KERNEL_SANDBOX enforce \
    --setenv OPENAI4S_SECRET_STORE env --setenv OPENAI4S_SECRET_ENV 1 \
    --setenv OPENAI4S_SKILLS_DIR "$SOURCE/skills" \
    --setenv OPENAI4S_LLM_PROVIDER chatgpt \
    --setenv OPENAI4S_LLM_MODEL leo-smoke-model \
    --setenv OPENAI4S_LLM_BASE_URL https://api.openai.com/v1 \
    --setenv OPENAI4S_LLM_API_KEY leo-smoke-synthetic-placeholder \
    -- /usr/bin/python3 -I -c '
import http.client
import json
import os
import selectors
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qsl, urlsplit

python_bin = sys.argv[1]
port = int(sys.argv[2])
command = [python_bin, "-m", "openai4s"]
server = None
stage = "start"


def run_cli(*arguments, timeout):
    process = subprocess.Popen(
        [*command, *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, True)
    selector.register(process.stderr, selectors.EVENT_READ, False)
    payload = bytearray()
    sizes = {True: 0, False: 0}
    deadline = time.monotonic() + timeout
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired([*command, *arguments], timeout)
            for key, _ in selector.select(min(remaining, 0.2)):
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                capture = bool(key.data)
                sizes[capture] += len(chunk)
                if sizes[capture] > 65536:
                    raise RuntimeError("oversized CLI output")
                if capture:
                    payload.extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired([*command, *arguments], timeout)
        return process.wait(timeout=remaining), bytes(payload)
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    finally:
        selector.close()
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()


def port_closed():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        return probe.connect_ex(("127.0.0.1", port)) != 0


failed = True
try:
    server = subprocess.Popen(
        [*command, "serve", "--host", "127.0.0.1", "--port", str(port), "--no-browser"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    # The staged stop command detects exit via kill(0).  Reap the foreground
    # child concurrently so a cleanly stopped server is not mistaken for a
    # still-live zombie owned by this supervisor.
    reaper = threading.Thread(target=server.wait, name="leo-smoke-reaper", daemon=True)
    reaper.start()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("server exited during startup")
        try:
            status_rc, _ = run_cli("status", timeout=2)
        except subprocess.TimeoutExpired:
            status_rc = -1
        if status_rc == 0:
            break
        time.sleep(0.2)
    else:
        raise RuntimeError("status never became ready")

    stage = "url"
    url_rc, url_payload = run_cli("url", timeout=5)
    if url_rc != 0:
        raise RuntimeError("url command failed")
    lines = url_payload.decode("utf-8", "strict").splitlines()
    urls = [line.strip() for line in lines if line.strip().startswith("http://")]
    if len(urls) != 1:
        raise RuntimeError("url command returned an invalid count")
    parsed = urlsplit(urls[0])
    query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    if not (
        parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "localhost"}
        and parsed.port == port
        and parsed.path == "/"
        and not parsed.fragment
        and parsed.username is None
        and parsed.password is None
        and len(query) == 1
        and query[0][0] == "token"
        and query[0][1]
    ):
        raise RuntimeError("url command returned an unsafe URL")

    stage = "health"
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", "/health", headers={"Host": f"127.0.0.1:{port}"})
        response = connection.getresponse()
        body = response.read(65537)
    finally:
        connection.close()
    if response.status != 200 or len(body) > 65536:
        raise RuntimeError("health response was invalid")
    health = json.loads(body)
    if not (
        isinstance(health, dict)
        and health.get("status") == "ok"
        and isinstance(health.get("model"), str)
        and health["model"].strip()
    ):
        raise RuntimeError("health payload was invalid")

    stage = "stop-command"
    stop_rc, _ = run_cli("stop", timeout=15)
    if stop_rc != 0:
        raise RuntimeError("stop command failed")
    stage = "server-exit"
    server.wait(timeout=15)
    stage = "stopped-status"
    status_rc, _ = run_cli("status", timeout=5)
    if status_rc != 1:
        raise RuntimeError("status still reported a running server")
    stage = "port-release"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and not port_closed():
        time.sleep(0.1)
    if not port_closed():
        raise RuntimeError("server port remained open")
    failed = False
except BaseException:
    pass
finally:
    if server is not None and server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

if failed:
    print("staged lifecycle failed at " + stage, file=sys.stderr)
    raise SystemExit(1)
print(json.dumps({"health": True, "status": True, "stop": True, "url": True}, separators=(",", ":")))
' "$PY" "$smoke_port" \
    >"$WORK_DIR/smoke-lifecycle.json" 2>"$WORK_DIR/smoke-lifecycle.err" &
  SMOKE_SERVER_PID=$!
  SMOKE_SERVER_PORT="$smoke_port"
  SMOKE_SERVER_START="$(awk '{print $22}' "/proc/$SMOKE_SERVER_PID/stat" 2>/dev/null || true)"
  case "$SMOKE_SERVER_START" in
    ''|*[!0-9]*)
      wait "$SMOKE_SERVER_PID" 2>/dev/null || true
      SMOKE_SERVER_PID=""
      SMOKE_SERVER_PORT=""
      SMOKE_SERVER_START=""
      die "TEMP_SERVER_SMOKE_FAILED" "The lifecycle supervisor failed to start."
      ;;
  esac
  lifecycle_rc=0
  wait "$SMOKE_SERVER_PID" || lifecycle_rc=$?
  SMOKE_SERVER_PID=""
  SMOKE_SERVER_START=""
  if [ "$lifecycle_rc" -ne 0 ]; then
    lifecycle_stage=""
    IFS= read -r lifecycle_failure < "$WORK_DIR/smoke-lifecycle.err" || true
    case "$lifecycle_failure" in
      "staged lifecycle failed at start") lifecycle_stage="startup/status" ;;
      "staged lifecycle failed at url") lifecycle_stage="authenticated URL" ;;
      "staged lifecycle failed at health") lifecycle_stage="health" ;;
      "staged lifecycle failed at stop-command") lifecycle_stage="stop command" ;;
      "staged lifecycle failed at server-exit") lifecycle_stage="server shutdown" ;;
      "staged lifecycle failed at stopped-status") lifecycle_stage="post-stop status" ;;
      "staged lifecycle failed at port-release") lifecycle_stage="port release" ;;
      *) lifecycle_stage="supervisor" ;;
    esac
    die "TEMP_SERVER_SMOKE_FAILED" "The staged lifecycle check failed during $lifecycle_stage."
  fi
  loopback_port_closed "$smoke_port" \
    || die "TEMP_SERVER_SMOKE_FAILED" "The supervised staged-source server left its temporary port open."
  SMOKE_SERVER_PORT=""
  python3 -I -c '
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value == {"health": True, "status": True, "stop": True, "url": True}
' "$WORK_DIR/smoke-lifecycle.json" >/dev/null 2>&1 \
    || die "TEMP_SERVER_SMOKE_FAILED" "The staged lifecycle supervisor returned malformed results."
  selected="$(basename "$SOURCE")"
  json_ok "state|s|passed" "revision|s|$selected" "sandbox|s|enforce" "openai4s_cell|b|1" "doctor|b|1" "temporary_server|b|1" "temporary_port|i|$smoke_port" "temporary_data|b|$temporary"
  ;;

backup-data)
  require_non_root_wsl2
  new_work
  refuse_running_daemon
  mkdir -p "$BACKUPS_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its WSL backup directory."
  backup_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
  target="$BACKUPS_DIR/$backup_id"
  [ ! -e "$target" ] || die "BACKUP_COLLISION" "A data backup identifier already exists."
  mkdir "$target" || die "BACKUP_FAILED" "The data backup could not be created."
  copy_clean_tree "$DATA_DIR" "$target/data" || die "BACKUP_FAILED" "The WSL data backup failed."
  printf '{"schema":1,"backup_id":"%s"}\n' "$backup_id" > "$target/leo-backup.json" || die "BACKUP_FAILED" "The backup manifest could not be written."
  json_ok "state|s|created" "backup_id|s|$backup_id"
  ;;

restore-data)
  require_non_root_wsl2
  [ "$#" -eq 1 ] || die "INVALID_ARGUMENT" "restore-data needs one backup identifier."
  backup_id="$1"
  valid_id "$backup_id" || die "INVALID_BACKUP" "The backup identifier is invalid."
  source_backup="$BACKUPS_DIR/$backup_id"
  [ -f "$source_backup/leo-backup.json" ] && [ -d "$source_backup/data" ] || die "BACKUP_NOT_FOUND" "The selected WSL data backup does not exist."
  new_work
  refuse_running_daemon
  copy_clean_tree "$source_backup/data" "$WORK_DIR/data" || die "RESTORE_FAILED" "The selected WSL data backup could not be read."
  if path_present "$DATA_DIR"; then
    [ -d "$DATA_DIR" ] && [ ! -L "$DATA_DIR" ] || die "RESTORE_FAILED" "The current WSL data path is not a safe directory."
  else
    mkdir -p "$DATA_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its WSL data directory."
  fi
  begin_rc=0
  begin_data_transaction "$WORK_DIR/data" || begin_rc=$?
  case "$begin_rc" in
    0) ;;
    2) die "DATA_TRANSACTION_BUSY" "Another Leo data transaction is still running." "Wait for the current import or restore operation to finish, then retry." ;;
    *) die "RESTORE_FAILED" "The WSL data restoration transaction could not be prepared." ;;
  esac
  activate_data_transaction || die "RESTORE_FAILED" "The WSL data backup could not be activated safely."
  json_ok "state|s|restored" "backup_id|s|$backup_id"
  ;;

export)
  require_non_root_wsl2
  [ "$#" -eq 1 ] || die "INVALID_ARGUMENT" "export needs one destination archive path."
  destination="$1"
  new_work
  refuse_running_daemon
  mkdir -p "$DATA_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot read its WSL data directory."
  python3 -I - "$DATA_DIR" "$destination" >"$WORK_DIR/export.count" <<'PY' || die "EXPORT_FAILED" "Leo could not create the data export archive."
import datetime
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

source, destination = map(Path, sys.argv[1:])

def excluded(relative):
    parts = [part.lower() for part in relative.parts]
    if not parts:
        return False
    if "logs" in parts:
        return True
    name = parts[-1]
    return (
        name in {
            ".env",
            "access-token",
            "worker-bootstrap-secret",
            "openai4s.pid",
            "daemon.json",
            "app.out",
            "app.err",
        }
        or name.startswith(".access-token.tmp-")
        or name.startswith(".worker-bootstrap-secret.tmp-")
        or name.endswith(".pid")
        or name.endswith(".log")
        or ".log." in name
        or name.startswith("app.out.")
        or name.startswith("app.err.")
    )

destination.parent.mkdir(parents=True, exist_ok=True)
temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
files = []
try:
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for item in sorted(source.rglob("*")):
            if not item.is_file() or item.is_symlink():
                continue
            relative = item.relative_to(source)
            if excluded(relative):
                continue
            digest = hashlib.sha256()
            with item.open("rb") as f:
                for block in iter(lambda: f.read(1024 * 1024), b""):
                    digest.update(block)
            archive_name = "data/" + relative.as_posix()
            zf.write(item, archive_name)
            files.append({"path": archive_name, "sha256": digest.hexdigest(), "size": item.stat().st_size})
        manifest = {"schema": 1, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "files": files}
        zf.writestr("leo-export.json", json.dumps(manifest, separators=(",", ":")))
    os.replace(temporary, destination)
finally:
    try: temporary.unlink()
    except FileNotFoundError: pass
print(len(files))
PY
  count="$(cat "$WORK_DIR/export.count")"
  digest="$(sha256sum "$destination" | awk '{print $1}')"
  json_ok "state|s|exported" "files|i|$count" "sha256|s|$digest"
  ;;

import)
  require_non_root_wsl2
  [ "$#" -eq 1 ] || die "INVALID_ARGUMENT" "import needs one source archive path."
  archive="$1"
  [ -f "$archive" ] || die "IMPORT_MISSING" "The selected data archive is not readable from WSL."
  new_work
  refuse_running_daemon
  extracted="$WORK_DIR/extracted"
  python3 -I - "$archive" "$extracted" <<'PY' || die "IMPORT_UNSAFE" "The data archive is invalid, damaged, or contains an unsafe path."
import hashlib
import json
import os
import posixpath
import stat
import sys
import zipfile
from pathlib import Path

archive, destination = Path(sys.argv[1]), Path(sys.argv[2])
destination.mkdir(mode=0o700)

def clean(name):
    if not name or "\\" in name or name.startswith("/"):
        raise ValueError("unsafe path")
    value = posixpath.normpath(name)
    if value == ".." or value.startswith("../"):
        raise ValueError("path traversal")
    return value

def excluded(name):
    parts = [part.lower() for part in name.split("/")]
    if parts and parts[0] == "data":
        parts = parts[1:]
    if not parts:
        return False
    if "logs" in parts:
        return True
    leaf = parts[-1]
    return (
        leaf in {
            ".env",
            "access-token",
            "worker-bootstrap-secret",
            "openai4s.pid",
            "daemon.json",
            "app.out",
            "app.err",
        }
        or leaf.startswith(".access-token.tmp-")
        or leaf.startswith(".worker-bootstrap-secret.tmp-")
        or leaf.endswith(".pid")
        or leaf.endswith(".log")
        or ".log." in leaf
        or leaf.startswith("app.out.")
        or leaf.startswith("app.err.")
    )

with zipfile.ZipFile(archive) as zf:
    infos = zf.infolist()
    if len(infos) > 200_000 or sum(info.file_size for info in infos) > 8 * 1024**3:
        raise ValueError("archive too large")
    names = [clean(info.filename) for info in infos]
    if len(set(names)) != len(names) or "leo-export.json" not in names:
        raise ValueError("missing manifest or duplicate names")
    manifest = json.loads(zf.read("leo-export.json"))
    if manifest.get("schema") != 1 or not isinstance(manifest.get("files"), list):
        raise ValueError("unsupported manifest")
    expected = {item["path"]: item for item in manifest["files"]}
    if len(expected) != len(manifest["files"]):
        raise ValueError("duplicate manifest path")
    actual = {name for name in names if name != "leo-export.json" and not name.endswith("/")}
    if actual != set(expected):
        raise ValueError("manifest does not match archive")
    for info, name in zip(infos, names):
        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            raise ValueError("symbolic link")
        if name == "leo-export.json" or name.endswith("/"):
            continue
        if not name.startswith("data/") or excluded(name):
            raise ValueError("forbidden data path")
        target = destination.joinpath(*name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"): flags |= os.O_NOFOLLOW
        fd = os.open(target, flags, 0o600)
        with zf.open(info) as source, os.fdopen(fd, "wb") as output:
            while True:
                block = source.read(1024 * 1024)
                if not block: break
                digest.update(block); output.write(block)
        item = expected[name]
        if digest.hexdigest() != item.get("sha256") or target.stat().st_size != item.get("size"):
            raise ValueError("file digest mismatch")
PY
  [ -d "$extracted/data" ] || mkdir "$extracted/data"
  if path_present "$DATA_DIR"; then
    [ -d "$DATA_DIR" ] && [ ! -L "$DATA_DIR" ] || die "IMPORT_FAILED" "The current WSL data path is not a safe directory."
  else
    mkdir -p "$DATA_DIR" || die "DATA_DIR_UNWRITABLE" "Leo cannot create its WSL data directory."
  fi
  begin_rc=0
  begin_data_transaction "$extracted/data" || begin_rc=$?
  case "$begin_rc" in
    0) ;;
    2) die "DATA_TRANSACTION_BUSY" "Another Leo data transaction is still running." "Wait for the current import or restore operation to finish, then retry." ;;
    *) die "IMPORT_FAILED" "The data import transaction could not be prepared." ;;
  esac
  activate_data_transaction || die "IMPORT_FAILED" "The imported WSL data could not be activated safely."
  json_ok "state|s|imported"
  ;;
esac
