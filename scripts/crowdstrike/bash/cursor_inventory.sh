#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# cursor_inventory.sh
# SCRIPT_VERSION: 1.2.0
# Inventory Cursor account + plan + security-relevant metadata from the local
# SQLite state DB. Run via Falcon RTR (root). macOS + Linux. Enumerates ALL
# user profiles (RTR runs as root/SYSTEM, not the logged-in user).
#
# SECURITY: token VALUES are never emitted. For the access token we decode and
# emit only the JWT 'exp' (expiry) + presence flags. Refresh token = presence only.
#
# OUTPUT: one compact JSON object per Cursor profile found (JSON-lines).
#
# This file follows the shared 5-section layout (see ARCHITECTURE.md):
#   1 HEADER · 2 SHARED PRELUDE · 3 DISCOVERY · 4 COLLECT · 5 EMIT

# ─────────────────────────────────────────────────────────────────────────────
# 2. SHARED PRELUDE — keep byte-identical across all bash collectors
#    (generic helpers only; if you edit this block, paste it into the others)
# ─────────────────────────────────────────────────────────────────────────────
set -u   # error on use of an unset variable — catches typos early

OS="$(uname -s)"
HOST="$(hostname 2>/dev/null)"

# json_escape VALUE -> stdout with backslashes/quotes escaped and CR/LF stripped,
# so the result is safe to drop between the quotes of a JSON string.
json_escape() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\r\n'; }

# file_epoch PATH -> file mtime as unix seconds. Tries GNU stat, then BSD stat.
file_epoch() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null; }
# epoch_iso EPOCH -> that unix time as UTC ISO-8601. Tries GNU date, then BSD date.
epoch_iso() { [ -n "$1" ] && { date -u -d "@$1" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -r "$1" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null; }; }

# --- JSON line builder -------------------------------------------------------
# Instead of one giant printf with dozens of positional args, build the object
# one field at a time into a buffer, then emit it. Add/remove/reorder fields by
# editing one readable line each.
_json_buf=""
json_reset() { _json_buf=""; }
# json_str KEY VALUE  -> append  "KEY":"escaped-value"   (use for text)
json_str() { local s=""; [ -n "$_json_buf" ] && s=","; _json_buf="${_json_buf}${s}\"$1\":\"$(json_escape "$2")\""; }
# json_raw KEY LITERAL -> append  "KEY":LITERAL          (use for numbers / true / false)
json_raw() { local s=""; [ -n "$_json_buf" ] && s=","; _json_buf="${_json_buf}${s}\"$1\":$2"; }
# json_emit -> print the accumulated object as one line, then clear the buffer
json_emit() { printf '{%s}\n' "$_json_buf"; json_reset; }

# enumerate_homes -> fill the HOMES[] array with every user profile directory.
# Returns 1 on an unsupported OS so the caller can emit its own product error.
enumerate_homes() {
  HOMES=()
  case "$OS" in
    Darwin) for d in /Users/*; do [ -d "$d" ] && HOMES+=("$d"); done ;;
    Linux)  for d in /home/*; do [ -d "$d" ] && HOMES+=("$d"); done; [ -d /root ] && HOMES+=("/root") ;;
    *) return 1 ;;
  esac
  return 0
}

# --- Secret-pattern scan (skills / memory / rules files) --------------------
# service<TAB>ERE-pattern. Flags credential-SHAPED strings by pattern only —
# never captures or emits the matched substring, just which service it maps to
# and where (file + line number). Extend this table to add new services.
SECRET_PATTERNS='aws_access_key	AKIA[0-9A-Z]{16}
github_token	gh[pousr]_[A-Za-z0-9]{20,}
github_fine_grained	github_pat_[A-Za-z0-9_]{60,}
slack_token	xox[baprs]-[A-Za-z0-9-]{10,}
slack_webhook	hooks\.slack\.com/services/T[0-9A-Za-z]+/B[0-9A-Za-z]+/[0-9A-Za-z]+
openai_key	sk-[A-Za-z0-9]{20,}
anthropic_key	sk-ant-[A-Za-z0-9_-]{20,}
google_api_key	AIza[0-9A-Za-z_-]{35}
stripe_key	(sk|pk)_live_[0-9A-Za-z]{20,}
sendgrid_key	SG\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}
npm_token	npm_[A-Za-z0-9]{30,}
private_key_block	-----BEGIN[A-Z ]*PRIVATE KEY-----
jwt	eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+
generic_credential	(api[_-]?key|apikey|secret|token|password)[[:space:]]*[:=][[:space:]]*[A-Za-z0-9_-]{16,}'

# scan_secrets_file PATH -> print "service<TAB>lineno" per match, one per line.
# Never prints the matched text, only which pattern matched and where. Skips
# unreadable files and anything over 512KB (skill/rule/memory files are prose,
# not the kind of thing that's legitimately huge).
scan_secrets_file() {
  local f="$1" sz
  [ -f "$f" ] && [ -r "$f" ] || return 0
  sz="$(stat -f %z "$f" 2>/dev/null || stat -c %s "$f" 2>/dev/null || echo 0)"
  [ "${sz:-0}" -gt 524288 ] && return 0
  local svc pat
  while IFS=$'\t' read -r svc pat; do
    [ -z "$svc" ] && continue
    grep -EnI -e "$pat" "$f" 2>/dev/null | cut -d: -f1 | while IFS= read -r ln; do
      [ -n "$ln" ] && printf '%s\t%s\n' "$svc" "$ln"
    done
  done <<< "$SECRET_PATTERNS"
}

# scan_secrets_paths PATH... -> sets SECRETS_JSON (compact JSON array of
# {"file","service","line"}) and SECRETS_FILES_SCANNED, capped at
# MAX_SECRET_FINDINGS total findings so one noisy file can't blow up output.
MAX_SECRET_FINDINGS=50
scan_secrets_paths() {
  SECRETS_JSON="[]"; SECRETS_FILES_SCANNED=0
  local arr="" first=1 count=0 f svc ln
  for f in "$@"; do
    [ -f "$f" ] || continue
    SECRETS_FILES_SCANNED=$((SECRETS_FILES_SCANNED+1))
    while IFS=$'\t' read -r svc ln; do
      [ -z "$svc" ] && continue
      [ "$count" -ge "$MAX_SECRET_FINDINGS" ] && continue
      [ "$first" -eq 0 ] && arr="${arr},"
      arr="${arr}{\"file\":\"$(json_escape "$f")\",\"service\":\"$(json_escape "$svc")\",\"line\":$ln}"
      first=0; count=$((count+1))
    done < <(scan_secrets_file "$f")
  done
  SECRETS_JSON="[${arr}]"
}
# ===== END SHARED PRELUDE =====

# ─────────────────────────────────────────────────────────────────────────────
# 3. DISCOVERY — locate Cursor's state DB(s) and app version for one profile
# ─────────────────────────────────────────────────────────────────────────────

# cursor_version -> the installed Cursor app version (best effort), else "".
cursor_version() {
  case "$OS" in
    Darwin)
      [ -f "/Applications/Cursor.app/Contents/Info.plist" ] && \
        /usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" \
          "/Applications/Cursor.app/Contents/Info.plist" 2>/dev/null && return
      ;;
    Linux)
      for pj in /opt/Cursor/resources/app/package.json /usr/share/cursor/resources/app/package.json \
                /usr/lib/cursor/resources/app/package.json; do
        [ -f "$pj" ] && { grep -Eo '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$pj" \
          | head -1 | sed -E 's/.*"([^"]*)"$/\1/'; return; }
      done
      ;;
  esac
}

# discover_dbs HOME -> print each Cursor state.vscdb path for that profile.
# Strategy: known default locations first (fast common case); only if none of
# those exist do we fall back to a bounded, pruned search.
discover_dbs() {
  local H="$1" found_any=0 p; local cands=()
  case "$OS" in
    Darwin) cands+=("$H/Library/Application Support/Cursor/User/globalStorage/state.vscdb") ;;
    Linux)
      cands+=("$H/.config/Cursor/User/globalStorage/state.vscdb")
      [ -n "${XDG_CONFIG_HOME:-}" ] && cands+=("$XDG_CONFIG_HOME/Cursor/User/globalStorage/state.vscdb")
      cands+=("$H/.var/app/sh.cursor.Cursor/config/Cursor/User/globalStorage/state.vscdb")  # Flatpak
      cands+=("$H/.var/app/co.anysphere.cursor/config/Cursor/User/globalStorage/state.vscdb")
      cands+=("$H/snap/cursor/current/.config/Cursor/User/globalStorage/state.vscdb")        # Snap
      for p in "$H"/snap/cursor/*/.config/Cursor/User/globalStorage/state.vscdb; do [ -f "$p" ] && cands+=("$p"); done
      ;;
  esac
  for p in "${cands[@]}"; do [ -f "$p" ] && { printf '%s\n' "$p"; found_any=1; }; done
  [ "$found_any" -eq 1 ] && return 0
  # Fallback: search the profile, pruning big/noisy dirs, bounded to depth 7.
  find "$H" -maxdepth 7 \
    \( -name node_modules -o -name .git -o -name Caches -o -name Cache -o -name .Trash \) -prune -o \
    -type f -name 'state.vscdb' -path '*Cursor*globalStorage*' -print 2>/dev/null
}

# cursor_secret_targets HOME -> candidate secret-scan file paths for one
# profile: global .cursorrules + .cursor/rules + .cursor/skills-cursor +
# .cursor/memory. Global scope only — Cursor doesn't track a project list we
# can cheaply reuse (unlike Claude's projects), so per-project .cursorrules/
# .cursor/rules files are out of scope.
cursor_secret_targets() {
  local H="$1"
  [ -f "$H/.cursorrules" ] && printf '%s\n' "$H/.cursorrules"
  find "$H/.cursor/rules" "$H/.cursor/skills-cursor" "$H/.cursor/memory" \
    -maxdepth 4 -type f \( -name '*.md' -o -name '*.mdc' \) 2>/dev/null
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — read the fields for one profile's DB (+ small read helpers)
# ─────────────────────────────────────────────────────────────────────────────

# strip_quotes -> remove one leading and trailing double-quote, if present.
strip_quotes() { local s="$1"; s="${s#\"}"; s="${s%\"}"; printf '%s' "$s"; }
# bool VALUE -> "true" if VALUE is non-empty, else "false" (a JSON literal).
bool() { [ -n "$1" ] && printf 'true' || printf 'false'; }

# b64url_decode STRING -> decode a base64url string (JWT segments use base64url).
# Converts to standard base64, re-pads, then tries GNU base64, BSD base64, openssl.
b64url_decode() {
  local d="$1"; d="${d//-/+}"; d="${d//_//}"
  case $(( ${#d} % 4 )) in 2) d="$d==";; 3) d="$d=";; esac
  printf '%s' "$d" | base64 -d 2>/dev/null || printf '%s' "$d" | base64 -D 2>/dev/null || printf '%s' "$d" | openssl base64 -d -A 2>/dev/null
}
# jwt_exp TOKEN -> the 'exp' (expiry epoch) from a JWT's payload, WITHOUT ever
# emitting the token itself. Empty unless the token looks like header.payload.sig.
jwt_exp() {
  local tok="$1"
  case "$tok" in *.*.*) ;; *) return;; esac
  b64url_decode "$(printf '%s' "$tok" | cut -d. -f2)" 2>/dev/null \
    | grep -Eo '"exp"[[:space:]]*:[[:space:]]*[0-9]+' | grep -Eo '[0-9]+' | head -1
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — process one DB end-to-end: copy, query, derive, build, print
# ─────────────────────────────────────────────────────────────────────────────

# process_db OS_USER DB_PATH HOME_DIR -> emit one JSON line for that Cursor profile.
# Returns 1 (emits nothing) if the DB has no account info worth reporting.
process_db() {
  local user="$1" DB="$2" home_dir="$3"

  # Work on a copy so we never lock or mutate the live DB; bring WAL/SHM too.
  local TMP; TMP="$(mktemp -d)" || return 1
  cp "$DB" "$TMP/state.vscdb" 2>/dev/null || { rm -rf "$TMP"; return 1; }
  [ -f "$DB-wal" ] && cp "$DB-wal" "$TMP/state.vscdb-wal" 2>/dev/null
  [ -f "$DB-shm" ] && cp "$DB-shm" "$TMP/state.vscdb-shm" 2>/dev/null

  # q KEY -> the value stored under that ItemTable key (Cursor's key/value store).
  # Two readers, one interface: the sqlite3 CLI when present, else python3's stdlib
  # sqlite3 module (needs no external binary). Both open the copied DB with its
  # -wal/-shm sidecars alongside, so fresh (un-checkpointed) writes are merged, not lost.
  if [ "$READER" = "sqlite3" ]; then
    q() { "$SQLITE" "$TMP/state.vscdb" "SELECT value FROM ItemTable WHERE key='$1';" 2>/dev/null; }
  else
    # Dump every row once as  key<TAB>base64(value)  so q can look it up locally
    # instead of re-spawning python per key; base64 keeps any value on a single line.
    "$PY" - "$TMP/state.vscdb" >"$TMP/dump.tsv" 2>/dev/null <<'PYEOF'
import sqlite3, sys, base64
con = sqlite3.connect(sys.argv[1])      # read-write on our copy -> WAL auto-merges
con.text_factory = bytes                # raw bytes for TEXT + BLOB, uniformly
out = getattr(sys.stdout, "buffer", sys.stdout)
try:
    for k, v in con.execute("SELECT key, value FROM ItemTable"):
        if v is None: v = b""
        elif not isinstance(v, (bytes, bytearray)): v = str(v).encode("utf-8")
        if isinstance(k, bytes): k = k.decode("utf-8", "replace")
        out.write(k.encode("utf-8") + b"\t" + base64.b64encode(bytes(v)) + b"\n")
finally:
    con.close()
PYEOF
    q() {
      local b
      b="$(awk -v k="$1" -F'\t' '$1==k{print $2; exit}' "$TMP/dump.tsv" 2>/dev/null)"
      [ -z "$b" ] && return 0
      printf '%s' "$b" | base64 -d 2>/dev/null || printf '%s' "$b" | base64 -D 2>/dev/null
    }
  fi

  local email plan joined auth scopes svc_mid tel_mid tel_dev tel_sqm first_sess last_sess cur_sess
  email="$(strip_quotes "$(q 'cursorAuth/cachedEmail')")"
  plan="$(strip_quotes "$(q 'cursorAuth/stripeMembershipType')")"
  joined="$(strip_quotes "$(q 'cursorAuth/onboardingDate')")"
  auth="$(strip_quotes "$(q 'cursorAuth/cachedSignUpType')")"
  scopes="$(strip_quotes "$(q 'cursorAuth/scopes')")"
  svc_mid="$(strip_quotes "$(q 'storage.serviceMachineId')")"
  tel_mid="$(strip_quotes "$(q 'telemetry.machineId')")"
  tel_dev="$(strip_quotes "$(q 'telemetry.devDeviceId')")"
  tel_sqm="$(strip_quotes "$(q 'telemetry.sqmId')")"
  first_sess="$(strip_quotes "$(q 'telemetry.firstSessionDate')")"
  last_sess="$(strip_quotes "$(q 'telemetry.lastSessionDate')")"
  cur_sess="$(strip_quotes "$(q 'telemetry.currentSessionDate')")"

  # Tokens: presence + (access token) expiry only; the values are scrubbed below.
  local at rt at_present rt_present at_exp_epoch at_exp_iso at_expired
  at="$(strip_quotes "$(q 'cursorAuth/accessToken')")"
  rt="$(strip_quotes "$(q 'cursorAuth/refreshToken')")"
  at_present=""; [ -n "$at" ] && at_present=1
  rt_present=""; [ -n "$rt" ] && rt_present=1
  at_exp_epoch="$(jwt_exp "$at")"
  at_exp_iso="$(epoch_iso "$at_exp_epoch")"
  at_expired="false"; [ -n "$at_exp_epoch" ] && [ "$at_exp_epoch" -lt "$(date -u +%s)" ] 2>/dev/null && at_expired="true"
  at=""; rt=""   # scrub token values from memory

  # user_id lives inside a JSON blob under this key; pull just the id, not the blob.
  local raw_local user_id
  raw_local="$(q 'anysphere.cursor-always-local')"
  user_id="$(printf '%s' "$raw_local" | grep -Eo '"(userId|machineId|user_id)"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed -E 's/.*"([^"]*)"$/\1/')"

  # mcp_servers: external data-egress surface. Servers (with structural detail +
  # auth_metadata) are read from config files, when python3 is available:
  #   - GLOBAL  ~/.cursor/mcp.json                 (user scope)
  #   - PROJECT <folder>/.cursor/mcp.json          (project scope) for every folder
  #     Cursor has opened, enumerated from its own workspaceStorage/*/workspace.json
  #     -> a bounded set of known roots, never a filesystem crawl.
  # The DB's mcpService.knownServerIds is intentionally NOT used: it stores
  # scope-mangled ids (user-<name>, project-<n>-<folder>-<name>) that can't be
  # normalized back to the config key and would duplicate config-derived entries.
  # Never emit config or secret env/header VALUES, only names/indicators.
  local mcp_json mcp_count auth_meta_json ws_dir
  ws_dir="$(dirname "$(dirname "$DB")")/workspaceStorage"
  if [ -n "$PY" ]; then
    local _mcp_out
    _mcp_out="$("$PY" - "$home_dir" "$ws_dir" <<'PYEOF'
import json,os,sys,glob,re
from urllib.parse import urlparse, unquote
home, ws_dir = sys.argv[1], sys.argv[2]
# Servers are sourced from config files only (global + project). Cursor's DB
# mcpService.knownServerIds is deliberately NOT unioned in: it stores scope-mangled
# ids (user-<name>, project-<n>-<folder>-<name>) that can't be reliably normalized
# back to the config key (server names contain dashes too) and would duplicate the
# config-derived entries. Config files carry clean names + full enrichment.
configs = {}   # server name -> config dict (first writer wins: global before project)
def ingest(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f: j = json.load(f)
    except Exception:
        return
    for k, v in (j.get("mcpServers") or {}).items():
        if isinstance(v, dict): configs.setdefault(k, v)
ingest(os.path.join(home, ".cursor", "mcp.json"))
seen = set()
for wj in glob.glob(os.path.join(ws_dir, "*", "workspace.json")):
    try:
        with open(wj, encoding="utf-8", errors="replace") as f: meta = json.load(f)
    except Exception:
        continue
    folder = meta.get("folder") or ""
    if folder.startswith("file://"): folder = unquote(folder[7:])
    if folder and folder not in seen and os.path.isdir(folder):
        seen.add(folder); ingest(os.path.join(folder, ".cursor", "mcp.json"))
names = set(configs.keys())
def _fs(a):
    return False if "=" in a else bool(re.match(r'^(/|\./|\.\./|~|[A-Za-z]:\\|\\\\)', a))
servers, auth = [], []
for name in sorted(names):
    cfg = configs.get(name) or {}
    url = cfg.get("url") or cfg.get("baseUrl") or ""
    tr = str(cfg.get("type") or cfg.get("transport") or "").lower()
    if not tr: tr = "http" if url else ("stdio" if cfg.get("command") else "unknown")
    e = {"name": name, "transport": tr}
    if tr == "stdio":
        e["command_present"] = bool(cfg.get("command")); e["arg_count"] = len(cfg.get("args") or [])
    elif tr in ("http", "sse") and url:
        h = urlparse(url).hostname
        if h: e["url_host"] = h
    servers.append(e)
    en = sorted((cfg.get("env") or {}).keys()); hn = sorted((cfg.get("headers") or {}).keys())
    args = [str(a) for a in (cfg.get("args") or [])]; cmd = str(cfg.get("command") or "")
    fp = [a for a in args if not a.startswith("-") and "server-filesystem" not in a and _fs(a)] if "server-filesystem" in " ".join([cmd] + args) else []
    a = {"name": name}
    if en: a["env_var_names"] = en
    if hn: a["header_key_names"] = hn
    if fp: a["filesystem_scope_paths"] = fp
    if len(a) > 1: auth.append(a)
print(json.dumps(servers, separators=(",", ":")))
print(len(servers))
print(json.dumps(auth, separators=(",", ":")))
PYEOF
)"
    mcp_json="$(printf '%s\n' "$_mcp_out" | sed -n '1p')"
    mcp_count="$(printf '%s\n' "$_mcp_out" | sed -n '2p')"
    auth_meta_json="$(printf '%s\n' "$_mcp_out" | sed -n '3p')"
    [ -z "$mcp_json" ] && mcp_json="[]"
    [ -z "$mcp_count" ] && mcp_count=0
    [ -z "$auth_meta_json" ] && auth_meta_json="[]"
  else
    # python3 absent: config files can't be parsed, so MCP enumeration is skipped.
    # (The DB knownServerIds holds only scope-mangled ids that would be misleading
    # name-only entries, so we do not emit them.) Rare — RTR-root normally has python3.
    mcp_json="[]"; auth_meta_json="[]"; mcp_count=0
  fi

  # model: most-frequent non-"default" model across composer sessions (cursorDiskKV).
  # Cursor is multi-model/per-chat, so we surface the dominant explicitly-chosen model
  # ("default" = Cursor auto-select, which isn't a real model name -> skipped).
  local model="" model_raw=""
  if [ "$READER" = "sqlite3" ]; then
    model_raw="$("$SQLITE" "$TMP/state.vscdb" "SELECT value FROM cursorDiskKV WHERE key LIKE 'composerData:%';" 2>/dev/null)"
  elif [ -n "$PY" ]; then
    model_raw="$("$PY" - "$TMP/state.vscdb" 2>/dev/null <<'PYEOF'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
try:
    for row in con.execute("SELECT value FROM cursorDiskKV WHERE key LIKE 'composerData:%'"):
        v = row[0]
        if v is None: continue
        if isinstance(v, (bytes, bytearray)): v = v.decode("utf-8", "replace")
        sys.stdout.write(str(v) + "\n")
finally:
    con.close()
PYEOF
)"
  fi
  if [ -n "$model_raw" ]; then
    model="$(printf '%s' "$model_raw" \
      | grep -Eo '"modelName"[[:space:]]*:[[:space:]]*"[^"]*"' \
      | sed -E 's/.*"([^"]*)"$/\1/' \
      | grep -vx default | grep -vx '' \
      | sort | uniq -c | sort -rn | head -1 | awk '{print $2}')"
  fi

  rm -rf "$TMP"

  # No account identity on this DB -> nothing useful to report.
  [ -z "$email" ] && [ -z "$plan" ] && return 1

  local secret_files=() sf
  while IFS= read -r sf; do secret_files+=("$sf"); done < <(cursor_secret_targets "$home_dir")
  # bash 3.2 (stock macOS) errors on "${arr[@]}" when the array is empty under
  # `set -u`; the ${arr[@]+...} guard expands to nothing instead of aborting.
  scan_secrets_paths ${secret_files[@]+"${secret_files[@]}"}

  # last-used: telemetry.currentSessionDate is the MOST recent app launch;
  # lastSessionDate is the launch BEFORE that (so it understates recency — don't
  # prefer it). Order: current_session -> last_session -> DB file mtime.
  local db_epoch db_iso last_used
  db_epoch="$(file_epoch "$DB")"; db_iso="$(epoch_iso "$db_epoch")"
  last_used="$cur_sess"
  [ -z "$last_used" ] && last_used="$last_sess"
  [ -z "$last_used" ] && last_used="$db_iso"

  # workspace breadth = number of workspace dirs (sibling of globalStorage).
  local ws_dir ws_count
  ws_dir="${DB%/globalStorage/state.vscdb}/workspaceStorage"
  ws_count=0; [ -d "$ws_dir" ] && ws_count="$(find "$ws_dir" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')"

  # Build the output object one field at a time (field order is the contract).
  json_str product "cursor"
  json_str host "$HOST"
  json_str os_user "$user"
  json_str email "$email"
  json_str plan "$plan"
  json_str joined "$joined"
  json_str auth_method "$auth"
  json_str model "$model"
  json_str scopes "$scopes"
  json_str last_used "$last_used"
  json_str db_mtime "$db_iso"
  json_str first_session "$first_sess"
  json_str current_session "$cur_sess"
  json_raw workspace_count "${ws_count:-0}"
  json_raw mcp_servers "$mcp_json"
  json_raw mcp_count "$mcp_count"
  json_str user_id "$user_id"
  json_str machine_id "$tel_mid"
  json_str dev_device_id "$tel_dev"
  json_str service_machine_id "$svc_mid"
  json_str sqm_id "$tel_sqm"
  json_raw access_token_present "$(bool "$at_present")"
  json_str access_token_exp "$at_exp_iso"
  json_raw access_token_expired "$at_expired"
  json_raw refresh_token_present "$(bool "$rt_present")"
  json_str app_version "$APPVER"
  json_str db_path "$DB"
  json_str source "$SRC"
  json_raw secrets_scan "{\"files_scanned\":${SECRETS_FILES_SCANNED},\"findings\":${SECRETS_JSON}}"
  if [ "$auth_meta_json" != "[]" ]; then
    json_raw auth_metadata "{\"mcp_servers\":$auth_meta_json}"
  fi
  json_emit
  return 0
}

# --- main --------------------------------------------------------------------
# Reader selection (most reliable first). A real SQLite engine is required to read
# the WAL-mode state.vscdb correctly; we don't depend on any single one being present:
#   sqlite3 CLI  -> SRC=sqlite3         (macOS ships /usr/bin/sqlite3)
#   python3      -> SRC=python-sqlite3  (stdlib sqlite3 module, no external binary)
SQLITE="$(command -v sqlite3 || true)"
PY="$(command -v python3 || command -v python || true)"
READER=""; SRC=""
[ -n "$SQLITE" ] && { READER="sqlite3"; SRC="sqlite3"; }
[ -z "$READER" ] && [ -n "$PY" ] && { READER="python"; SRC="python-sqlite3"; }
if [ -z "$READER" ]; then
  json_str product "cursor"; json_str host "$HOST"; json_str error "no_sqlite_reader"; json_emit
  exit 0
fi

if ! enumerate_homes; then
  json_str product "cursor"; json_str host "$HOST"; json_str error "unsupported_os"; json_str os "$OS"; json_emit
  exit 0
fi

APPVER="$(cursor_version)"

# Dedup by real path so symlinked/duplicate DBs are reported once.
emitted=()
already() { local x; for x in "${emitted[@]:-}"; do [ "$x" = "$1" ] && return 0; done; return 1; }

found=0
for H in "${HOMES[@]}"; do
  user="$(basename "$H")"
  # process-substitution feeds discover_dbs output line-by-line into the loop
  while IFS= read -r DB; do
    [ -z "$DB" ] && continue
    rp="$(readlink -f "$DB" 2>/dev/null || printf '%s' "$DB")"
    already "$rp" && continue
    emitted+=("$rp"); found=1   # a DB exists here -> not "not installed", even if it has no account
    process_db "$user" "$DB" "$H"
  done < <(discover_dbs "$H")
done

[ "$found" -eq 0 ] && { json_str product "cursor"; json_str host "$HOST"; json_str status "not_installed_or_no_profile"; json_emit; }
