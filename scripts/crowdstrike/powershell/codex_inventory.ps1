# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# codex_inventory.ps1
# SCRIPT_VERSION: 1.0.0
# Inventory OpenAI Codex account + plan + security metadata on Windows. RTR (SYSTEM).
# ALL profiles under C:\Users. CODEX_HOME = <profile>\.codex.
#
# Sources per profile:
#   1) .codex\auth.json  -> auth_mode; token presence; and (decoded from the id_token
#      JWT) email, plan (chatgpt_plan_type), org id, account id, expiry
#   2) .codex\config.toml -> mcp servers (egress surface), trusted project paths,
#      configured model, app version
#   3) .codex\ folder -> last_used (newest session rollout), installation_id, cred mtime
#
# SECURITY: credential VALUES are never emitted. Codex keeps email + plan ONLY inside
# the id_token JWT, so we decode that token's identity claims (email/plan/org/account/
# exp) and emit those claims — never the raw token. Access token -> JWT exp only;
# refresh token and OPENAI_API_KEY -> presence only.
#
# OUTPUT: one compact JSON object per profile (JSON-lines).
#
# This file follows the shared 5-section layout (see README.md):
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
# ===== END SHARED PRELUDE =====

# ─────────────────────────────────────────────────────────────────────────────
# 3. DISCOVERY — app version + JWT decode helpers
# ─────────────────────────────────────────────────────────────────────────────

# Codex-Version -> installed Codex desktop app version (best effort), else ''.
function Codex-Version{
  foreach($p in @("$env:LOCALAPPDATA\Programs\@openai\codex\resources\app\package.json",
                  "$env:LOCALAPPDATA\Programs\codex\resources\app\package.json",
                  "$env:ProgramFiles\Codex\resources\app\package.json")){
    if(Test-Path $p){try{return (Get-Content $p -Raw|ConvertFrom-Json).version}catch{}}
  }
  return ''
}

# Get-JwtPayload TOKEN -> the decoded JWT payload object, or $null. Decodes ONLY the
# claims segment; the token itself is never emitted.
function Get-JwtPayload([string]$tok){
  if(-not $tok -or ($tok.Split('.').Count -lt 3)){return $null}
  try{
    $p=$tok.Split('.')[1].Replace('-','+').Replace('_','/')
    switch($p.Length % 4){2{$p+='=='}3{$p+='='}}
    return [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($p))|ConvertFrom-Json
  }catch{ return $null }
}

# Get-ExpIso EXP -> a numeric unix 'exp' as UTC ISO-8601, or ''.
function Get-ExpIso($exp){
  if(-not $exp){return ''}
  try{return [DateTimeOffset]::FromUnixTimeSeconds([int64]$exp).UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ssZ')}catch{return ''}
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — read config.toml + folder metadata
# ─────────────────────────────────────────────────────────────────────────────

# Newest-SessionUtc CDIR -> mtime of the newest session rollout *.jsonl (UTC ISO-8601),
# or '' if none. This is the best "last used" signal for Codex.
function Newest-SessionUtc([string]$cdir){
  $sdir=Join-Path $cdir 'sessions'
  if(-not(Test-Path $sdir)){return ''}
  $f=Get-ChildItem -LiteralPath $sdir -Recurse -Depth 5 -Filter '*.jsonl' -File 2>$null |
     Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
  if($f){return $f.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}
  return ''
}

# Codex-UrlHost URL -> hostname of an http(s) URL, or '' on failure. Plain URLs
# (not file URIs), so [uri].Host is safe here.
function Codex-UrlHost([string]$u){ try{ return ([uri]$u).Host }catch{ return '' } }

# Parse-CodexConfig TEXT -> { mcp[], auth_meta[], projects[], model, version } from
# config.toml. Hand-rolled line-based TOML scan (no TOML parser dependency; works on
# any Windows PowerShell). Reads only names/structure per MCP server — transport, url
# host, arg count, env-var and header NAMES, and the explicit `auth = "oauth"` flag —
# never secret values or full URLs.
function Parse-CodexConfig([string]$text){
  $servers=@{}; $order=New-Object System.Collections.Generic.List[string]
  $projects=New-Object System.Collections.Generic.List[string]
  $cur=$null; $cursub=''
  foreach($raw in ($text -split "`n")){
    $line=$raw.Trim()
    if($line.StartsWith('[') -and $line.EndsWith(']')){
      $inner=$line.Substring(1,$line.Length-2).Trim()
      if($inner.StartsWith('mcp_servers.')){
        $rest=$inner.Substring('mcp_servers.'.Length)
        if($rest.StartsWith('"')){
          $e=$rest.IndexOf('"',1)
          if($e -lt 0){ $cur=$null; $cursub=''; continue }
          $name=$rest.Substring(1,$e-1); $sub=$rest.Substring($e+1).TrimStart('.')
        } else {
          $dot=$rest.IndexOf('.')
          if($dot -lt 0){ $name=$rest; $sub='' } else { $name=$rest.Substring(0,$dot); $sub=$rest.Substring($dot+1) }
        }
        $cur=$name.Trim(); $cursub=$sub.Trim()
        if($cur -and -not $servers.ContainsKey($cur)){
          $servers[$cur]=@{env=(New-Object System.Collections.Generic.List[string]); headers=(New-Object System.Collections.Generic.List[string]); command=$false; argc=0; url=''; oauth=$false}
          [void]$order.Add($cur)
        }
      } else {
        $cur=$null; $cursub=''
        $pm=[regex]::Match($inner,'^projects\.(?:"([^"]+)"|(.+))$')
        if($pm.Success){ $p=if($pm.Groups[1].Value){$pm.Groups[1].Value}else{$pm.Groups[2].Value}; if($p){[void]$projects.Add($p.Trim())} }
      }
      continue
    }
    if($null -eq $cur){continue}
    $km=[regex]::Match($line,'^("?[^"=]+"?)\s*=\s*(.*)$')
    if(-not $km.Success){continue}
    $key=$km.Groups[1].Value.Trim().Trim('"'); $val=$km.Groups[2].Value.Trim()
    if($cursub -eq 'env'){ [void]$servers[$cur].env.Add($key) }
    elseif($cursub -eq 'http_headers' -or $cursub -eq 'env_http_headers'){ [void]$servers[$cur].headers.Add($key) }
    elseif($cursub -eq ''){
      if($key -eq 'command'){ $servers[$cur].command=$true }
      elseif($key -eq 'url'){ $servers[$cur].url=$val.Trim('"') }
      elseif($key -eq 'bearer_token_env_var'){ [void]$servers[$cur].env.Add($val.Trim('"')) }
      elseif($key -eq 'auth' -and ($val.Trim('"').ToLower()) -eq 'oauth'){ $servers[$cur].oauth=$true }
      elseif($key -eq 'args'){ if($val.StartsWith('[') -and $val.EndsWith(']')){ $body=$val.Substring(1,$val.Length-2).Trim(); $servers[$cur].argc=if($body){[regex]::Matches($body,',').Count + 1}else{0} } }
    }
  }
  $mcp=@(); $authMeta=@()
  foreach($n in $order){
    $s=$servers[$n]
    $transport=if($s.url){'http'}elseif($s.command){'stdio'}else{'unknown'}
    $e=[ordered]@{name=$n; transport=$transport}
    if($transport -eq 'stdio'){ $e['command_present']=$s.command; $e['arg_count']=$s.argc }
    elseif($transport -eq 'http'){ $h=Codex-UrlHost $s.url; if($h){$e['url_host']=$h} }
    if($s.oauth){ $e['uses_oauth']=$true }
    $mcp += [pscustomobject]$e
    $env=@($s.env | Where-Object {$_} | Sort-Object -Unique)
    $hdr=@($s.headers | Where-Object {$_} | Sort-Object -Unique)
    $am=[ordered]@{name=$n}
    if($env.Count){ $am['env_var_names']=$env }
    if($hdr.Count){ $am['header_key_names']=$hdr }
    if($am.Count -gt 1){ $authMeta += [pscustomobject]$am }
  }
  $model=''; $mm=[regex]::Match($text,'(?m)^\s*model\s*=\s*"([^"]+)"'); if($mm.Success){$model=$mm.Groups[1].Value}
  $ver='';   $vm=[regex]::Match($text,'BROWSER_USE_CODEX_APP_VERSION\s*=\s*"([^"]+)"'); if($vm.Success){$ver=$vm.Groups[1].Value}
  return @{mcp=$mcp; auth_meta=$authMeta; projects=$projects; model=$model; version=$ver}
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — build one profile object; main loop collects + prints
# ─────────────────────────────────────────────────────────────────────────────

# Collect-CodexProfile USER CDIR APPVER -> a profile object, or $null if no identity
# (email/account) could be recovered.
function Collect-CodexProfile([string]$u,[string]$cdir,[string]$appver){
  $auth=Join-Path $cdir 'auth.json'; $cfg=Join-Path $cdir 'config.toml'
  $email='';$plan='';$orgid='';$acct='';$userId='';$authMode='';$lastRefresh=''
  $apiKey=$false;$rtPresent=$false;$atPresent=$false;$idPresent=$false
  $idExp='';$idExpired=$false;$atExp='';$atExpired=$false
  $now=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()

  if(Test-Path $auth){
    try{
      $a=Get-Content $auth -Raw|ConvertFrom-Json
      $authMode=[string]$a.auth_mode
      $apiKey=[bool]$a.OPENAI_API_KEY
      $lastRefresh=[string]$a.last_refresh
      $tk=$a.tokens
      if($tk){
        $acct=[string]$tk.account_id
        $idt=[string]$tk.id_token; $at=[string]$tk.access_token; $rt=[string]$tk.refresh_token
        $idPresent=[bool]$idt; $atPresent=[bool]$at; $rtPresent=[bool]$rt
        if($idt){
          $p=Get-JwtPayload $idt
          if($p){
            $email=[string]$p.email
            if($p.exp){$idExp=Get-ExpIso $p.exp; $idExpired=([int64]$p.exp -lt $now)}
            $claim=$p.PSObject.Properties['https://api.openai.com/auth']
            if($claim){
              $c=$claim.Value
              $plan=[string]$c.chatgpt_plan_type
              $orgid=[string]$c.organization_id
              if(-not $acct){$acct=[string]$c.chatgpt_account_id}
              $userId=if($c.chatgpt_user_id){[string]$c.chatgpt_user_id}else{[string]$c.user_id}
            }
          }
        }
        if($at){$ap=Get-JwtPayload $at; if($ap -and $ap.exp){$atExp=Get-ExpIso $ap.exp; $atExpired=([int64]$ap.exp -lt $now)}}
        $idt=$null;$at=$null;$rt=$null   # scrub token values
      }
    }catch{}
  }
  if(-not $plan){$plan='unknown'}

  $mcp=@();$mcpAuthMeta=@();$projects=@();$model='';$cfgVer=''
  if(Test-Path $cfg){
    try{ $parsed=Parse-CodexConfig (Get-Content $cfg -Raw)
         $mcp=@($parsed.mcp); $mcpAuthMeta=@($parsed.auth_meta); $projects=@($parsed.projects); $model=$parsed.model; $cfgVer=$parsed.version }catch{}
  }

  $lastUsed=Newest-SessionUtc $cdir
  if(-not $lastUsed){
    $si=Join-Path $cdir 'session_index.jsonl'
    if(Test-Path $si){$lastUsed=(Get-Item $si).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}
    elseif(Test-Path $auth){$lastUsed=(Get-Item $auth).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}
  }
  $cred=Test-Path $auth
  $credMtime=if($cred){(Get-Item $auth).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}else{''}
  $inst=''
  $ip=Join-Path $cdir 'installation_id'
  if(Test-Path $ip){try{$inst=((Get-Content $ip -Raw).Trim())}catch{}}
  if($inst.Length -gt 64){$inst=$inst.Substring(0,64)}
  $projTrunc=$projects.Count -gt 50
  $appVerOut=if($appver){$appver}else{$cfgVer}

  if(-not $email -and -not $acct){return $null}

  # Field order here is the output contract — keep it aligned with codex_inventory.sh.
  # auth_metadata is added below only when non-empty so the key is absent otherwise.
  $out=[ordered]@{
    product='codex'; host=$host_name; os_user=$u
    email=$email; plan=$plan; org=''; org_id=$orgid; account_uuid=$acct; user_id=$userId
    auth_method=$authMode; last_used=$lastUsed; last_refresh=$lastRefresh
    model=$model; app_version=$appVerOut; install_id=$inst
    projects_count=$projects.Count; project_paths=@($projects|Select-Object -First 50); projects_truncated=$projTrunc
    mcp_servers=@($mcp); mcp_count=@($mcp).Count
    credentials_on_disk=$cred; credentials_mtime=$credMtime
    id_token_present=$idPresent; id_token_exp=$idExp; id_token_expired=$idExpired
    access_token_present=$atPresent; access_token_exp=$atExp; access_token_expired=$atExpired
    refresh_token_present=$rtPresent; api_key_present=$apiKey
    source='auth+config'
  }
  if(@($mcpAuthMeta).Count -gt 0){ $out.auth_metadata=[pscustomobject]@{mcp_servers=$mcpAuthMeta} }
  return [pscustomobject]$out
}

# --- main --------------------------------------------------------------------
$appver=Codex-Version

foreach($profileDir in Get-Profiles){
  $u=$profileDir.Name
  $cdir=Join-Path $profileDir.FullName '.codex'
  if(-not(Test-Path $cdir)){continue}                            # no Codex footprint
  if(-not(Test-Path (Join-Path $cdir 'auth.json')) -and -not(Test-Path (Join-Path $cdir 'config.toml'))){continue}
  if(-not $seen.Add($cdir.ToLower())){continue}                  # already reported this CODEX_HOME
  $obj=Collect-CodexProfile $u $cdir $appver
  if($obj){$results += $obj}
}

Emit-Results 'codex' 'not_installed'
