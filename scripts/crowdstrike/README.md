# Falcon-rtr scripts (Cursor + Claude Code)

Endpoint inventory scripts for discovering Cursor and Claude Code installs across a
fleet — account identity, plan/subscription, last-used, and security-relevant metadata —
designed to run via **CrowdStrike Falcon RTR** and feed a single deduplicated roster.

## What this is for

- **Shadow-IT discovery**: personal / free / pro accounts that aren't in your managed tenants.
- **License reconciliation**: cross-check endpoint reality against the Cursor Admin API
  and the Anthropic Console / Admin API, which are the *authoritative* source for
  Team/Enterprise seats and billing. These scripts find what those APIs can't see.

## Layout

```
rtr_scripts/                  # bundled with the crowdstrike provider (providers/crowdstrike/)
├── bash/                     # macOS + Linux endpoints
│   ├── cursor_inventory.sh
│   └── claude_inventory.sh
├── powershell/               # Windows endpoints
│   ├── cursor_inventory.ps1
│   └── claude_inventory.ps1
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

All scripts emit **JSON-lines**: one object per profile found. Collect the RTR output
into files (one per host or all concatenated) and run the aggregator.


## Fields of note

| Field | Why it matters |
|---|---|
| `plan` / `subscriptionType` | License compliance. Claude often shows `unknown` locally — confirm via Admin API. |
| `last_used` | Dormant installs / offboarding. |
| `auth_method`, email domain | Personal vs SSO accounts = data-egress risk. |
| `mcp_servers`, `mcp_count`  | External integrations the agent can reach. |
| `project_paths` (Claude) | Which repos/dirs the agent has operated in. |
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
name, and the exact `claude auth status` JSON shape. The scripts fail soft (empty
fields) rather than erroring on a renamed key — so a silent column of blanks is the
signal to re-check names. Run one canary host, eyeball the JSON, then widen.
