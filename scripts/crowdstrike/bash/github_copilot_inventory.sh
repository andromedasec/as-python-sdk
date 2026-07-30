#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# github_copilot_inventory.sh
# SCRIPT_VERSION: 1.1.0
# Inventory GitHub Copilot usage on the endpoint. RTR (root). macOS + Linux.
# Enumerates ALL user profiles (RTR runs as root/SYSTEM, not the logged-in user).
#
# Copilot ships as an IDE extension AND (since 2026) as a standalone CLI + desktop
# app, so there is no single account store like Claude/Cursor. We combine several
# on-disk signals per profile:
#   1) Shared OAuth store  ~/.config/github-copilot/apps.json (older: hosts.json)
#      -> github_login (the "user" field). Written by the Copilot language server
#      (Neovim / JetBrains / old CLI); reliably present for JetBrains users, often
#      ABSENT for VS Code users whose token lives in the OS keychain.
#   2) Editor installs  -> which editors have Copilot + version:
#      - VS Code:  ~/.vscode/extensions/github.copilot-<ver> (+ -server / -insiders)
#      - JetBrains: <cfg>/JetBrains/<Product>/plugins/github-copilot-intellij
#   3) Standalone Copilot CLI  ~/.copilot/ (config.json + data.db). Version from the
#      "data.db.pre-update-backup-<ver>-<epoch>" backup files. Identity is in the OS
#      keychain, so this is a presence + version signal (github_login stays empty).
#   4) Standalone Copilot desktop app ("GitHub Copilot.app", GA 2026). Per-user data
#      under com.github.githubapp; version from the ~/Library/Caches/
#      copilot-desktop-gh-<ver> dir (macOS). Identity is in the OS keychain too.
#
# SECURITY: the oauth_token VALUE is never read or emitted. apps.json is reported
# as presence + mtime only (credentials_on_disk / credentials_mtime). The CLI's
# config.json is JSONC and holds only a first-launch timestamp — we never parse it,
# only note its presence. Seat/plan is NOT on disk (lives in the GitHub billing
# API) -> plan is always "unknown".
#
# OUTPUT: one compact JSON object per profile with a Copilot footprint (JSON-lines).
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
# build the object one field at a time into a buffer, then emit it.
# Add/remove/reorder fields by editing one readable line each.
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
# ===== END SHARED PRELUDE =====

# ─────────────────────────────────────────────────────────────────────────────
# 3. DISCOVERY — locate Copilot's auth store and editor installs for one profile
# ─────────────────────────────────────────────────────────────────────────────

# copilot_auth_file HOME -> path to the profile's github-copilot auth store
# (apps.json preferred, hosts.json fallback), else "". Honors XDG_CONFIG_HOME.
copilot_auth_file() {
  local H="$1" base p
  for base in "$H/.config/github-copilot" "${XDG_CONFIG_HOME:+$XDG_CONFIG_HOME/github-copilot}"; do
    [ -z "$base" ] && continue
    for p in "$base/apps.json" "$base/hosts.json"; do
      [ -f "$p" ] && { printf '%s' "$p"; return; }
    done
  done
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — extract identity, editors, and version for one profile
# ─────────────────────────────────────────────────────────────────────────────

# gh_login FILE -> the "user" (github login) from apps.json/hosts.json, else "".
# Uses python3 for a proper parse when present; else a grep fallback. The token
# value is never read.
gh_login() {
  local f="$1"
  if [ -n "$PY" ]; then
    "$PY" - "$f" 2>/dev/null <<'PYEOF'
import json,sys
try:
    with open(sys.argv[1],encoding="utf-8",errors="replace") as fh: j=json.load(fh)
except Exception:
    sys.exit(0)
login=""
if isinstance(j,dict):
    # prefer a github.com host entry, else the first entry that has a user
    for k in sorted(j, key=lambda x:(0 if str(x).startswith("github.com") else 1, str(x))):
        v=j[k]
        if isinstance(v,dict) and v.get("user"):
            login=v["user"]; break
print(login)
PYEOF
  else
    # grep fallback: first "user":"..." value (never matches the token key).
    sed -n 's/.*"user"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$f" 2>/dev/null | head -n1
  fi
}

# max_epoch PATHS... -> the newest mtime (unix seconds) among the given paths, or "".
max_epoch() {
  local newest="" e p
  for p in "$@"; do
    [ -e "$p" ] || continue
    e="$(file_epoch "$p")"
    [ -n "$e" ] && { [ -z "$newest" ] || [ "$e" -gt "$newest" ]; } && newest="$e"
  done
  printf '%s' "$newest"
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — process one profile end-to-end: discover, derive, build, print
# ─────────────────────────────────────────────────────────────────────────────

# process_profile HOME USER -> emit one JSON line if the profile has any Copilot
# footprint (auth store OR an editor install); return 1 (emits nothing) otherwise.
process_profile() {
  local H="$1" user="$2"
  local auth login="" cred="false" cred_mtime="" cred_source="" version=""
  local -a editors=(); local -a touch=()

  # --- auth store (identity + credential presence) ---------------------------
  auth="$(copilot_auth_file "$H")"
  if [ -n "$auth" ]; then
    login="$(gh_login "$auth")"
    grep -q 'oauth_token' "$auth" 2>/dev/null && cred="true"
    cred_mtime="$(epoch_iso "$(file_epoch "$auth")")"
    case "$auth" in *apps.json) cred_source="apps.json";; *hosts.json) cred_source="hosts.json";; esac
    touch+=("$auth")
  fi

  # --- VS Code family presence + version -------------------------------------
  # Copilot has two extensions: the main "github.copilot" and "github.copilot-chat";
  # EITHER means Copilot is installed. And the extensions dir can lag (pending
  # reload, or left behind after uninstall), so we ALSO treat the VS Code
  # globalStorage dir as a presence signal. Arrays (no process substitution) keep
  # the spaces in the "Application Support" paths intact.
  # client_version prefers the main extension version (1.x); falls back to the
  # chat extension version (0.x) only if the main one is absent.
  local root d ver has_vscode=0 main_ver="" chat_ver=""
  local -a vsroots=(
    "$H/.vscode/extensions" "$H/.vscode-server/extensions" "$H/.vscode-insiders/extensions"
  )
  # newest_ver A B -> the version-sorted-higher of the two (either may be empty).
  newest_ver() { [ -z "$1" ] && { printf '%s' "$2"; return; }; [ -z "$2" ] && { printf '%s' "$1"; return; }; printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n1; }
  for root in "${vsroots[@]}"; do
    [ -d "$root" ] || continue
    for d in "$root"/github.copilot-[0-9]* "$root"/github.copilot-chat-[0-9]*; do
      [ -d "$d" ] || continue
      has_vscode=1; touch+=("$d")
      case "$d" in
        */github.copilot-chat-[0-9]*) chat_ver="$(newest_ver "$chat_ver" "${d##*/github.copilot-chat-}")" ;;
        */github.copilot-[0-9]*)      main_ver="$(newest_ver "$main_ver" "${d##*/github.copilot-}")" ;;
      esac
    done
  done
  # globalStorage / cached-VSIX under each VS Code data dir (Code + Insiders).
  local gs
  local -a vsdata=(
    "$H/Library/Application Support/Code" "$H/Library/Application Support/Code - Insiders"
    "$H/.config/Code" "$H/.config/Code - Insiders"
  )
  for gs in "${vsdata[@]}"; do
    for d in "$gs/User/globalStorage/github.copilot" "$gs/User/globalStorage/github.copilot-chat"; do
      [ -d "$d" ] || continue
      has_vscode=1; touch+=("$d")
    done
    # version fallback from the cached VSIX when no extension dir gave one
    if [ -d "$gs/CachedExtensionVSIXs" ]; then
      for d in "$gs"/CachedExtensionVSIXs/github.copilot-[0-9]*; do
        [ -e "$d" ] && main_ver="$(newest_ver "$main_ver" "${d##*/github.copilot-}")"
      done
      for d in "$gs"/CachedExtensionVSIXs/github.copilot-chat-[0-9]*; do
        [ -e "$d" ] && chat_ver="$(newest_ver "$chat_ver" "${d##*/github.copilot-chat-}")"
      done
    fi
  done
  [ -n "$main_ver" ] && version="$main_ver" || version="$chat_ver"
  [ "$has_vscode" -eq 1 ] && editors+=("vscode")
  # NOTE: version is finalized after the CLI/desktop blocks below (they provide a
  # fallback when no VS Code version was found).

  # --- JetBrains plugin presence (per IDE product) ---------------------------
  local jbroot product plugin
  local -a jbroots=(
    "$H/Library/Application Support/JetBrains" "$H/.local/share/JetBrains"
  )
  for jbroot in "${jbroots[@]}"; do
    [ -d "$jbroot" ] || continue
    for plugin in "$jbroot"/*/plugins/github-copilot-intellij; do
      [ -d "$plugin" ] || continue
      touch+=("$plugin")
      # <jbroot>/<Product><ver>/plugins/github-copilot-intellij -> the product dir
      product="${plugin%/plugins/github-copilot-intellij}"; product="${product##*/}"
      editors+=("jetbrains:$product")
    done
  done

  # --- Standalone Copilot CLI  ~/.copilot ------------------------------------
  # The `copilot` CLI (also the engine under the desktop app) stores state here.
  # config.json is JSONC (first-launch timestamp only) and identity lives in the
  # OS keychain, so this is presence + version only. Version = newest
  # "data.db.pre-update-backup-<ver>-<epoch>" backup file. Not honoring
  # COPILOT_HOME / XDG_CONFIG_HOME on purpose: under RTR those belong to root, not
  # to the profile being scanned, so they'd misattribute.
  local cli="$H/.copilot" cli_ver=""
  if [ -e "$cli/config.json" ] || [ -e "$cli/data.db" ]; then
    editors+=("copilot-cli"); touch+=("$cli")
    for d in "$cli"/*pre-update-backup-[0-9]*; do
      [ -e "$d" ] || continue
      cli_ver="$(newest_ver "$cli_ver" "$(printf '%s' "${d##*pre-update-backup-}" | sed 's/-[0-9].*$//')")"
    done
  fi

  # --- Standalone Copilot desktop app ("GitHub Copilot.app") -----------------
  # GA 2026. Per-user state under com.github.githubapp (macOS confirmed;
  # Linux dirs best-effort). Identity is in the OS keychain -> github_login stays
  # empty. Version from the per-user cache dir "copilot-desktop-gh-<ver>" (macOS).
  local desk_ver="" dbase has_desktop=0
  local -a desk_dirs=(
    "$H/Library/Application Support/com.github.githubapp"   # macOS (confirmed)
    "$H/.config/com.github.githubapp"                       # Linux (best-effort)
    "$H/.config/GitHub Copilot"                             # Linux (best-effort)
  )
  for dbase in "${desk_dirs[@]}"; do
    [ -d "$dbase" ] || continue
    has_desktop=1; editors+=("copilot-desktop"); touch+=("$dbase"); break
  done
  if [ "$has_desktop" -eq 1 ]; then
    for d in "$H/Library/Caches/copilot-desktop-gh-"[0-9]*; do
      [ -d "$d" ] || continue
      desk_ver="$(newest_ver "$desk_ver" "${d##*/copilot-desktop-gh-}")"
    done
  fi

  # Finalize version: VS Code (set above) wins; else the CLI, else the desktop app.
  [ -z "$version" ] && version="$cli_ver"
  [ -z "$version" ] && version="$desk_ver"

  # No Copilot footprint at all on this profile -> nothing to report.
  [ -n "$auth" ] || [ "${#editors[@]}" -gt 0 ] || return 1

  # last_used: newest mtime across the auth store + editor install dirs.
  local last_used=""
  [ "${#touch[@]}" -gt 0 ] && last_used="$(epoch_iso "$(max_epoch "${touch[@]}")")"

  # editors -> compact JSON array of unique entries (order-preserving).
  local editors_json="[" i n seen=""
  n=0
  # ${arr[@]+"${arr[@]}"} — expand safely even when empty (auth store present but
  # no editor install). A bare "${editors[@]}" trips `set -u` on bash 3.2 (macOS).
  for i in ${editors[@]+"${editors[@]}"}; do
    case ",$seen," in *",$i,"*) continue;; esac
    seen="$seen,$i"
    [ "$n" -gt 0 ] && editors_json="$editors_json,"
    editors_json="$editors_json\"$(json_escape "$i")\""
    n=$((n+1))
  done
  editors_json="$editors_json]"

  # Field order here is the output contract — keep it stable.
  json_str product "github_copilot"
  json_str host "$HOST"
  json_str os_user "$user"
  json_str github_login "$login"
  json_str email ""
  json_str plan "unknown"
  json_str auth_method "github_oauth"
  json_str client_version "$version"
  json_raw editors "$editors_json"
  json_str model ""
  json_str last_used "$last_used"
  json_raw credentials_on_disk "$cred"
  json_str credentials_mtime "$cred_mtime"
  json_str credentials_source "$cred_source"
  json_str source "config"
  json_emit
  return 0
}

# --- main --------------------------------------------------------------------
PY="$(command -v python3 || command -v python || true)"

if ! enumerate_homes; then
  json_str product "github_copilot"; json_str host "$HOST"; json_str error "unsupported_os"; json_str os "$OS"; json_emit
  exit 0
fi

found=0
# ${HOMES[@]+"${HOMES[@]}"} — safe expansion when no profile dirs exist (a bare
# "${HOMES[@]}" trips `set -u` on bash 3.2). In production /Users (or /home + /root)
# is never empty, but this keeps the loop robust on an empty box.
for H in ${HOMES[@]+"${HOMES[@]}"}; do
  user="$(basename "$H")"
  process_profile "$H" "$user" && found=1
done

[ "$found" -eq 0 ] && { json_str product "github_copilot"; json_str host "$HOST"; json_str status "not_installed"; json_emit; }
