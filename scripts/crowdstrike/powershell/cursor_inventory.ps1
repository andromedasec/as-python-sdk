# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# cursor_inventory.ps1
# SCRIPT_VERSION: 1.2.0
# Inventory Cursor account + plan + security metadata from the SQLite state DB on
# Windows. Falcon RTR (SYSTEM). ALL profiles under C:\Users. Default path ->
# alternates -> bounded search. Prefers sqlite3.exe (RTR `put` it first); else a
# best-effort binary scrape of the DB file.
#
# SECURITY: token VALUES are never emitted. Access token -> JWT 'exp' only;
# refresh token -> presence only.
#
# OUTPUT: one compact JSON object per profile (JSON-lines).
#
# This file follows the shared 5-section layout (see ARCHITECTURE.md):
#   1 HEADER · 2 SHARED PRELUDE · 3 DISCOVERY · 4 COLLECT · 5 EMIT

# ─────────────────────────────────────────────────────────────────────────────
# 2. SHARED PRELUDE — keep byte-identical across all PowerShell collectors
#    (generic helpers only; if you edit this block, paste it into the others)
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = 'SilentlyContinue'   # keep going past expected access errors
$host_name = $env:COMPUTERNAME
$results   = @()                                                    # collected profile objects
$seen      = New-Object System.Collections.Generic.HashSet[string]  # dedup set (lower-cased paths)

# Get-Profiles -> every user profile directory under C:\Users.
# (RTR runs as SYSTEM, so we inventory all users, not just the current one.)
function Get-Profiles { Get-ChildItem 'C:\Users' -Directory }

# Emit-Results PRODUCT EMPTY_STATUS -> print one compact JSON line per collected
# object, or a single {product,host,status} object when nothing was found.
function Emit-Results([string]$product,[string]$emptyStatus){
  if($results.Count -eq 0){
    [pscustomobject]@{product=$product; host=$host_name; status=$emptyStatus} | ConvertTo-Json -Compress
  } else {
    $results | ForEach-Object { $_ | ConvertTo-Json -Compress -Depth 4 }
  }
}

# Secret-pattern table: service -> regex. Flags credential-SHAPED strings by
# pattern only — never captures or emits the matched substring, just which
# service it maps to and where (file + line number). Extend to add services.
$SecretPatterns = [ordered]@{
  aws_access_key      = 'AKIA[0-9A-Z]{16}'
  github_token        = 'gh[pousr]_[A-Za-z0-9]{20,}'
  github_fine_grained = 'github_pat_[A-Za-z0-9_]{60,}'
  slack_token         = 'xox[baprs]-[A-Za-z0-9-]{10,}'
  slack_webhook       = 'hooks\.slack\.com/services/T[0-9A-Za-z]+/B[0-9A-Za-z]+/[0-9A-Za-z]+'
  openai_key          = 'sk-[A-Za-z0-9]{20,}'
  anthropic_key       = 'sk-ant-[A-Za-z0-9_-]{20,}'
  google_api_key      = 'AIza[0-9A-Za-z_-]{35}'
  stripe_key          = '(sk|pk)_live_[0-9A-Za-z]{20,}'
  sendgrid_key        = 'SG\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}'
  npm_token           = 'npm_[A-Za-z0-9]{30,}'
  private_key_block   = '-----BEGIN[A-Z ]*PRIVATE KEY-----'
  jwt                 = 'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
  generic_credential  = '(api[_-]?key|apikey|secret|token|password)\s*[:=]\s*[A-Za-z0-9_-]{16,}'
}

# Get-SecretFindings PATH[] -> [pscustomobject]@{files_scanned; findings=@(...)}.
# Scans each given file (skips missing/unreadable/>512KB) against $SecretPatterns
# line by line, recording only file+service+line — never the matched text.
# Caps total findings at 50 so one noisy file can't blow up the output.
function Get-SecretFindings([string[]]$paths){
  $findings=New-Object System.Collections.Generic.List[object]
  $scanned=0; $cap=50
  foreach($f in $paths){
    if($findings.Count -ge $cap){break}
    if(-not(Test-Path -LiteralPath $f -PathType Leaf)){continue}
    try{
      $item=Get-Item -LiteralPath $f -Force -ErrorAction Stop
      if($item.Length -gt 524288){continue}
      $scanned++
      $lines=@(Get-Content -LiteralPath $f -Force -ErrorAction Stop)
      for($i=0;$i -lt $lines.Count -and $findings.Count -lt $cap;$i++){
        foreach($svc in $SecretPatterns.Keys){
          if([regex]::IsMatch($lines[$i],$SecretPatterns[$svc],[Text.RegularExpressions.RegexOptions]::IgnoreCase)){
            $findings.Add([pscustomobject]@{file=$f; service=$svc; line=($i+1)})
          }
        }
      }
    }catch{}
  }
  return [pscustomobject]@{files_scanned=$scanned; findings=$findings.ToArray()}
}
# ===== END SHARED PRELUDE =====

# ─────────────────────────────────────────────────────────────────────────────
# 3. DISCOVERY — locate Cursor's state DB(s) and app version
# ─────────────────────────────────────────────────────────────────────────────

# Find-CursorDbs PROFILE -> each Cursor state.vscdb path for that profile.
# Known default locations first; only if none exist do we do a bounded search.
function Find-CursorDbs([string]$profile){
  $out=New-Object System.Collections.Generic.List[string]
  foreach($r in @('AppData\Roaming','AppData\Local')){
    $d=Join-Path $profile "$r\Cursor\User\globalStorage\state.vscdb"
    if(Test-Path $d){$out.Add($d)}
  }
  if($out.Count -gt 0){return $out}
  foreach($root in @((Join-Path $profile 'AppData\Roaming'),(Join-Path $profile 'AppData\Local'))){
    if(-not(Test-Path $root)){continue}
    Get-ChildItem -LiteralPath $root -Recurse -Depth 6 -Filter 'state.vscdb' -File 2>$null |
      Where-Object{$_.FullName -match 'Cursor' -and $_.FullName -match 'globalStorage'} |
      ForEach-Object{$out.Add($_.FullName)}
  }
  return $out
}

# Cursor-Version -> installed Cursor app version (best effort), else ''.
function Cursor-Version{
  foreach($p in @("$env:LOCALAPPDATA\Programs\Cursor\resources\app\package.json",
                  "$env:ProgramFiles\Cursor\resources\app\package.json")){
    if(Test-Path $p){try{return (Get-Content $p -Raw|ConvertFrom-Json).version}catch{}}
  }
  return ''
}

# Get-CursorSecretTargets PROFILE -> candidate secret-scan file paths for one
# profile: global .cursorrules + .cursor\rules + .cursor\skills-cursor +
# .cursor\memory. Global scope only — Cursor doesn't track a project list we
# can cheaply reuse (unlike Claude's projects), so per-project .cursorrules/
# .cursor\rules files are out of scope.
function Get-CursorSecretTargets([string]$profile){
  $out=New-Object System.Collections.Generic.List[string]
  $legacy=Join-Path $profile '.cursorrules'
  if(Test-Path -LiteralPath $legacy -PathType Leaf){$out.Add($legacy)}
  foreach($sub in '.cursor\rules','.cursor\skills-cursor','.cursor\memory'){
    $d=Join-Path $profile $sub
    if(Test-Path -LiteralPath $d){
      Get-ChildItem -LiteralPath $d -Recurse -Depth 4 -File -ErrorAction SilentlyContinue |
        Where-Object{$_.Extension -in '.md','.mdc'} | ForEach-Object{$out.Add($_.FullName)}
    }
  }
  return $out
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — read DB values (+ helpers) and build one profile object
# ─────────────────────────────────────────────────────────────────────────────

# Read-Shared PATH -> file bytes, opened ReadWrite-shared so we can read the DB
# even while Cursor holds it open.
function Read-Shared([string]$path){
  $fs=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
  try{$l=[int]$fs.Length;$b=New-Object byte[] $l;[void]$fs.Read($b,0,$l);return $b}finally{$fs.Dispose()}
}

# Initialize-WinSqlite -> $true if the in-box winsqlite3.dll is usable on this host.
# winsqlite3.dll ships in System32 on Windows 10/11 and Server 2016+ — a real SQLite
# engine reachable with zero install. We P/Invoke the UTF-16 ("*16") entry points so
# .NET strings marshal directly (no manual UTF-8 handling). On older Windows the DLL
# is absent and the P/Invoke throws DllNotFoundException -> we return $false and the
# caller falls through to the next reader.
function Initialize-WinSqlite{
  if(-not ([System.Management.Automation.PSTypeName]'WinSql').Type){
    try{
      Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class WinSql {
  [DllImport("winsqlite3.dll", CallingConvention=CallingConvention.Cdecl, CharSet=CharSet.Unicode)]
  public static extern int sqlite3_open16(string filename, out IntPtr db);
  [DllImport("winsqlite3.dll", CallingConvention=CallingConvention.Cdecl, CharSet=CharSet.Unicode)]
  public static extern int sqlite3_prepare16_v2(IntPtr db, string sql, int nByte, out IntPtr stmt, IntPtr tail);
  [DllImport("winsqlite3.dll", CallingConvention=CallingConvention.Cdecl)]
  public static extern int sqlite3_step(IntPtr stmt);
  [DllImport("winsqlite3.dll", CallingConvention=CallingConvention.Cdecl)]
  public static extern IntPtr sqlite3_column_text16(IntPtr stmt, int iCol);
  [DllImport("winsqlite3.dll", CallingConvention=CallingConvention.Cdecl)]
  public static extern int sqlite3_finalize(IntPtr stmt);
  [DllImport("winsqlite3.dll", CallingConvention=CallingConvention.Cdecl)]
  public static extern int sqlite3_close(IntPtr db);
}
"@
    }catch{return $false}   # Add-Type/csc unavailable (rare, locked-down hosts)
  }
  try{
    $h=[IntPtr]::Zero
    $rc=[WinSql]::sqlite3_open16(':memory:',[ref]$h)   # throws if the DLL is missing
    if($h -ne [IntPtr]::Zero){[void][WinSql]::sqlite3_close($h)}
    return ($rc -eq 0)
  }catch{return $false}
}

# Get-WinSqlValue DBHANDLE KEY -> the ItemTable value for KEY via an open winsqlite3
# handle, or '' if missing/unreadable (SQLITE_ROW = 100). Caller opens/closes the DB.
function Get-WinSqlValue([IntPtr]$db,[string]$key){
  $stmt=[IntPtr]::Zero
  $sql="SELECT value FROM ItemTable WHERE key='" + $key.Replace("'","''") + "'"
  if([WinSql]::sqlite3_prepare16_v2($db,$sql,-1,[ref]$stmt,[IntPtr]::Zero) -ne 0){return ''}
  try{
    if([WinSql]::sqlite3_step($stmt) -eq 100){
      $p=[WinSql]::sqlite3_column_text16($stmt,0)
      if($p -ne [IntPtr]::Zero){return [Runtime.InteropServices.Marshal]::PtrToStringUni($p)}
    }
  }finally{[void][WinSql]::sqlite3_finalize($stmt)}
  return ''
}

# Read-PyDump EXE PREARGS DBPATH -> hashtable of ItemTable key -> value via python's
# stdlib sqlite3 (no external sqlite3 binary). Dumps every row once as
# key<TAB>base64(value) so we parse it locally. Used only if winsqlite3 + sqlite3.exe
# are both absent. Returns an empty hashtable on any failure.
function Read-PyDump([string]$exe,[string[]]$pre,[string]$dbPath){
  $code=@'
import sqlite3, sys, base64
con = sqlite3.connect(sys.argv[1]); con.text_factory = bytes
out = getattr(sys.stdout, "buffer", sys.stdout)
for k, v in con.execute("SELECT key, value FROM ItemTable"):
    if v is None: v = b""
    elif not isinstance(v, (bytes, bytearray)): v = str(v).encode("utf-8")
    if isinstance(k, bytes): k = k.decode("utf-8", "replace")
    out.write(k.encode("utf-8") + b"\t" + base64.b64encode(bytes(v)) + b"\n")
con.close()
'@
  $h=@{}
  try{
    $lines = & $exe @pre '-c' $code $dbPath 2>$null
    foreach($ln in $lines){
      $t=$ln.IndexOf("`t"); if($t -lt 0){continue}
      try{$h[$ln.Substring(0,$t)]=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($ln.Substring($t+1)))}catch{}
    }
  }catch{}
  return $h
}

# Get-VscValue TEXT KEY -> value following KEY in a raw DB text scrape (no sqlite3).
# Walks printable chars after the key until the run ends.
function Get-VscValue([string]$text,[string]$key){
  $i=$text.IndexOf($key); if($i -lt 0){return ''}
  $sb=New-Object System.Text.StringBuilder
  for($j=$i+$key.Length;$j -lt $text.Length;$j++){
    $c=[int]$text[$j]
    if($c -ge 32 -and $c -lt 127){[void]$sb.Append($text[$j])}elseif($sb.Length -gt 0){break}
  }
  return $sb.ToString().Trim('"').Trim()
}

# Get-JwtExp TOKEN -> the JWT 'exp' as UTC ISO-8601, WITHOUT emitting the token.
function Get-JwtExp([string]$tok){
  if(-not $tok -or ($tok.Split('.').Count -lt 3)){return $null}
  try{
    $p=$tok.Split('.')[1].Replace('-','+').Replace('_','/')
    switch($p.Length % 4){2{$p+='=='}3{$p+='='}}
    $json=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))
    $exp=([regex]::Match($json,'"exp"\s*:\s*(\d+)')).Groups[1].Value
    if($exp){return [DateTimeOffset]::FromUnixTimeSeconds([int64]$exp).UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ssZ')}
  }catch{}
  return $null
}

# Get-McpTransportInfo NAME CFG -> a pscustomobject describing structural shape
# only (transport/command-presence/arg-count/url-host) — never command/args/url
# values themselves beyond a bare hostname for remote servers.
function Get-McpTransportInfo([string]$name,$cfg){
  $url=''; if($cfg.url){$url=$cfg.url}elseif($cfg.baseUrl){$url=$cfg.baseUrl}
  $transport=''
  if($cfg.type){$transport=([string]$cfg.type).ToLower()}elseif($cfg.transport){$transport=([string]$cfg.transport).ToLower()}
  if(-not $transport){ if($url){$transport='http'}elseif($cfg.command){$transport='stdio'}else{$transport='unknown'} }
  $entry=[ordered]@{name=$name; transport=$transport}
  if($transport -eq 'stdio'){
    $entry.command_present=[bool]$cfg.command
    $entry.arg_count=if($cfg.args){@($cfg.args).Count}else{0}
  }elseif(($transport -eq 'http' -or $transport -eq 'sse') -and $url){
    try{$h=([uri]$url).Host; if($h){$entry.url_host=$h}}catch{}
  }
  return [pscustomobject]$entry
}

# Get-McpAuthMeta NAME CFG -> a pscustomobject with env_var_names/header_key_names/
# filesystem_scope_paths (names/indicators only — never values), or $null if none apply.
function Get-McpAuthMeta([string]$name,$cfg){
  $envNames=@(); if($cfg.env){$envNames=@($cfg.env.PSObject.Properties.Name|Sort-Object)}
  $headerNames=@(); if($cfg.headers){$headerNames=@($cfg.headers.PSObject.Properties.Name|Sort-Object)}
  $fsPaths=@()
  $args=@(); if($cfg.args){$args=@($cfg.args|ForEach-Object{[string]$_})}
  $cmd=if($cfg.command){[string]$cfg.command}else{''}
  if(($cmd + ' ' + ($args -join ' ')) -match 'server-filesystem'){
    $fsPaths=@($args|Where-Object{$_ -notmatch '^-' -and $_ -notmatch 'server-filesystem' -and $_ -notmatch '=' -and $_ -match '^(/|\./|\.\./|~|[A-Za-z]:\\|\\\\)'})
  }
  $entry=[ordered]@{name=$name}
  if($envNames.Count -gt 0){$entry.env_var_names=$envNames}
  if($headerNames.Count -gt 0){$entry.header_key_names=$headerNames}
  if($fsPaths.Count -gt 0){$entry.filesystem_scope_paths=$fsPaths}
  if($entry.Count -gt 1){return [pscustomobject]$entry}
  return $null
}

# Read-CursorMcpConfig PROFILE -> hashtable of server name -> config object, from the
# GLOBAL PROFILE\.cursor\mcp.json (user scope). Returns an empty hashtable on any failure.
function Read-CursorMcpConfig([string]$profile){
  $h=@{}
  $cfgPath=Join-Path $profile '.cursor\mcp.json'
  if(-not(Test-Path $cfgPath)){return $h}
  try{
    $j=Get-Content $cfgPath -Raw|ConvertFrom-Json
    if($j.mcpServers){foreach($mp in $j.mcpServers.PSObject.Properties){$h[$mp.Name]=$mp.Value}}
  }catch{}
  return $h
}

# Read-CursorProjectMcpConfigs WSDIR -> hashtable of server name -> config, from each
# <folder>\.cursor\mcp.json for every folder Cursor has opened. Folders are enumerated
# from WSDIR\*\workspace.json (a bounded set of known roots — never a filesystem crawl).
# The workspace.json "folder" is a file URI (e.g. file:///c%3A/Users/x/proj);
# ([uri]).LocalPath decodes it to a native path, with a manual fallback.
function Read-CursorProjectMcpConfigs([string]$wsDir){
  $h=@{}
  if(-not(Test-Path $wsDir)){return $h}
  foreach($wj in (Get-ChildItem $wsDir -Recurse -Filter workspace.json -EA 0)){
    try{
      $folder=(Get-Content -LiteralPath $wj.FullName -Raw|ConvertFrom-Json).folder
      if(-not $folder){continue}
      # "folder" is a file URI with a URL-encoded, forward-slashed path, e.g.
      # file:///c%3A/Users/x/proj. [uri].LocalPath mis-handles the encoded drive colon
      # (yields /c:/Users/...), so parse manually: strip file:/// , URL-decode, normalize.
      $path=[uri]::UnescapeDataString(($folder -replace '^file:/+','')) -replace '/','\'
      if(-not $path){continue}
      $cfgPath=Join-Path $path '.cursor\mcp.json'
      if(Test-Path -LiteralPath $cfgPath){
        $j=Get-Content -LiteralPath $cfgPath -Raw|ConvertFrom-Json
        if($j.mcpServers){foreach($mp in $j.mcpServers.PSObject.Properties){if(-not $h.ContainsKey($mp.Name)){$h[$mp.Name]=$mp.Value}}}
      }
    }catch{}
  }
  return $h
}

# ItemTable keys we pull as plain values (token keys are handled separately below).
$keys=[ordered]@{
  email='cursorAuth/cachedEmail'; plan='cursorAuth/stripeMembershipType'
  joined='cursorAuth/onboardingDate'; auth_method='cursorAuth/cachedSignUpType'
  scopes='cursorAuth/scopes'; service_machine_id='storage.serviceMachineId'
  machine_id='telemetry.machineId'; dev_device_id='telemetry.devDeviceId'
  sqm_id='telemetry.sqmId'; first_session='telemetry.firstSessionDate'
  last_session='telemetry.lastSessionDate'; current_session='telemetry.currentSessionDate'
}

# Get-WinSqlRows DBPATH SQL -> every single-column string value for SQL via winsqlite3.
function Get-WinSqlRows([string]$dbPath,[string]$sql){
  $rows=@(); $dbh=[IntPtr]::Zero
  if([WinSql]::sqlite3_open16($dbPath,[ref]$dbh) -ne 0){
    if($dbh -ne [IntPtr]::Zero){[void][WinSql]::sqlite3_close($dbh)}; return $rows
  }
  try{
    $stmt=[IntPtr]::Zero
    if([WinSql]::sqlite3_prepare16_v2($dbh,$sql,-1,[ref]$stmt,[IntPtr]::Zero) -eq 0){
      try{
        while([WinSql]::sqlite3_step($stmt) -eq 100){
          $p=[WinSql]::sqlite3_column_text16($stmt,0)
          if($p -ne [IntPtr]::Zero){$rows+=[Runtime.InteropServices.Marshal]::PtrToStringUni($p)}
        }
      }finally{[void][WinSql]::sqlite3_finalize($stmt)}
    }
  }finally{[void][WinSql]::sqlite3_close($dbh)}
  return $rows
}

# Get-CursorModel ... -> dominant non-"default" composer model from cursorDiskKV, or ''.
# Cursor is multi-model/per-chat; we surface the most-used explicit model. Fully
# defensive (any failure -> '') so it can never break the rest of the inventory.
function Get-CursorModel([string]$dbPath,[bool]$winOk,[string]$sqlite,[string]$pyExe,[string[]]$pyPre){
  try{
    $blob=''
    if($winOk){ $blob=((Get-WinSqlRows $dbPath "SELECT value FROM cursorDiskKV WHERE key LIKE 'composerData:%'") -join "`n") }
    if(-not $blob -and $sqlite){ $blob=(& $sqlite $dbPath "SELECT value FROM cursorDiskKV WHERE key LIKE 'composerData:%';" 2>$null|Out-String) }
    if(-not $blob -and $pyExe){
      $code=@'
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
'@
      $blob=(& $pyExe @pyPre '-c' $code $dbPath 2>$null|Out-String)
    }
    if(-not $blob){return ''}
    $counts=@{}
    foreach($m in [regex]::Matches($blob,'"modelName"\s*:\s*"([^"]*)"')){
      $name=$m.Groups[1].Value
      if($name -and $name -ne 'default'){$counts[$name]=[int]$counts[$name]+1}
    }
    if($counts.Count -eq 0){return ''}
    return ($counts.GetEnumerator()|Sort-Object Value -Descending|Select-Object -First 1).Key
  }catch{ return '' }
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — process one DB into a profile object; main loop collects + prints
# ─────────────────────────────────────────────────────────────────────────────

# Collect-CursorDb USER DB SQLITE APPVER WINOK PYEXE PYPRE -> a profile object, or
# $null if the DB has no account info. Copies the DB (+ WAL/SHM sidecars) to TEMP,
# reads it via the first available engine (winsqlite3 -> sqlite3.exe -> python3 ->
# regex scrape), records which in `source`, then scrubs token values.
function Collect-CursorDb([string]$u,[string]$db,[string]$sqlite,[string]$appver,[bool]$winOk,[string]$pyExe,[string[]]$pyPre,[string]$profileHome){
  $v=@{}; foreach($k in $keys.Keys){$v[$k]=''}
  $at=''; $rt=''; $src=''; $mcpRaw=''
  $tmp=Join-Path $env:TEMP ("cur_{0}_{1}.vscdb" -f $u,([guid]::NewGuid().ToString('N').Substring(0,6)))
  try{[IO.File]::WriteAllBytes($tmp,(Read-Shared $db))}catch{return $null}
  # Bring the WAL/SHM sidecars alongside the copy so a real engine merges fresh,
  # un-checkpointed writes (recent sign-ins land in the -wal before the main DB).
  foreach($sx in '-wal','-shm'){
    if(Test-Path ($db+$sx)){try{[IO.File]::WriteAllBytes(($tmp+$sx),(Read-Shared ($db+$sx)))}catch{}}
  }

  # Reader cascade, most reliable first; $src records which one actually read the DB.
  $handled=$false
  # 1) in-box winsqlite3.dll — real engine, no install, WAL-correct.
  if($winOk){
    $dbh=[IntPtr]::Zero
    if([WinSql]::sqlite3_open16($tmp,[ref]$dbh) -eq 0){
      try{
        foreach($k in $keys.Keys){$v[$k]=(Get-WinSqlValue $dbh $keys[$k]).Trim().Trim('"')}
        $at=(Get-WinSqlValue $dbh 'cursorAuth/accessToken').Trim().Trim('"')
        $rt=(Get-WinSqlValue $dbh 'cursorAuth/refreshToken').Trim().Trim('"')
        $mcpRaw=(Get-WinSqlValue $dbh 'mcpService.knownServerIds').Trim()
        $src='winsqlite3'; $handled=$true
      }finally{[void][WinSql]::sqlite3_close($dbh)}
    } elseif($dbh -ne [IntPtr]::Zero){[void][WinSql]::sqlite3_close($dbh)}
  }
  # 2) sqlite3.exe on PATH or `put` into the RTR session dir.
  if(-not $handled -and $sqlite){
    foreach($k in $keys.Keys){
      $r=& $sqlite $tmp ("SELECT value FROM ItemTable WHERE key='{0}';" -f $keys[$k]) 2>$null
      $v[$k]=($r|Out-String).Trim().Trim('"')
    }
    $at=(& $sqlite $tmp "SELECT value FROM ItemTable WHERE key='cursorAuth/accessToken';" 2>$null|Out-String).Trim().Trim('"')
    $rt=(& $sqlite $tmp "SELECT value FROM ItemTable WHERE key='cursorAuth/refreshToken';" 2>$null|Out-String).Trim().Trim('"')
    $mcpRaw=(& $sqlite $tmp "SELECT value FROM ItemTable WHERE key='mcpService.knownServerIds';" 2>$null|Out-String).Trim()
    $src='sqlite3'; $handled=$true
  }
  # 3) python3 stdlib sqlite3 — no external binary.
  if(-not $handled -and $pyExe){
    $dump=Read-PyDump $pyExe $pyPre $tmp
    if($dump.Count -gt 0){
      foreach($k in $keys.Keys){if($dump[$keys[$k]]){$v[$k]=$dump[$keys[$k]].Trim().Trim('"')}}
      if($dump['cursorAuth/accessToken']){$at=$dump['cursorAuth/accessToken'].Trim().Trim('"')}
      if($dump['cursorAuth/refreshToken']){$rt=$dump['cursorAuth/refreshToken'].Trim().Trim('"')}
      if($dump['mcpService.knownServerIds']){$mcpRaw=$dump['mcpService.knownServerIds'].Trim()}
      $src='python-sqlite3'; $handled=$true
    }
  }
  # 4) last resort: lossy regex scrape of the raw bytes (no real engine available).
  if(-not $handled){
    $text=[Text.Encoding]::GetEncoding('ISO-8859-1').GetString((Read-Shared $tmp))
    foreach($k in $keys.Keys){$v[$k]=Get-VscValue $text $keys[$k]}
    $at=Get-VscValue $text 'cursorAuth/accessToken'
    $rt=Get-VscValue $text 'cursorAuth/refreshToken'
    $mcpRaw=Get-VscValue $text 'mcpService.knownServerIds'
    $src='binary-scrape'
  }
  $model=Get-CursorModel $tmp $winOk $sqlite $pyExe $pyPre
  foreach($sx in '','-wal','-shm'){Remove-Item ($tmp+$sx) -Force -ErrorAction SilentlyContinue}
  if(-not $v.email -and -not $v.plan){return $null}

  $atExp=Get-JwtExp $at
  $atPresent=[bool]$at; $rtPresent=[bool]$rt
  $atExpired=$false
  if($atExp){$atExpired=([datetime]$atExp -lt (Get-Date).ToUniversalTime())}
  $at=$null; $rt=$null  # scrub token values

  # mcp_servers: server config comes from config files — the global
  # <profile>\.cursor\mcp.json (user scope) and each opened project's
  # <folder>\.cursor\mcp.json (project scope; folders enumerated from Cursor's
  # workspaceStorage, a bounded set of known roots). The DB's mcpService.knownServerIds
  # is intentionally NOT used: it stores scope-mangled ids (user-<name>,
  # project-<n>-<folder>-<name>) that can't be normalized back to the config key and
  # would duplicate config-derived entries. Never emit config/secret env/header VALUES.
  $wsDir=$db -replace 'globalStorage\\state\.vscdb$','workspaceStorage'
  $mcpConfig=Read-CursorMcpConfig $profileHome
  $projCfg=Read-CursorProjectMcpConfigs $wsDir
  foreach($k in @($projCfg.Keys)){ if(-not $mcpConfig.ContainsKey($k)){$mcpConfig[$k]=$projCfg[$k]} }  # global wins on clash

  $mcpNames=New-Object System.Collections.Generic.List[string]
  $nameSeen=New-Object System.Collections.Generic.HashSet[string]
  foreach($mn in @($mcpConfig.Keys)){
    if($mn -and $nameSeen.Add($mn)){[void]$mcpNames.Add($mn)}
  }

  $mcp=@(); $authMetaServers=@()
  foreach($mn in $mcpNames){
    if($mcpConfig.ContainsKey($mn)){
      $mcp += Get-McpTransportInfo $mn $mcpConfig[$mn]
      $am=Get-McpAuthMeta $mn $mcpConfig[$mn]
      if($am){$authMetaServers += $am}
    } else {
      $mcp += [pscustomobject]@{name=$mn; transport='unknown'}
    }
  }

  $secretsScan = Get-SecretFindings (Get-CursorSecretTargets $profileHome)

  $dbMtime=(Get-Item $db).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
  # last_used: currentSessionDate is the MOST recent launch; lastSessionDate is the
  # one before it (understates recency). Order: current -> last -> DB file mtime.
  $lastUsed=if($v.current_session){$v.current_session}elseif($v.last_session){$v.last_session}else{$dbMtime}
  $wsCount=0; if(Test-Path $wsDir){$wsCount=(Get-ChildItem $wsDir -Directory 2>$null).Count}

  # Field order here is the output contract — keep it stable. auth_metadata is
  # added below only when non-empty, so the key is entirely ABSENT from the
  # JSON otherwise (matching the bash collector's behavior) rather than
  # present with a $null value — ConvertTo-Json would otherwise still emit
  # "auth_metadata":null for a property whose value is $null.
  $out=[ordered]@{
    product='cursor'; host=$host_name; os_user=$u
    email=$v.email; plan=$v.plan; joined=$v.joined; auth_method=$v.auth_method
    scopes=$v.scopes; model=$model; last_used=$lastUsed; db_mtime=$dbMtime
    first_session=$v.first_session; current_session=$v.current_session
    workspace_count=$wsCount; mcp_servers=$mcp; mcp_count=$mcpNames.Count
    machine_id=$v.machine_id; dev_device_id=$v.dev_device_id
    service_machine_id=$v.service_machine_id; sqm_id=$v.sqm_id
    access_token_present=$atPresent; access_token_exp=$atExp; access_token_expired=$atExpired
    refresh_token_present=$rtPresent; app_version=$appver; db_path=$db; source=$src
    secrets_scan=$secretsScan
  }
  if($authMetaServers.Count -gt 0){$out.auth_metadata=[pscustomobject]@{mcp_servers=$authMetaServers}}
  return [pscustomobject]$out
}

# --- main --------------------------------------------------------------------
# Reader cascade (most reliable first): in-box winsqlite3.dll -> sqlite3.exe (PATH or
# `put` into the RTR session dir) -> python3 stdlib -> regex scrape. Probe each once.
$winOk=Initialize-WinSqlite

$sqlite=(Get-Command sqlite3.exe -ErrorAction SilentlyContinue).Source
if(-not $sqlite){   # RTR `put` drops files into the session working dir, not onto PATH
  foreach($c in @((Join-Path (Get-Location).Path 'sqlite3.exe'),
                  $(if($PSScriptRoot){Join-Path $PSScriptRoot 'sqlite3.exe'}))){
    if($c -and (Test-Path $c)){$sqlite=$c; break}
  }
}

# python is a *secondary* fallback on Windows: not installed by default, and a bare
# `python`/`python3` often resolves to the Microsoft Store execution-alias stub that
# does nothing non-interactively. Probe candidates and keep only one that can actually
# `import sqlite3` (the `py -3` launcher is the reliable form when present).
$pyExe=''; $pyPre=@()
foreach($cand in 'py|-3','python3|','python|'){
  $parts=$cand.Split('|'); $exe=$parts[0]; $pre=@(); if($parts[1]){$pre=@($parts[1])}
  try{
    $probe=& $exe @pre '-c' 'import sqlite3;print(1)' 2>$null
    if(($probe|Out-String).Trim() -eq '1'){$pyExe=$exe; $pyPre=$pre; break}
  }catch{}
}

$appver=Cursor-Version

foreach($profileDir in Get-Profiles){
  $u=$profileDir.Name
  foreach($db in (Find-CursorDbs $profileDir.FullName)){
    if(-not $seen.Add($db.ToLower())){continue}   # already reported this DB
    $obj=Collect-CursorDb $u $db $sqlite $appver $winOk $pyExe $pyPre $profileDir.FullName
    if($obj){$results += $obj}
  }
}

Emit-Results 'cursor' 'not_installed_or_no_profile'
