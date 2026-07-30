#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# codex_inventory.sh
# SCRIPT_VERSION: 1.0.0
# Inventory OpenAI Codex account + plan + security-relevant metadata. RTR (root).
# macOS + Linux. Enumerates ALL user profiles (RTR runs as root/SYSTEM).
#
# Sources per profile (CODEX_HOME = ~/.codex):
#   1) ~/.codex/auth.json  -> auth_mode; token presence; and (decoded from the
#      id_token JWT) email, plan (chatgpt_plan_type), org id, account id, expiry
#   2) ~/.codex/config.toml -> mcp servers (egress surface), trusted project
#      paths (repos touched), configured model, app version
#   3) ~/.codex/ folder -> last_used (newest session rollout mtime), installation_id,
#      credentials presence/mtime
#
# SECURITY: credential VALUES are never emitted. Codex keeps email + plan ONLY
# inside the id_token JWT, so we decode that token's identity claims (email, plan,
# org, account, exp) and emit those claims — never the raw token. The access token
# yields its JWT exp only; refresh token and OPENAI_API_KEY are presence-only.
# mcpServers reveal external data-egress surface; project paths reveal which repos
# the agent has operated in.
#
# Nested fields (id_token JSON, config.toml) need real parsing -> uses python3 if
# present, else a grep/base64 fallback that still returns the core identity/plan
# fields. OUTPUT: one compact JSON object per profile (JSON-lines).
#
# This file follows the shared 5-section layout (see README.md):
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
# 3. DISCOVERY — locate the Codex app version + per-profile CODEX_HOME
# ─────────────────────────────────────────────────────────────────────────────

# codex_version -> the installed Codex desktop app version (best effort), else "".
# The config.toml env carries a version too; that's read on the python path.
codex_version() {
  case "$OS" in
    Darwin)
      [ -f "/Applications/Codex.app/Contents/Info.plist" ] && \
        /usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" \
          "/Applications/Codex.app/Contents/Info.plist" 2>/dev/null && return
      ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — small parse helpers (JWT decode for the grep fallback)
# ─────────────────────────────────────────────────────────────────────────────

# jget KEY JSON -> the string value of "KEY" in a flat JSON blob (first match).
jget() { printf '%s' "$2" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -n1; }

# b64url_decode STRING -> decode a base64url string (JWT segments use base64url).
# Converts to standard base64, re-pads, then tries GNU base64, BSD base64, openssl.
b64url_decode() {
  local d="$1"; d="${d//-/+}"; d="${d//_//}"
  case $(( ${#d} % 4 )) in 2) d="$d==";; 3) d="$d=";; esac
  printf '%s' "$d" | base64 -d 2>/dev/null || printf '%s' "$d" | base64 -D 2>/dev/null || printf '%s' "$d" | openssl base64 -d -A 2>/dev/null
}
# jwt_claim TOKEN CLAIM -> the string value of CLAIM from a JWT payload, WITHOUT
# ever emitting the token itself. Empty unless the token looks like h.p.s.
jwt_claim() {
  local tok="$1" claim="$2"
  case "$tok" in *.*.*) ;; *) return;; esac
  b64url_decode "$(printf '%s' "$tok" | cut -d. -f2)" 2>/dev/null \
    | sed -n "s/.*\"$claim\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1
}
# jwt_exp TOKEN -> the numeric 'exp' (expiry epoch) from a JWT payload, or "".
jwt_exp() {
  local tok="$1"
  case "$tok" in *.*.*) ;; *) return;; esac
  b64url_decode "$(printf '%s' "$tok" | cut -d. -f2)" 2>/dev/null \
    | grep -Eo '"exp"[[:space:]]*:[[:space:]]*[0-9]+' | grep -Eo '[0-9]+' | head -1
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — two paths: python3 enrichment (full), or a grep fallback (core fields)
# ─────────────────────────────────────────────────────────────────────────────

# py_emit HOST OS_USER CDIR APPVER -> read auth.json + config.toml + folder, decode
# the id_token identity claims, and print the final JSON line. Nested JSON + the
# id_token JWT need real parsing, which is why this path uses python3.
py_emit() {
  "$PY" - "$1" "$2" "$3" "$4" <<'PYEOF'
import json,os,sys,glob,base64,datetime,re
host,os_user,cdir,appver = sys.argv[1:5]
o={"product":"codex","host":host,"os_user":os_user}
auth=os.path.join(cdir,"auth.json"); cfg=os.path.join(cdir,"config.toml")
now=int(datetime.datetime.utcnow().timestamp())

def iso(ts):
    try: return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception: return ""

def jwt_payload(tok):
    # Decode ONLY the middle (claims) segment; never the signature, never re-emit tok.
    try:
        seg=tok.split(".")[1]; seg+="="*(-len(seg)%4)
        return json.loads(base64.urlsafe_b64decode(seg.encode("ascii")))
    except Exception:
        return {}

email="";plan="";orgid="";acct="";user_id="";auth_mode="";last_refresh=""
api_key_present=False;refresh_present=False;at_present=False;id_present=False
id_exp="";id_expired=False;at_exp="";at_expired=False
try:
    with open(auth,encoding="utf-8",errors="replace") as f: a=json.load(f)
    auth_mode=a.get("auth_mode") or ""
    api_key_present=bool(a.get("OPENAI_API_KEY"))
    last_refresh=a.get("last_refresh") or ""
    tk=a.get("tokens") or {}
    acct=tk.get("account_id") or ""
    idt=tk.get("id_token") or ""; at=tk.get("access_token") or ""; rt=tk.get("refresh_token") or ""
    id_present=bool(idt); at_present=bool(at); refresh_present=bool(rt)
    if idt:
        p=jwt_payload(idt)
        email=p.get("email") or ""
        e=p.get("exp")
        if e: id_exp=iso(e); id_expired=int(e)<now
        claim=p.get("https://api.openai.com/auth") or {}
        plan=claim.get("chatgpt_plan_type") or ""
        orgid=claim.get("organization_id") or ""
        acct=acct or claim.get("chatgpt_account_id") or ""
        user_id=claim.get("chatgpt_user_id") or claim.get("user_id") or ""
    if at:
        e=jwt_payload(at).get("exp")
        if e: at_exp=iso(e); at_expired=int(e)<now
    idt=at=rt=""   # scrub token values from memory
except Exception as e:
    o["auth_error"]=str(e)[:80]

# config.toml: MCP servers (FULL structural parse), trusted projects, model, app
# version. Hand-rolled line-based TOML scan so it works on Python 3.9 hosts (no
# tomllib, which is 3.11+). We read only names/structure per MCP server — transport,
# url host, arg count, env-var and header NAMES, and the explicit `auth = "oauth"`
# flag — never secret values, command lines, or full URLs.
mcp_servers_out=[]; auth_meta_servers=[]; projects=[]; model=""; cfg_ver=""
def _host(u):
    try:
        from urllib.parse import urlparse
        return urlparse(u).hostname or ""
    except Exception:
        return ""
# _mcp_section("mcp_servers.NAME[.sub]") -> (name, subtable) or None. NAME may be
# bare or "quoted"; subtable is "" (base), env, http_headers, env_http_headers.
def _mcp_section(inner):
    if not inner.startswith("mcp_servers."): return None
    rest=inner[len("mcp_servers."):]
    if rest.startswith('"'):
        e=rest.find('"',1)
        if e<0: return None
        return rest[1:e], rest[e+1:].lstrip(".")
    parts=rest.split(".",1)
    return parts[0], (parts[1] if len(parts)>1 else "")
try:
    with open(cfg,encoding="utf-8",errors="replace") as f: text=f.read()
    servers={}; order=[]; cur=None; cursub=""
    for raw in text.splitlines():
        line=raw.strip()
        if line.startswith("[") and line.endswith("]"):
            inner=line[1:-1].strip()
            sec=_mcp_section(inner)
            if sec and sec[0]:
                cur,cursub=sec[0].strip(),sec[1].strip()
                if cur not in servers:
                    servers[cur]={"env":[],"headers":[],"command":False,"argc":0,"url":"","oauth":False}
                    order.append(cur)
            else:
                cur=None; cursub=""
                pm=re.match(r'projects\.(?:"([^"]+)"|(.+))$', inner)
                if pm:
                    p=(pm.group(1) or pm.group(2) or "").strip()
                    if p: projects.append(p)
            continue
        if cur is None: continue
        km=re.match(r'^("?[^"=]+"?)\s*=\s*(.*)$', line)
        if not km: continue
        key=km.group(1).strip().strip('"'); val=km.group(2).strip()
        if cursub=="env":
            servers[cur]["env"].append(key)
        elif cursub in ("http_headers","env_http_headers"):
            servers[cur]["headers"].append(key)
        elif cursub=="":
            if key=="command": servers[cur]["command"]=True
            elif key=="url": servers[cur]["url"]=val.strip('"')
            elif key=="bearer_token_env_var": servers[cur]["env"].append(val.strip('"'))
            elif key=="auth" and val.strip('"').lower()=="oauth": servers[cur]["oauth"]=True
            elif key=="args":
                if val.startswith("[") and val.endswith("]"):
                    body=val[1:-1].strip()
                    servers[cur]["argc"]=0 if not body else body.count(",")+1
    for n in order:
        s=servers[n]
        transport="http" if s["url"] else ("stdio" if s["command"] else "unknown")
        e={"name":n,"transport":transport}
        if transport=="stdio":
            e["command_present"]=s["command"]; e["arg_count"]=s["argc"]
        elif transport=="http":
            h=_host(s["url"])
            if h: e["url_host"]=h
        if s["oauth"]: e["uses_oauth"]=True
        mcp_servers_out.append(e)
        am={"name":n}
        env=sorted(set(x for x in s["env"] if x)); hdr=sorted(set(x for x in s["headers"] if x))
        if env: am["env_var_names"]=env
        if hdr: am["header_key_names"]=hdr
        if len(am)>1: auth_meta_servers.append(am)
    mm=re.search(r'(?m)^\s*model\s*=\s*"([^"]+)"', text)
    if mm: model=mm.group(1)
    vm=re.search(r'BROWSER_USE_CODEX_APP_VERSION\s*=\s*"([^"]+)"', text)
    if vm: cfg_ver=vm.group(1)
except Exception:
    pass

# folder metadata: last_used (newest session rollout), install id, cred mtime.
newest=0
for fp in glob.iglob(os.path.join(cdir,"sessions","**","*.jsonl"),recursive=True):
    try: newest=max(newest,os.path.getmtime(fp))
    except OSError: pass
si=os.path.join(cdir,"session_index.jsonl")
if os.path.isfile(si):
    try: newest=max(newest,os.path.getmtime(si))
    except OSError: pass
last_used=iso(newest) if newest else ""
cred=os.path.isfile(auth)
cred_mtime=iso(os.path.getmtime(auth)) if cred else ""
if not last_used:
    for f in (auth,cfg):
        if os.path.isfile(f): last_used=iso(os.path.getmtime(f)); break
inst=""
ip=os.path.join(cdir,"installation_id")
if os.path.isfile(ip):
    try:
        with open(ip,encoding="utf-8",errors="replace") as f: inst=f.read().strip()[:64]
    except Exception: pass

o.update({
  "email":email,"plan":plan or "unknown","org":"","org_id":orgid,"account_uuid":acct,
  "user_id":user_id,"auth_method":auth_mode,"last_used":last_used,"last_refresh":last_refresh,
  "model":model,"app_version":appver or cfg_ver,"install_id":inst,
  "projects_count":len(projects),"project_paths":projects[:50],"projects_truncated":len(projects)>50,
  "mcp_servers":mcp_servers_out,"mcp_count":len(mcp_servers_out),
  "credentials_on_disk":cred,"credentials_mtime":cred_mtime,
  "id_token_present":id_present,"id_token_exp":id_exp,"id_token_expired":id_expired,
  "access_token_present":at_present,"access_token_exp":at_exp,"access_token_expired":at_expired,
  "refresh_token_present":refresh_present,"api_key_present":api_key_present,
  "source":"auth+config" if (email or acct) else "config"
})
if auth_meta_servers:
    o["auth_metadata"]={"mcp_servers":auth_meta_servers}
print(json.dumps(o,separators=(",",":")))
PYEOF
}

# emit_grep_fallback OS_USER CDIR -> core fields only, no python3 (stock macOS).
# Decodes the id_token identity claims with the bash JWT helpers. Returns 1
# (emits nothing) if no identity could be recovered.
emit_grep_fallback() {
  local user="$1" cdir="$2" auth="$2/auth.json" cfg="$2/config.toml"
  local ablob="" auth_mode api_key email plan orgid acct idt at
  local id_exp_epoch id_exp id_expired lu_epoch lu cred mcp_count now
  [ -f "$auth" ] && ablob="$(cat "$auth" 2>/dev/null)"
  auth_mode="$(jget auth_mode "$ablob")"
  # OPENAI_API_KEY present only if it is a non-null string value.
  api_key="false"; printf '%s' "$ablob" | grep -Eq '"OPENAI_API_KEY"[[:space:]]*:[[:space:]]*"' && api_key="true"
  idt="$(jget id_token "$ablob")"
  at="$(jget access_token "$ablob")"
  acct="$(jget account_id "$ablob")"
  email="$(jwt_claim "$idt" email)"
  plan="$(jwt_claim "$idt" chatgpt_plan_type)"
  orgid="$(jwt_claim "$idt" organization_id)"
  [ -z "$acct" ] && acct="$(jwt_claim "$idt" chatgpt_account_id)"
  [ -z "$plan" ] && plan="unknown"
  now="$(date -u +%s)"
  id_exp_epoch="$(jwt_exp "$idt")"; id_exp="$(epoch_iso "$id_exp_epoch")"
  id_expired="false"; [ -n "$id_exp_epoch" ] && [ "$id_exp_epoch" -lt "$now" ] 2>/dev/null && id_expired="true"
  idt=""; at=""   # scrub token values
  # last_used: newest session rollout mtime, else auth.json mtime.
  lu_epoch="$(find "$cdir/sessions" -type f -name '*.jsonl' -exec stat -f %m {} \; 2>/dev/null | sort -rn | head -1)"
  [ -z "$lu_epoch" ] && lu_epoch="$(file_epoch "$auth")"
  lu="$(epoch_iso "$lu_epoch")"
  # mcp_servers: count distinct [mcp_servers.NAME] headers. The class [^].] stops at
  # both the closing bracket and a dot, so [mcp_servers.x] and [mcp_servers.x.env]
  # collapse to the same NAME (matches the python path's dedupe).
  mcp_count=0
  [ -f "$cfg" ] && mcp_count="$(grep -Eo '^\[mcp_servers\.[^].]+' "$cfg" 2>/dev/null | sort -u | wc -l | tr -d ' ')"
  cred="false"; [ -f "$auth" ] && cred="true"
  [ -z "$email$acct" ] && return 1
  json_str product "codex"
  json_str host "$HOST"
  json_str os_user "$user"
  json_str email "$email"
  json_str plan "$plan"
  json_str org_id "$orgid"
  json_str account_uuid "$acct"
  json_str auth_method "$auth_mode"
  json_str last_used "$lu"
  json_str id_token_exp "$id_exp"
  json_raw id_token_expired "$id_expired"
  json_raw api_key_present "$api_key"
  json_raw mcp_count "${mcp_count:-0}"
  json_raw credentials_on_disk "$cred"
  json_str source "auth-grep"
  json_str note "python3_absent_limited_fields"
  json_emit
  return 0
}

# --- main --------------------------------------------------------------------
PY="$(command -v python3 || command -v python || true)"

if ! enumerate_homes; then
  json_str product "codex"; json_str host "$HOST"; json_str error "unsupported_os"; json_str os "$OS"; json_emit
  exit 0
fi

APPVER="$(codex_version)"

found=0
for H in "${HOMES[@]}"; do
  user="$(basename "$H")"
  CDIR="$H/.codex"
  # Skip profiles with no Codex footprint at all.
  [ ! -d "$CDIR" ] && continue
  [ ! -f "$CDIR/auth.json" ] && [ ! -f "$CDIR/config.toml" ] && continue

  if [ -n "$PY" ]; then
    py_emit "$HOST" "$user" "$CDIR" "$APPVER"
    found=1
  else
    emit_grep_fallback "$user" "$CDIR" && found=1
  fi
done

[ "$found" -eq 0 ] && { json_str product "codex"; json_str host "$HOST"; json_str status "not_installed"; json_emit; }
