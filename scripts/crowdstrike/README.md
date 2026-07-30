# Falcon-rtr scripts (Cursor + Claude Code + Codex + GitHub Copilot)

Endpoint inventory scripts for discovering Cursor, Claude Code, OpenAI Codex, and GitHub
Copilot installs
across a fleet — account identity, plan/subscription, last-used, and security-relevant
metadata — designed to run via **CrowdStrike Falcon RTR** and feed a single deduplicated roster.

## What this is for

- **Shadow-IT discovery**: personal / free / pro accounts that aren't in your managed tenants.
- **License reconciliation**: cross-check endpoint reality against the Cursor Admin API,
  the Anthropic Console / Admin API, the OpenAI/ChatGPT admin surface, and the GitHub
  Copilot billing API, which are the *authoritative* source for Team/Enterprise/Business
  seats and billing. These scripts find what those APIs can't see.

## Layout

```
rtr_scripts/                  # bundled with the crowdstrike provider (providers/crowdstrike/)
├── bash/                     # macOS + Linux endpoints
│   ├── cursor_inventory.sh
│   ├── claude_inventory.sh
│   ├── codex_inventory.sh
│   └── github_copilot_inventory.sh
├── powershell/               # Windows endpoints
│   ├── cursor_inventory.ps1
│   ├── claude_inventory.ps1
│   ├── codex_inventory.ps1
│   └── github_copilot_inventory.ps1
└── README.md
```

The provider uploads these to Falcon RTR automatically on every inventory run
(`CROWDSTRIKE_MANAGE_RTR_SCRIPTS`, default on), so manual upload is not required.

## Running via Falcon RTR

These run as **root** (macOS/Linux) or **SYSTEM** (Windows), not as the logged-in user,
so every script enumerates *all* user profiles on the box rather than one `$HOME`.

- **bash**: `put` the `.sh`, then `runscript -Raw=...` or `run`. Cursor's `state.vscdb`
  is read with the `sqlite3` CLI if present (macOS ships it at `/usr/bin/sqlite3`), else
  with `python3`'s stdlib `sqlite3` module — no external binary required. The `source`
  field reports which (`sqlite3` / `python-sqlite3`); only if *both* are absent does it
  emit `error: no_sqlite_reader`.
- **powershell**: `runscript -CloudFile=...`. Cursor's `state.vscdb` is read through a
  reader cascade (most reliable first): the in-box **`winsqlite3.dll`** (present in
  System32 on Windows 10/11 and Server 2016+ — a real SQLite engine, zero install) → a
  `sqlite3.exe` on PATH or `put` into the RTR session dir → `python3`'s stdlib `sqlite3`
  → a last-resort regex scrape. The `source` field reports which was used
  (`winsqlite3` / `sqlite3` / `python-sqlite3` / `binary-scrape`). On modern Windows you
  no longer need to `put` a `sqlite3.exe`; a `binary-scrape` result should now be rare and
  is the signal to investigate the host (e.g. pre-2016 Windows with no Python).
- **Claude bash** uses `python3` for nested fields (projects, MCP servers) and falls back
  to a reduced grep mode (flagged `python3_absent_limited_fields`) when it's missing —
  notably on stock macOS.
- **Codex** reads `~/.codex` (`CODEX_HOME`): `auth.json` for auth mode + token presence,
  `config.toml` for MCP servers / trusted project paths / model, and the `sessions/`
  rollout files for last-used. Unlike Cursor/Claude, Codex stores email + plan **only**
  inside the `id_token` JWT, so both collectors decode that token's identity claims
  (email, `chatgpt_plan_type`, org, account, `exp`) — the raw token is never emitted, and
  the access/refresh tokens + `OPENAI_API_KEY` are presence-only. bash uses `python3`
  (grep/base64 fallback flagged `python3_absent_limited_fields`); PowerShell uses
  `ConvertFrom-Json` + `[Convert]::FromBase64String`.
- **GitHub Copilot** is an IDE *extension*, not a standalone app, so it has no single
  account store. The scripts combine the shared OAuth store
  (`~/.config/github-copilot/apps.json`, Windows `%LOCALAPPDATA%\github-copilot\apps.json`)
  for the `github_login`, with editor-install detection for presence, `client_version`, and
  the `editors` list:
  - **VS Code family** — both the `github.copilot` and `github.copilot-chat` extensions
    count. Detection looks in the extension dirs (`~/.vscode/extensions`, `-server`,
    `-insiders`) **and** the VS Code data dir's `User/globalStorage/github.copilot*`
    (macOS `~/Library/Application Support/Code`, Linux `~/.config/Code`, `+ Code - Insiders`).
    globalStorage matters because the extension dir can lag a reload or be empty after an
    uninstall while the extension is still present/used. `client_version` prefers the main
    extension version, falling back to the chat version or the cached-VSIX version.
  - **JetBrains** — the `github-copilot-intellij` plugin dir under each IDE profile.

  `apps.json` is reliably present for JetBrains/Neovim/CLI users but often absent for VS Code
  users (whose token lives in the OS keychain), so `github_login` can be empty while
  `editors` still shows the install. Seat/plan is **not on disk** (GitHub billing API only)
  → `plan` is always `unknown`.

All scripts emit **JSON-lines**: one object per profile found. Collect the RTR output
into files (one per host or all concatenated) and run the aggregator.


## Output schema

Every script emits **JSON-lines**: one JSON object per user profile found (they run as
root/SYSTEM and enumerate all profiles). The three products share a common core; each
adds its own product-specific fields on top.

### Common core (all products, both bash + PowerShell)

Present in every *full* profile record regardless of product:

| Field | Type | Meaning |
|---|---|---|
| `product` | string | `cursor` / `claude` / `codex` / `github_copilot` |
| `host` | string | hostname |
| `os_user` | string | profile owner the record was found under |
| `email` | string | account identity |
| `plan` | string | subscription / plan tier (`unknown` if undetermined) |
| `auth_method` | string | how the account authenticated |
| `model` | string | configured / most-used model |
| `last_used` | string | ISO-8601; newest session activity, falling back to a file mtime |
| `mcp_servers` | array of objects | Claude/Cursor: `{name, transport, command_present?, arg_count?, url_host?}` per server (structural shape only — never command/args/url values). Codex: unchanged array of name strings. |
| `mcp_count` | number | length of `mcp_servers` |
| `auth_metadata` | object | Claude/Cursor only. `{"mcp_servers":[{name, env_var_names?, header_key_names?, filesystem_scope_paths?}]}` — per-MCP-server auth-surface indicators, names/indicators only, never secret values. Absent if no MCP server has any of these configured, or in reduced/fallback modes. |
| `source` | string | how the record was derived (per-product values, e.g. `config`, `auth+config`, `sqlite3`, `*-grep`) |

Type conventions hold everywhere: strings are escaped and CR/LF-stripped, counts are JSON
numbers, presence flags are JSON `true`/`false`. **No secret values are ever emitted** —
only presence, expiry, and on-disk mtimes.

### Guaranteed on every line

Only `product` + `host` appear on *every* object, because the terminal "nothing found"
and error lines are smaller:

- `{product, host, status:"not_installed…"}` — no profile / not installed
- `{product, host, error:"unsupported_os", os}` — plus cursor-only `error:"no_sqlite_reader"`

Reduced **grep-fallback** records (claude/codex on python-less hosts — `source` ends in
`-grep`, and they carry `note:"python3_absent_limited_fields"`) guarantee only
`product, host, os_user, email, plan, source`; `model` / `auth_method` / `mcp_servers`
may be absent.

### Product-specific fields (shared by 2 of 3)

| Field group | cursor | claude | codex |
|---|:--:|:--:|:--:|
| `user_id` | bash only¹ | ✓ | ✓ |
| `org` / `org_id` / `account_uuid` | — | ✓ | ✓² |
| `projects_count` / `project_paths` / `projects_truncated` | — (`workspace_count` instead) | ✓ | ✓ |
| `credentials_on_disk` / `credentials_mtime` | — | ✓ | ✓ |
| `access_token_present` / `_exp` / `_expired`, `refresh_token_present` | ✓ | — | ✓ |
| `app_version` | ✓ | — (`client_version`) | ✓ |
| device IDs (`machine_id`, `dev_device_id`, `service_machine_id`, `sqm_id`) | ✓ | — | — |
| `id_token_*`, `api_key_present`, `last_refresh`, `install_id` | — | — | ✓ |

¹ cursor's PowerShell collector omits `user_id` (a bash/PS divergence).
² codex always emits `org` as an empty string — its identity lives in the id_token JWT,
which carries no org *name*.


## Fields of note

| Field | Why it matters |
|---|---|
| `plan` / `subscriptionType` | License compliance. Claude often shows `unknown` locally — confirm via Admin API. |
| `last_used` | Dormant installs / offboarding. |
| `auth_method`, email domain | Personal vs SSO accounts = data-egress risk. |
| `mcp_servers`, `mcp_count`  | External integrations the agent can reach. Enriched detail (`transport`, `auth_metadata`) comes from both user-global and project-scoped configs: Claude reads `~/.claude.json` (user + local scope) plus each `<projectRoot>/.mcp.json` (project scope); Cursor reads global `~/.cursor/mcp.json` plus `<folder>/.cursor/mcp.json` for every folder in its `workspaceStorage`. Project roots are a bounded set of known paths (never a filesystem crawl). Codex remains name-only. |
| `project_paths` (Claude) | Which repos/dirs the agent has operated in. |
| `github_login`, `editors` (Copilot) | Which GitHub account, and which IDEs have Copilot on the host. |
| `*_token_present`, `credentials_on_disk`, `*_exp` | Credential hygiene; expiry/staleness. |
| telemetry IDs (Cursor) | Device correlation. |

## Security stance on secrets

The scripts **do not read or emit token/credential values**. They report presence,
on-disk age (`credentials_mtime`), and — for Cursor's JWT access token — the decoded
`exp` (expiry). Centralizing live credentials into RTR output/SIEM would create more
exposure than it resolves; if you decide you need values, treat it as a deliberate,
separately-approved change.

## Verify before fleeting

Field names drift across releases. On one real install of each *deployed* version,
confirm: the Cursor `state.vscdb` keys, the Claude `~/.claude.json` field names
(`oauthAccount.*`, `numStartups`, `installMethod`), the `CLAUDE_CONFIG_DIR` variable
name, and the exact `claude auth status` JSON shape. For Codex, confirm the `auth.json`
shape (`auth_mode`, `tokens.id_token`), the `id_token` claim names (`email`, and the
`https://api.openai.com/auth` claim's `chatgpt_plan_type` / `organization_id` /
`chatgpt_account_id`), and the `config.toml` section names (`[mcp_servers.*]`,
`[projects."..."]`). The scripts fail soft (empty fields) rather than erroring on a
renamed key — so a silent column of blanks is the signal to re-check names. Run one
canary host, eyeball the JSON, then widen.
