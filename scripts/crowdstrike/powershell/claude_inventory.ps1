# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# claude_inventory.ps1
# SCRIPT_VERSION: 1.0.0
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

# Collect-ClaudeProfile USER CFG CDIR -> a profile object, or $null if no identity
# (email/org) could be recovered. Parses .claude.json for identity/plan/projects/
# mcpServers, then adds folder-derived last-used + credentials presence.
function Collect-ClaudeProfile([string]$u,[string]$cfg,[string]$cdir){
  $email='';$org='';$orgid='';$plan='';$acct='';$role='';$method=''
  $numStartups='';$version='';$install='';$userId='';$firstStart=''
  $projects=@();$mcp=New-Object System.Collections.Generic.HashSet[string]
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
          if($pp.Value.mcpServers){foreach($m in $pp.Value.mcpServers.PSObject.Properties.Name){[void]$mcp.Add($m)}}
          if($pp.Value.lastModelUsage){foreach($mu in $pp.Value.lastModelUsage.PSObject.Properties.Name){$modelCounts[$mu]=[int]$modelCounts[$mu]+1}}
        }
      }
      if($j.mcpServers){foreach($m in $j.mcpServers.PSObject.Properties.Name){[void]$mcp.Add($m)}}
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

  # Field order here is the output contract — keep it stable.
  return [pscustomobject]@{
    product='claude'; host=$host_name; os_user=$u
    email=$email; plan=$plan; org=$org; org_id=$orgid; account_uuid=$acct; org_role=$role
    auth_method=$method; last_used=$lastUsed; num_startups=$numStartups; client_version=$version
    install_method=$install; user_id=$userId; first_start=$firstStart; model=$model
    projects_count=$projects.Count; project_paths=@($projects|Select-Object -First 50); projects_truncated=$projTrunc
    mcp_servers=@($mcp); mcp_count=$mcp.Count
    credentials_on_disk=$cred; credentials_mtime=$credMtime; settings_present=$settings
    source='config'
  }
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
  $obj=Collect-ClaudeProfile $u $cfg $cdir
  if($obj){$results += $obj}
}

Emit-Results 'claude' 'not_installed'
