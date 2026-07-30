#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# claude_inventory.sh
# SCRIPT_VERSION: 1.2.0
# Inventory Claude Code account + plan + security-relevant metadata. RTR (root).
# macOS + Linux. Enumerates ALL user profiles (RTR runs as root/SYSTEM).
#
# Sources per profile (in priority order for plan/email):
#   1) live `claude auth status` as the user  -> subscriptionType (best)
#   2) ~/.claude.json (oauthAccount: email/org/account + plan via seatTier /
#      organizationType; also projects, mcpServers, numStartups, version)
#   3) ~/.claude/ folder  -> last_used (newest session mtime), credentials presence
#
# SECURITY: credential VALUES are never read/emitted. ~/.claude/.credentials.json
# is reported as presence + mtime only. mcpServers reveal external data-egress
# surface; project paths reveal which repos the agent has touched.
#
# Nested fields (projects, mcpServers) need real JSON parsing -> uses python3 if
# present, else a grep fallback that still returns the core identity/plan fields.
# OUTPUT: one compact JSON object per profile (JSON-lines).
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
# 3. DISCOVERY — locate the Claude CLI and the config file for one profile
# ─────────────────────────────────────────────────────────────────────────────

# find_cli HOME -> path to an executable `claude` for that profile, else "".
find_cli() {
  local H="$1" c
  for c in "$H/.claude/local/claude" "$H/.local/bin/claude" "/usr/local/bin/claude" "/opt/homebrew/bin/claude"; do
    [ -x "$c" ] && { printf '%s' "$c"; return; }
  done
}

# find_cfg HOME -> path to that profile's .claude.json. Known locations first
# (incl. $CLAUDE_CONFIG_DIR), then a bounded, pruned search as a fallback.
find_cfg() {
  local H="$1" p
  for p in "$H/.claude.json" "$H/.config/claude/.claude.json" "$H/.config/claude/config.json" \
           "${CLAUDE_CONFIG_DIR:+$CLAUDE_CONFIG_DIR/.claude.json}"; do
    [ -n "$p" ] && [ -f "$p" ] && { printf '%s' "$p"; return; }
  done
  find "$H" -maxdepth 5 \( -name node_modules -o -name .git -o -name Caches \) -prune -o \
    -type f -name '.claude.json' -print 2>/dev/null | head -1
}

# claude_secret_targets HOME CDIR -> candidate secret-scan file paths for one
# profile: global CLAUDE.md + skills/memory files. Global scope only —
# per-project CLAUDE.md/skills files are out of scope (no cheap way to bound
# recursive scans across arbitrary repos from RTR).
claude_secret_targets() {
  local H="$1" cdir="$2" f
  for f in "$H/CLAUDE.md" "$cdir/CLAUDE.md"; do [ -f "$f" ] && printf '%s\n' "$f"; done
  find "$cdir/skills" "$cdir/memory" -maxdepth 4 -type f \( -name '*.md' -o -name '*.mdc' \) 2>/dev/null
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — pull identity/plan from the live CLI (best source for plan)
# ─────────────────────────────────────────────────────────────────────────────

# jget KEY JSON -> the string value of "KEY" in a flat JSON blob (first match).
jget() { printf '%s' "$2" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -n1; }

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — two paths: python3 enrichment (full), or a grep fallback (core fields)
# ─────────────────────────────────────────────────────────────────────────────

# py_emit HOST USER CFG CDIR CLI_EMAIL CLI_PLAN CLI_ORG CLI_METHOD SECRETS_JSON SECRETS_FILES_SCANNED
# Reads the config + ~/.claude folder, merges in the CLI-derived values, and
# prints the final JSON line. Nested fields (projects/mcpServers) need real JSON
# parsing, which is why this path uses python3.
py_emit() {
  "$PY" - "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "${10}" <<'PYEOF'
import json,os,sys,glob,re
host,os_user,cfg,cdir,cli_email,cli_plan,cli_org,cli_method,secrets_json,secrets_files_scanned = sys.argv[1:11]
o={"product":"claude","host":host,"os_user":os_user}
email=cli_email or ""; plan=cli_plan or ""; org=cli_org or ""; method=cli_method or ""
orgid=""; acct=""; role=""; num_startups=""; install=""; version=""; user_id=""; first_start=""
projects=[]; mcp={}; model_counts={}

def _classify_mcp_server(name, cfg):
    """Structural shape only — never the command/args/url values themselves,
    beyond a bare hostname for remote servers."""
    cfg = cfg if isinstance(cfg, dict) else {}
    url = cfg.get("url") or cfg.get("baseUrl") or ""
    transport = str(cfg.get("type") or cfg.get("transport") or "").lower()
    if not transport:
        transport = "http" if url else ("stdio" if cfg.get("command") else "unknown")
    entry = {"name": name, "transport": transport}
    if transport == "stdio":
        entry["command_present"] = bool(cfg.get("command"))
        entry["arg_count"] = len(cfg.get("args") or [])
    elif transport in ("http", "sse") and url:
        try:
            from urllib.parse import urlparse
            host = urlparse(url).hostname
            if host:
                entry["url_host"] = host
        except Exception:
            pass
    return entry

def _looks_like_fs_path(a):
    """True only if the arg looks like a filesystem path and NOT an env-assignment
    token (e.g. "GITHUB_TOKEN=ghp_SECRET123") — those must never be emitted."""
    if "=" in a:
        return False
    return bool(re.match(r'^(/|\./|\.\./|~|[A-Za-z]:\\|\\\\)', a))

def _auth_meta_for_mcp_server(name, cfg):
    """Names/indicators only: which env vars and header keys are configured, and
    (heuristically, for the common @modelcontextprotocol/server-filesystem package)
    which directory paths are exposed. Never the values."""
    cfg = cfg if isinstance(cfg, dict) else {}
    env_names = sorted((cfg.get("env") or {}).keys())
    header_names = sorted((cfg.get("headers") or {}).keys())
    fs_paths = []
    args = [str(a) for a in (cfg.get("args") or [])]
    cmd = str(cfg.get("command") or "")
    if "server-filesystem" in " ".join([cmd] + args):
        fs_paths = [a for a in args if not a.startswith("-") and "server-filesystem" not in a and _looks_like_fs_path(a)]
    entry = {"name": name}
    if env_names: entry["env_var_names"] = env_names
    if header_names: entry["header_key_names"] = header_names
    if fs_paths: entry["filesystem_scope_paths"] = fs_paths
    return entry
try:
    with open(cfg,encoding="utf-8",errors="replace") as f: j=json.load(f)
    oa=j.get("oauthAccount") or {}
    email=email or oa.get("emailAddress") or j.get("email") or ""
    org=org or oa.get("organizationName") or ""
    orgid=oa.get("organizationUuid") or oa.get("organizationUuidV2") or ""
    acct=oa.get("accountUuid") or ""
    role=oa.get("organizationRole") or oa.get("role") or ""
    # Claude Code stores the plan under oauthAccount.seatTier ("team_standard") /
    # organizationType ("claude_team"); subscriptionType/subscription/planType are
    # legacy/absent. Check the legacy keys first, then the current ones.
    for k in ("subscriptionType","subscription","planType","seatTier","organizationType"):
        if not plan and (j.get(k) or oa.get(k)): plan=j.get(k) or oa.get(k); break
    num_startups=j.get("numStartups","")
    install=j.get("installMethod") or j.get("autoUpdaterStatus") or ""
    version=j.get("version") or j.get("clientVersion") or ""
    user_id=j.get("userID") or j.get("userId") or ""
    first_start=j.get("firstStartTime") or ""
    pj=j.get("projects") or {}
    if isinstance(pj,dict):
        projects=list(pj.keys())
        for p,v in pj.items():
            if isinstance(v,dict):
                for m,mcfg in (v.get("mcpServers") or {}).items(): mcp[m]=mcfg   # local scope
                for mu in (v.get("lastModelUsage") or {}): model_counts[mu]=model_counts.get(mu,0)+1
            # project scope: <projectRoot>/.mcp.json (committed, team-shared). The
            # projects keys are absolute paths, so this is a bounded read of known
            # roots, not a filesystem crawl. setdefault -> a local-scope server of the
            # same name (higher precedence) is not clobbered.
            try:
                pmcp=os.path.join(p,".mcp.json")
                if os.path.isfile(pmcp):
                    with open(pmcp,encoding="utf-8",errors="replace") as pf: pj2=json.load(pf)
                    for m,mcfg in (pj2.get("mcpServers") or {}).items(): mcp.setdefault(m,mcfg)
            except Exception: pass
    for m,mcfg in (j.get("mcpServers") or {}).items(): mcp[m]=mcfg   # user scope
except Exception as e:
    o["config_error"]=str(e)[:80]

# folder metadata: last_used (newest session jsonl), credentials presence
last_used=""; cred=False; cred_mtime=""; settings=False; model=""
if cdir and os.path.isdir(cdir):
    newest=0
    for pat in ("projects/**/*.jsonl","history.jsonl","**/*.jsonl"):
        for fp in glob.iglob(os.path.join(cdir,pat),recursive=True):
            try: newest=max(newest,os.path.getmtime(fp))
            except OSError: pass
    if newest:
        import datetime; last_used=datetime.datetime.utcfromtimestamp(int(newest)).strftime("%Y-%m-%dT%H:%M:%SZ")
    credp=os.path.join(cdir,".credentials.json")
    if os.path.isfile(credp):
        cred=True
        import datetime; cred_mtime=datetime.datetime.utcfromtimestamp(int(os.path.getmtime(credp))).strftime("%Y-%m-%dT%H:%M:%SZ")
    settings_path=os.path.join(cdir,"settings.json")
    settings=os.path.isfile(settings_path)
    if settings:
        try:
            with open(settings_path,encoding="utf-8",errors="replace") as sf: model=(json.load(sf) or {}).get("model") or ""
        except Exception: pass

if not last_used and cfg and os.path.isfile(cfg):
    import datetime; last_used=datetime.datetime.utcfromtimestamp(int(os.path.getmtime(cfg))).strftime("%Y-%m-%dT%H:%M:%SZ")

# model: prefer settings.json's configured model; else the most-used from lastModelUsage
if not model and model_counts:
    model=max(model_counts, key=model_counts.get)

mcp_names = sorted(mcp)
mcp_servers_out = [_classify_mcp_server(n, mcp[n]) for n in mcp_names]
auth_meta_servers = [_auth_meta_for_mcp_server(n, mcp[n]) for n in mcp_names]
auth_meta_servers = [e for e in auth_meta_servers if len(e) > 1]  # drop entries with only "name"

try:
    secret_findings = json.loads(secrets_json) if secrets_json else []
except Exception:
    secret_findings = []
try:
    secret_files_scanned = int(secrets_files_scanned or 0)
except ValueError:
    secret_files_scanned = 0

o.update({
  "email":email,"plan":plan or "unknown","org":org,"org_id":orgid,"account_uuid":acct,
  "org_role":role,"auth_method":method,"last_used":last_used,"num_startups":num_startups,
  "client_version":version,"install_method":install,"user_id":user_id,"first_start":first_start,
  "model":model,
  "projects_count":len(projects),"project_paths":projects[:50],"projects_truncated":len(projects)>50,
  "mcp_servers":mcp_servers_out,"mcp_count":len(mcp_names),
  "credentials_on_disk":cred,"credentials_mtime":cred_mtime,"settings_present":settings,
  "secrets_scan":{"files_scanned":secret_files_scanned,"findings":secret_findings},
  "source":"cli+config" if cli_email else "config"
})
if auth_meta_servers:
    o["auth_metadata"] = {"mcp_servers": auth_meta_servers}
print(json.dumps(o,separators=(",",":")))
PYEOF
}

# emit_grep_fallback USER CFG CDIR CLI_EMAIL CLI_PLAN CLI_ORG SECRETS_JSON SECRETS_FILES_SCANNED
# -> core fields only. Used when python3 is absent (stock macOS). last_used
# comes from the cfg mtime. Returns 1 (emits nothing) if no identity recovered.
emit_grep_fallback() {
  local user="$1" cfg="$2" cdir="$3" email="$4" plan="$5" org="$6"
  local secrets_json="$7" secrets_files_scanned="$8"
  local blob="" orgid cred lu_epoch lu
  [ -n "$cfg" ] && blob="$(cat "$cfg" 2>/dev/null)"
  [ -z "$email" ] && email="$(jget emailAddress "$blob")"
  [ -z "$email" ] && email="$(jget email "$blob")"
  [ -z "$org" ] && org="$(jget organizationName "$blob")"
  orgid="$(jget organizationUuid "$blob")"
  [ -z "$plan" ] && plan="$(jget subscriptionType "$blob")"
  [ -z "$plan" ] && plan="$(jget seatTier "$blob")"
  [ -z "$plan" ] && plan="$(jget organizationType "$blob")"
  [ -z "$plan" ] && plan="unknown"
  cred="false"; [ -f "$cdir/.credentials.json" ] && cred="true"
  lu_epoch="$(file_epoch "$cfg")"
  lu="$(epoch_iso "$lu_epoch")"
  [ -z "$email$org" ] && return 1
  json_str product "claude"
  json_str host "$HOST"
  json_str os_user "$user"
  json_str email "$email"
  json_str plan "$plan"
  json_str org "$org"
  json_str org_id "$orgid"
  json_str last_used "$lu"
  json_raw credentials_on_disk "$cred"
  json_raw secrets_scan "{\"files_scanned\":${secrets_files_scanned:-0},\"findings\":${secrets_json:-[]}}"
  json_str source "config-grep"
  json_str note "python3_absent_limited_fields"
  json_emit
  return 0
}

# --- main --------------------------------------------------------------------
PY="$(command -v python3 || command -v python || true)"

if ! enumerate_homes; then
  json_str product "claude"; json_str host "$HOST"; json_str error "unsupported_os"; json_str os "$OS"; json_emit
  exit 0
fi

found=0
for H in "${HOMES[@]}"; do
  user="$(basename "$H")"
  cdir="$H/.claude"
  # Skip profiles with no Claude footprint at all.
  [ ! -e "$H/.claude.json" ] && [ ! -d "$cdir" ] && [ ! -d "$H/.config/claude" ] && continue
  cfg="$(find_cfg "$H")"

  # Live CLI is the best source of plan/subscription; run it as the profile's user.
  email=""; plan=""; org=""; method=""
  CLA="$(find_cli "$H")"
  out=""; [ -n "$CLA" ] && out="$(sudo -n -u "$user" "$CLA" auth status 2>/dev/null)"
  if printf '%s' "$out" | grep -q '"email"'; then
    email="$(jget email "$out")"; plan="$(jget subscriptionType "$out")"
    org="$(jget orgName "$out")"; method="$(jget authMethod "$out")"
  fi

  secret_files=()
  while IFS= read -r sf; do secret_files+=("$sf"); done < <(claude_secret_targets "$H" "$cdir")
  # bash 3.2 (stock macOS) errors on "${arr[@]}" when the array is empty under
  # `set -u`; the ${arr[@]+...} guard expands to nothing instead of aborting.
  scan_secrets_paths ${secret_files[@]+"${secret_files[@]}"}

  if [ -n "$PY" ] && [ -n "$cfg" ]; then
    py_emit "$HOST" "$user" "$cfg" "$cdir" "$email" "$plan" "$org" "$method" "$SECRETS_JSON" "$SECRETS_FILES_SCANNED"
    found=1
  else
    emit_grep_fallback "$user" "$cfg" "$cdir" "$email" "$plan" "$org" "$SECRETS_JSON" "$SECRETS_FILES_SCANNED" && found=1
  fi
done

[ "$found" -eq 0 ] && { json_str product "claude"; json_str host "$HOST"; json_str status "not_installed"; json_emit; }
