# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# claude_inventory.ps1
# SCRIPT_VERSION: 1.2.0
# Inventory Claude Code account + plan + security metadata on Windows. RTR (SYSTEM).
# ALL profiles under C:\Users. Default config -> alternates -> bounded search.
#
# SECURITY: credential VALUES are never read/emitted. ~/.claude/.credentials.json
# reported as presence + mtime only. mcpServers = external data-egress surface;
# project paths = which repos the agent touched. email/org reliable locally;
# plan read from oauthAccount.seatTier / organizationType (legacy subscriptionType
# absent) -> 'unknown' only if none present (authoritative source = Anthropic
# Console/Admin API).
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
# 3. DISCOVERY — locate the Claude config file for one profile
# ─────────────────────────────────────────────────────────────────────────────

# Find-ClaudeCfg PROFILE -> that profile's .claude.json. Known locations first,
# then a bounded, recursive search as a fallback.
function Find-ClaudeCfg([string]$p){
  foreach($c in @((Join-Path $p '.claude.json'),
                  (Join-Path $p '.config\claude\.claude.json'),
                  (Join-Path $p '.config\claude\config.json'),
                  (Join-Path $p 'AppData\Roaming\claude\.claude.json'))){
    if(Test-Path $c){return $c}
  }
  $h=Get-ChildItem -LiteralPath $p -Recurse -Depth 4 -Filter '.claude.json' -File -Force 2>$null|Select-Object -First 1
  if($h){return $h.FullName}
  return $null
}

# Get-ClaudeSecretTargets PROFILE CDIR -> candidate secret-scan file paths for
# one profile: global CLAUDE.md + skills/memory files. Global scope only —
# per-project CLAUDE.md/skills files are out of scope (no cheap way to bound
# recursive scans across arbitrary repos from RTR).
function Get-ClaudeSecretTargets([string]$profile,[string]$cdir){
  $out=New-Object System.Collections.Generic.List[string]
  foreach($f in @((Join-Path $profile 'CLAUDE.md'),(Join-Path $cdir 'CLAUDE.md'))){
    if(Test-Path -LiteralPath $f -PathType Leaf){$out.Add($f)}
  }
  foreach($sub in 'skills','memory'){
    $d=Join-Path $cdir $sub
    if(Test-Path -LiteralPath $d){
      Get-ChildItem -LiteralPath $d -Recurse -Depth 4 -File -ErrorAction SilentlyContinue |
        Where-Object{$_.Extension -in '.md','.mdc'} | ForEach-Object{$out.Add($_.FullName)}
    }
  }
  return $out
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — read last-used + build one profile object
# ─────────────────────────────────────────────────────────────────────────────

# Newest-SessionUtc CDIR -> mtime of the newest *.jsonl session file (UTC ISO-8601),
# or '' if none. This is the best "last used" signal for Claude Code.
function Newest-SessionUtc([string]$cdir){
  if(-not(Test-Path $cdir)){return ''}
  $f=Get-ChildItem -LiteralPath $cdir -Recurse -Depth 4 -Filter '*.jsonl' -File 2>$null |
     Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
  if($f){return $f.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}
  return ''
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

# Collect-ClaudeProfile USER CFG CDIR PROFILE -> a profile object, or $null if no
# identity (email/org) could be recovered. Parses .claude.json for identity/plan/
# projects/mcpServers, then adds folder-derived last-used + credentials presence.
function Collect-ClaudeProfile([string]$u,[string]$cfg,[string]$cdir,[string]$profile){
  $email='';$org='';$orgid='';$plan='';$acct='';$role='';$method=''
  $numStartups='';$version='';$install='';$userId='';$firstStart=''
  $projects=@();$mcp=[ordered]@{}
  $model='';$modelCounts=@{}

  if($cfg){
    try{
      $raw=Get-Content $cfg -Raw; $j=$raw|ConvertFrom-Json
      $oa=$j.oauthAccount
      if($oa){
        if($oa.emailAddress){$email=$oa.emailAddress}
        if($oa.organizationName){$org=$oa.organizationName}
        if($oa.organizationUuid){$orgid=$oa.organizationUuid}
        if($oa.accountUuid){$acct=$oa.accountUuid}
        if($oa.organizationRole){$role=$oa.organizationRole}
      }
      if(-not $email -and $j.email){$email=$j.email}
      # Plan lives under oauthAccount.seatTier ("team_standard") / organizationType
      # ("claude_team"); subscriptionType/subscription/planType are legacy/absent.
      foreach($f in 'subscriptionType','subscription','planType','seatTier','organizationType'){
        if($j.$f){$plan=$j.$f;break}elseif($oa -and $oa.$f){$plan=$oa.$f;break}
      }
      if($j.numStartups){$numStartups=$j.numStartups}
      if($j.version){$version=$j.version}elseif($j.clientVersion){$version=$j.clientVersion}
      if($j.installMethod){$install=$j.installMethod}elseif($j.autoUpdaterStatus){$install=$j.autoUpdaterStatus}
      if($j.userID){$userId=$j.userID}elseif($j.userId){$userId=$j.userId}
      if($j.firstStartTime){$firstStart=$j.firstStartTime}
      if($j.projects){
        $projects=@($j.projects.PSObject.Properties.Name)
        foreach($pp in $j.projects.PSObject.Properties){
          if($pp.Value.mcpServers){foreach($mp in $pp.Value.mcpServers.PSObject.Properties){$mcp[$mp.Name]=$mp.Value}}  # local scope
          if($pp.Value.lastModelUsage){foreach($mu in $pp.Value.lastModelUsage.PSObject.Properties.Name){$modelCounts[$mu]=[int]$modelCounts[$mu]+1}}
          # project scope: <projectRoot>\.mcp.json (committed, team-shared). Project keys
          # are absolute paths (fwd- or back-slashed on Windows; Join-Path/Test-Path handle
          # both) -> a bounded read of known roots, not a filesystem crawl. setdefault so a
          # local-scope server of the same name (higher precedence) is not clobbered.
          try{
            $pmcp=Join-Path $pp.Name '.mcp.json'
            if(Test-Path -LiteralPath $pmcp){
              $ppj=Get-Content -LiteralPath $pmcp -Raw|ConvertFrom-Json
              if($ppj.mcpServers){foreach($mp in $ppj.mcpServers.PSObject.Properties){if(-not $mcp.Contains($mp.Name)){$mcp[$mp.Name]=$mp.Value}}}
            }
          }catch{}
        }
      }
      if($j.mcpServers){foreach($mp in $j.mcpServers.PSObject.Properties){$mcp[$mp.Name]=$mp.Value}}  # user scope
      if(-not $email){
        $m=[regex]::Match($raw,'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
        if($m.Success){$email=$m.Value}
      }
    }catch{}
  }
  if(-not $email -and -not $org){return $null}
  if(-not $plan){$plan='unknown'}

  $lastUsed=Newest-SessionUtc $cdir
  if(-not $lastUsed -and $cfg){$lastUsed=(Get-Item $cfg).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}
  $credPath=Join-Path $cdir '.credentials.json'
  $cred=Test-Path $credPath
  $credMtime=if($cred){(Get-Item $credPath).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')}else{''}
  $settingsPath=Join-Path $cdir 'settings.json'
  $settings=Test-Path $settingsPath
  if($settings){try{$sj=Get-Content $settingsPath -Raw|ConvertFrom-Json; if($sj.model){$model=$sj.model}}catch{}}
  if(-not $model -and $modelCounts.Count -gt 0){$model=($modelCounts.GetEnumerator()|Sort-Object Value -Descending|Select-Object -First 1).Key}
  $projTrunc=$projects.Count -gt 50

  $mcpServersOut=@(); $authMetaServers=@()
  foreach($mn in $mcp.Keys){
    $mcpServersOut += Get-McpTransportInfo $mn $mcp[$mn]
    $am = Get-McpAuthMeta $mn $mcp[$mn]
    if($am){$authMetaServers += $am}
  }

  $secretsScan = Get-SecretFindings (Get-ClaudeSecretTargets $profile $cdir)

  # Field order here is the output contract — keep it stable. auth_metadata is
  # added below only when non-empty, so the key is entirely ABSENT from the
  # JSON otherwise (matching the bash collector's behavior) rather than
  # present with a $null value — ConvertTo-Json would otherwise still emit
  # "auth_metadata":null for a property whose value is $null.
  $out=[ordered]@{
    product='claude'; host=$host_name; os_user=$u
    email=$email; plan=$plan; org=$org; org_id=$orgid; account_uuid=$acct; org_role=$role
    auth_method=$method; last_used=$lastUsed; num_startups=$numStartups; client_version=$version
    install_method=$install; user_id=$userId; first_start=$firstStart; model=$model
    projects_count=$projects.Count; project_paths=@($projects|Select-Object -First 50); projects_truncated=$projTrunc
    mcp_servers=$mcpServersOut; mcp_count=$mcp.Count
    credentials_on_disk=$cred; credentials_mtime=$credMtime; settings_present=$settings
    secrets_scan=$secretsScan
    source='config'
  }
  if($authMetaServers.Count -gt 0){$out.auth_metadata=[pscustomobject]@{mcp_servers=$authMetaServers}}
  return [pscustomobject]$out
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — main loop collects every profile, then prints
# ─────────────────────────────────────────────────────────────────────────────
foreach($profileDir in Get-Profiles){
  $u=$profileDir.Name; $profile=$profileDir.FullName
  $cdir=Join-Path $profile '.claude'
  $cfg=Find-ClaudeCfg $profile
  if(-not $cfg -and -not (Test-Path $cdir)){continue}          # no Claude footprint
  if($cfg -and -not $seen.Add($cfg.ToLower())){continue}       # already reported this config
  $obj=Collect-ClaudeProfile $u $cfg $cdir $profile
  if($obj){$results += $obj}
}

Emit-Results 'claude' 'not_installed'
