# AGENTS.md — Car Logbook Prototype

Operating workspace for a proof-of-concept **per-car web logbook** for NHRA Legends of Drag Racing. Authoritative setup plan: [`Documents/plans/20260924_project-setup.plan.md`](Documents/plans/20260924_project-setup.plan.md).

Org-wide Concrete rules in `~/git/services/ai-env/.cursor/rules/*.mdc` are the assumed baseline. This file adds project-specific rules only.

**Default cross-model reviewers:** Claude Fable (authoring review) and Claude Opus 4.7 (adversarial / second pass). Primary author family: Cursor Grok.

No Jira epic is attached yet. Do not invent a ticket ID. Game work stays `NHRA-*`.

## Project context

This repo ships:

- **Local logbook site** (`tools/serve_logbook.py`, `logbook/`) — enter a Concrete Device ID, pick a car, read a themed timeslip page
- **Telemetry shaping** (`tools/logbook_data.py`) — join `Play_Mode_Race_Started` to `Play_Mode_Race_Complete` on `GUID`
- **Read-only Slack** (`tools/slack_read.py`) — bot token from the Slack Integration Test local config
- **Operating contract** (`AGENTS.md`, `.cursor/rules/`)
- **Grounding** (`Knowledge Packs/`, `References/`)

**Boundary:** Campaign creative lives in `~/Cursor Projects/NHRA Marketing/`. The Slack/Jira/GitHub toolkit lives in `~/Cursor Projects/Slack Integratation Test/`. Unity and BigQuery exports stay read-only. This folder produces the **logbook prototype**, not a production website deploy and not a Unity feature.

## Repository structure

| Path | Purpose | Lifecycle |
|---|---|---|
| `README.md` | Human overview | Update when structure changes |
| `AGENTS.md` | This manual | Update when rules change |
| `.cursor/rules/` | Always-applied session rules | Mirror of numbered rules below |
| `.cursor/commands/` | Thin wrappers to `ai-env` recipes | Pointers only |
| `tools/` | Slack reads, telemetry join, local server | Edit here |
| `logbook/` | Theme CSS | Edit here |
| `Documents/` | Plans, decisions, insights, runbooks, todo | Audit trail |
| `Knowledge Packs/` | Brand + telemetry facts | Cite; do not invent past them |
| `References/` | External source catalog | Catalog in `References/CATALOG.md` |
| `data/` | Gitignored query cache | Regenerated |
| `Experiments/` | Local scratch (gitignored) | Per-developer scratch only |

## Development rules

### Rule 1 — Never modify external repos without asking

LLMs must never create, edit, rename, move, or delete any file outside this repo without explicitly asking the user first.

| Local path | Repo / role |
|---|---|
| `~/Cursor Projects/Project Startup Best Practices/` | Operating patterns this repo was seeded from |
| `~/Cursor Projects/NHRA Marketing/` | Brand, guardrails, license — **required reads** |
| `~/Cursor Projects/Slack Integratation Test/` | Slack bot token + read client pattern. Read its `.local-config.json`; do not edit it |
| `~/git/services/ai-env/` | Org-wide rules + slash-command recipes |
| `~/git/unity/apps/nhra/` | Race analytics event contract (read-only) |
| `~/git/unity/tools/unity-nhra-ai-assisted-balancing/` | BigQuery telemetry tool (read-only) |

Do not edit `~/bin/sync-external-repos.sh` from this workspace. Adding clones there is a human edit.

### Rule 2 — Be explicit about substantive changes

When proposing a change to AGENTS.md, the active plan, the telemetry join, or the public page contract: state full paths, current vs proposed, impact, then wait — unless the change is already in the approved plan.

### Rule 3 — Keep `Documents/todo.md` updated

Forward-looking design lives in `Documents/plans/`. The todo is the near-term tracker.

### Rule 4 — Scratch stays local; durable work lands in Documents and tools

`Experiments/` and `data/` are gitignored. Sub-agent analysis meant to persist saves to `Documents/`.

### Rule 5 — Always use Python for math

ET, RT, 60-ft, and mph conversions go through `tools/logbook_data.py`. Do not do that arithmetic in prose.

### Rule 6 — Git safety

Never `git clean`, `git checkout --orphan`, or `git reset --hard` past untracked work in the main worktree. See `.cursor/rules/git-safety.mdc`.

### Rule 7 — Prototype-then-promote

| Surface | Why it's shared/critical | Evidence required |
|---|---|---|
| `AGENTS.md` + `.cursor/rules/` | Read at every agent run | Cross-model review of the delta |
| Active plan | Drives the prototype | Plan review + fix ledger |
| `tools/logbook_data.py` join | Wrong car or ET if GUID join drifts | Unit tests + one live user render |
| `logbook/` theme | Brand surface | Guardrails + a browser pass |
| Slack writes | Not this repo | Do not add them |

### Rule 8 — Cross-model review

Primary author: Cursor Grok. Reviewers: Claude Fable, then Claude Opus 4.7. Save reviews to `Documents/plans/<date>_<topic>_review.md`.

### Rule 9 — Never invent NHRA facts

Car, event, and opponent strings come from telemetry. Do not invent drivers, sponsors, liveries, or records. Brand rules in `Knowledge Packs/brand-guidelines.md` win over decoration. License constraints in NHRA Marketing win over brand preference.

### Rule 10 — Slack access is read-only

Use `tools/slack_read.py` and the bot token already stored for Slack Integration Test. Do not copy the token into git. Do not post, edit, or delete Slack messages from this repo.

### Rule 11 — Identity

The logbook key is the Concrete Device ID, which NHRA writes to Firebase Analytics `user_id`. A Firebase Auth uid will not match production telemetry. Production dataset is `nhra-64ac5.analytics_490826646`. Dev builds do not export there.

## Onboarding flow for a new agent

1. `README.md`
2. `AGENTS.md`
3. `Documents/directory.md`
4. `Documents/todo.md`
5. `Documents/plans/20260924_project-setup.plan.md`
6. `Knowledge Packs/brand-guidelines.md`
7. `Knowledge Packs/race-telemetry.md`
8. `Documents/runbooks/local-logbook.md`
9. `Documents/runbooks/slack-read.md`

Then summarize: what the page does, which id it expects, and what is still a local prototype.
