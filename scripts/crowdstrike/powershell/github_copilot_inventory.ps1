# ─────────────────────────────────────────────────────────────────────────────
# 1. HEADER
# ─────────────────────────────────────────────────────────────────────────────
# github_copilot_inventory.ps1
# SCRIPT_VERSION: 1.1.0
# Inventory GitHub Copilot usage on Windows. Falcon RTR (SYSTEM). ALL profiles
# under C:\Users.
#
# Copilot ships as an IDE extension AND (since 2026) as a standalone CLI + desktop
# app. We combine several on-disk signals:
#   1) Shared OAuth store  %LOCALAPPDATA%\github-copilot\apps.json (older hosts.json)
#      -> github_login (the "user" field). Reliably present for JetBrains users;
#      often ABSENT for VS Code users whose token lives in the OS keychain.
#   2) Editor installs -> which editors have Copilot + version:
#      - VS Code:  ~\.vscode\extensions\github.copilot-<ver> (+ -server / -insiders)
#      - JetBrains: %APPDATA%\JetBrains\<Product>\plugins\github-copilot-intellij
#   3) Standalone Copilot CLI  ~\.copilot\ (config.json + data.db). Version from the
#      "data.db.pre-update-backup-<ver>-<epoch>" backups. Identity is in the OS
#      credential store, so presence + version only (github_login stays empty).
#   4) Standalone Copilot desktop app ("GitHub Copilot", GA 2026). Per-user data
#      under %APPDATA%\com.github.githubapp (install: %LOCALAPPDATA%\Programs\GitHub
#      Copilot); version from %LOCALAPPDATA%\copilot-desktop-gh-<ver>. Identity in
#      the OS credential store (empty github_login).
#
# SECURITY: the oauth_token VALUE is never read or emitted. apps.json -> presence +
# mtime only. The CLI's config.json is JSONC (first-launch timestamp only) and is
# never parsed — presence only. Seat/plan is NOT on disk (GitHub billing API) ->
# plan is "unknown".
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
# 3. DISCOVERY — locate Copilot's auth store and editor installs for one profile
# ─────────────────────────────────────────────────────────────────────────────

# Find-CopilotAuth PROFILE -> the profile's github-copilot auth store path
# (apps.json preferred, hosts.json fallback), else $null.
function Find-CopilotAuth([string]$profile){
  foreach($base in @((Join-Path $profile 'AppData\Local\github-copilot'),
                     (Join-Path $profile '.config\github-copilot'))){
    foreach($name in 'apps.json','hosts.json'){
      $p=Join-Path $base $name
      if(Test-Path $p){return $p}
    }
  }
  return $null
}

# Get-VscExtRoots PROFILE -> each VS Code extensions dir that exists for the profile.
function Get-VscExtRoots([string]$profile){
  $out=@()
  foreach($r in '.vscode\extensions','.vscode-server\extensions','.vscode-insiders\extensions'){
    $d=Join-Path $profile $r
    if(Test-Path $d){$out+=$d}
  }
  return $out
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. COLLECT — extract identity, editors, and version for one profile
# ─────────────────────────────────────────────────────────────────────────────

# Get-GhLogin FILE -> the "user" (github login) from apps.json/hosts.json, else ''.
# Prefers a github.com host entry. The token value is never read.
function Get-GhLogin([string]$file){
  try{
    $j=Get-Content $file -Raw | ConvertFrom-Json
    $props=@($j.PSObject.Properties)
    $ordered=$props | Sort-Object { if($_.Name -like 'github.com*'){0}else{1} }, Name
    foreach($p in $ordered){
      if($p.Value -and $p.Value.user){return [string]$p.Value.user}
    }
  }catch{}
  # regex fallback: first "user":"..." (never matches the oauth_token key)
  try{
    $m=[regex]::Match((Get-Content $file -Raw),'"user"\s*:\s*"([^"]*)"')
    if($m.Success){return $m.Groups[1].Value}
  }catch{}
  return ''
}

# Newest-Utc PATHS -> the newest LastWriteTimeUtc among the paths as ISO-8601, or ''.
function Newest-Utc([string[]]$paths){
  $newest=$null
  foreach($p in $paths){
    if(-not $p -or -not (Test-Path $p)){continue}
    # -Force so dot-prefixed dirs (e.g. .copilot / .vscode) resolve on Unix too,
    # where a leading dot marks the item hidden and Get-Item would otherwise skip it.
    $it=Get-Item $p -Force -ErrorAction SilentlyContinue
    if(-not $it){continue}
    $t=$it.LastWriteTimeUtc
    if(-not $newest -or $t -gt $newest){$newest=$t}
  }
  if($newest){return $newest.ToString('yyyy-MM-ddTHH:mm:ssZ')}
  return ''
}

# Get-NewerVersion A B -> the version-sorted-higher of the two (either may be '').
function Get-NewerVersion([string]$a,[string]$b){
  if(-not $a){return $b}
  if(-not $b){return $a}
  try{ if([version]($b -replace '[^0-9.].*$','') -gt [version]($a -replace '[^0-9.].*$','')){return $b} }
  catch{ if($b -gt $a){return $b} }
  return $a
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. EMIT — build one profile object; main loop collects + prints
# ─────────────────────────────────────────────────────────────────────────────

# Collect-CopilotProfile USER PROFILE -> a profile object, or $null if the profile
# has no Copilot footprint (neither an auth store nor an editor install).
function Collect-CopilotProfile([string]$u,[string]$profile){
  $login='';$cred=$false;$credMtime='';$credSource='';$version=''
  $editors=New-Object System.Collections.Generic.List[string]
  $touch=New-Object System.Collections.Generic.List[string]

  # --- auth store (identity + credential presence) ---------------------------
  $auth=Find-CopilotAuth $profile
  if($auth){
    $login=Get-GhLogin $auth
    if(Select-String -Path $auth -Pattern 'oauth_token' -Quiet){$cred=$true}
    $credMtime=(Get-Item $auth).LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
    $credSource=Split-Path $auth -Leaf
    [void]$touch.Add($auth)
  }

  # --- VS Code family presence + version --------------------------------------
  # Both github.copilot and github.copilot-chat count as Copilot; the extensions
  # dir can lag a reload/uninstall, so the VS Code globalStorage dir is also a
  # presence signal. Prefer the main extension version (1.x), else chat (0.x).
  $hasVscode=$false; $mainVer=''; $chatVer=''
  foreach($root in Get-VscExtRoots $profile){
    foreach($d in (Get-ChildItem $root -Directory -Filter 'github.copilot-*' 2>$null)){
      if($d.Name -match '^github\.copilot-chat-\d'){
        $hasVscode=$true; [void]$touch.Add($d.FullName)
        $chatVer=Get-NewerVersion $chatVer ($d.Name -replace '^github\.copilot-chat-','')
      } elseif($d.Name -match '^github\.copilot-\d'){
        $hasVscode=$true; [void]$touch.Add($d.FullName)
        $mainVer=Get-NewerVersion $mainVer ($d.Name -replace '^github\.copilot-','')
      }
    }
  }
  # globalStorage + cached VSIX under each VS Code data dir (Code + Insiders).
  foreach($data in @((Join-Path $profile 'AppData\Roaming\Code'),
                     (Join-Path $profile 'AppData\Roaming\Code - Insiders'))){
    foreach($gsName in 'github.copilot','github.copilot-chat'){
      $gs=Join-Path $data ('User\globalStorage\{0}' -f $gsName)
      if(Test-Path $gs){$hasVscode=$true; [void]$touch.Add($gs)}
    }
    $vsix=Join-Path $data 'CachedExtensionVSIXs'
    if(Test-Path $vsix){
      foreach($f in (Get-ChildItem $vsix -Filter 'github.copilot-*' 2>$null)){
        if($f.Name -match '^github\.copilot-chat-\d'){$chatVer=Get-NewerVersion $chatVer ($f.Name -replace '^github\.copilot-chat-','')}
        elseif($f.Name -match '^github\.copilot-\d'){$mainVer=Get-NewerVersion $mainVer ($f.Name -replace '^github\.copilot-','')}
      }
    }
  }
  if($mainVer){$version=$mainVer}else{$version=$chatVer}
  if($hasVscode){[void]$editors.Add('vscode')}

  # --- JetBrains plugin presence (per IDE product) ---------------------------
  $jbRoot=Join-Path $profile 'AppData\Roaming\JetBrains'
  if(Test-Path $jbRoot){
    foreach($plugin in (Get-ChildItem $jbRoot -Directory 2>$null | ForEach-Object {
              Join-Path $_.FullName 'plugins\github-copilot-intellij' })){
      if(-not (Test-Path $plugin)){continue}
      [void]$touch.Add($plugin)
      $product=Split-Path (Split-Path (Split-Path $plugin -Parent) -Parent) -Leaf
      [void]$editors.Add("jetbrains:$product")
    }
  }

  # --- Standalone Copilot CLI  ~\.copilot ------------------------------------
  # The `copilot` CLI (also the engine under the desktop app) stores state here.
  # config.json is JSONC (first-launch timestamp only) and identity is in the OS
  # credential store, so this is presence + version only. Version = newest
  # "data.db.pre-update-backup-<ver>-<epoch>" backup file.
  $cliVer=''
  $cli=Join-Path $profile '.copilot'
  if((Test-Path (Join-Path $cli 'config.json')) -or (Test-Path (Join-Path $cli 'data.db'))){
    [void]$editors.Add('copilot-cli'); [void]$touch.Add($cli)
    foreach($f in (Get-ChildItem $cli -Filter '*pre-update-backup-*' 2>$null)){
      $m=[regex]::Match($f.Name,'pre-update-backup-([0-9]+\.[0-9]+\.[0-9]+)')
      if($m.Success){$cliVer=Get-NewerVersion $cliVer $m.Groups[1].Value}
    }
  }

  # --- Standalone Copilot desktop app ("GitHub Copilot") ---------------------
  # GA 2026. Confirmed Windows layout: install at %LOCALAPPDATA%\Programs\GitHub
  # Copilot; per-user state under %APPDATA%\com.github.githubapp (app-skills,
  # .window-state.json) with a WebView cache at %LOCALAPPDATA%\com.github.githubapp.
  # Identity is in the OS credential store -> github_login stays empty. Version from
  # the %LOCALAPPDATA%\copilot-desktop-gh-<ver> dir.
  $deskVer=''; $hasDesktop=$false
  foreach($dbase in @((Join-Path $profile 'AppData\Roaming\com.github.githubapp'),
                      (Join-Path $profile 'AppData\Local\com.github.githubapp'))){
    if(Test-Path $dbase){$hasDesktop=$true; [void]$editors.Add('copilot-desktop'); [void]$touch.Add($dbase); break}
  }
  if($hasDesktop){
    $cacheRoot=Join-Path $profile 'AppData\Local'
    foreach($c in (Get-ChildItem $cacheRoot -Directory -Filter 'copilot-desktop-gh-*' 2>$null)){
      $deskVer=Get-NewerVersion $deskVer ($c.Name -replace '^copilot-desktop-gh-','')
    }
  }

  # Version fallback: VS Code (set above) wins; else the CLI, else the desktop app.
  if(-not $version){$version=$cliVer}
  if(-not $version){$version=$deskVer}

  if(-not $auth -and $editors.Count -eq 0){return $null}   # no Copilot footprint

  $lastUsed=Newest-Utc @($touch)
  $editorsUnique=@($editors | Select-Object -Unique)

  # Field order here is the output contract — keep it stable.
  return [pscustomobject]@{
    product='github_copilot'; host=$host_name; os_user=$u
    github_login=$login; email=''; plan='unknown'; auth_method='github_oauth'
    client_version=$version; editors=$editorsUnique; model=''
    last_used=$lastUsed
    credentials_on_disk=$cred; credentials_mtime=$credMtime; credentials_source=$credSource
    source='config'
  }
}

# --- main --------------------------------------------------------------------
foreach($profileDir in Get-Profiles){
  $u=$profileDir.Name; $profile=$profileDir.FullName
  if(-not $seen.Add($profile.ToLower())){continue}
  $obj=Collect-CopilotProfile $u $profile
  if($obj){$results += $obj}
}

Emit-Results 'github_copilot' 'not_installed'
