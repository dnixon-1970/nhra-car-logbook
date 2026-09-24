# Project setup — per-car web logbook

- **Date**: 2026-09-24
- **Status**: In implementation — local prototype seeded
- **Ticket(s)**: none yet
- **Branch**: none (workspace is not a git repo)
- **Author / Reviewer**: Cursor Grok / Claude Fable then Claude Opus 4.7
- **Depends on / Sibling to**: Project Startup Best Practices; NHRA Marketing brand pack; Slack Integration Test bot token; `unity-nhra` analytics events
- **Motivation**: Steering and design threads describe a per-car logbook. Telemetry already has race results. This folder is the proof that a Concrete Device ID can become a themed HTML book for one car.
- **Decision**: Local site only. Production BigQuery, read-only. Brand from NHRA Marketing. Slack reads borrow the existing bot token and do not post.

## 0. Onboarding

1. `AGENTS.md`
2. This plan
3. `Knowledge Packs/brand-guidelines.md`
4. `Knowledge Packs/race-telemetry.md`
5. `Documents/runbooks/local-logbook.md`

Hard freeze: no Slack writes, no Unity edits, no public deploy, no invented NHRA history.

## 1. Scope

**In scope:** operating files, read-only Slack check, GUID join, Saira / trackside HTML, local server, unit tests.

**Out of scope:** game button, auth-uid lookup, dev Firebase, hosting, Jira, git remote.

## 2. What the page does

Today there is no logbook page. After this prototype: a person pastes a Concrete Device ID, sees that device's cars, and opens one car's timeslip (RT, 60, 330, ET, mph, result).

## 3. Surfaces

- `tools/slack_read.py` — read-only, sibling token
- `tools/logbook_data.py` — query, join, cache
- `tools/logbook_render.py` + `logbook/logbook.css` — theme
- `tools/serve_logbook.py` — `127.0.0.1:8787`

## 4. Cross-cutting

Marketing and Unity stay read-only. Query cost cap is $2 per dry-run. Cache lives in gitignored `data/`.

## 5. Rollout

No deploy. Run the server locally.

## 6. Rollback

Delete this workspace's files. External repos were not modified.

## 7. Open

1. Which production device id should be the demo?
2. Git repo, and under which ticket?
3. Later: in-game "view logbook" link, still out of this seed.
