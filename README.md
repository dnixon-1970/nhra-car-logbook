# Car Logbook Prototype

Proof of concept for a per-car **NHRA Legends** web logbook.

A player opens a page with their Concrete Device ID. The page reads production race telemetry, lists the cars they have run, and renders a timeslip book for the car they pick.

## Start here

1. `AGENTS.md`
2. `Documents/todo.md`
3. `Documents/plans/20260924_project-setup.plan.md`
4. `Knowledge Packs/brand-guidelines.md`
5. `Documents/runbooks/local-logbook.md`

## Run the site

```bash
python3 tools/serve_logbook.py
# http://127.0.0.1:8787
```

The id on the form is the Analytics `user_id` (Concrete Device ID), not a Firebase Auth uid.

## Share a snapshot

GitHub Pages cannot query BigQuery. `tools/export_pages.py` writes the cached garage into `docs/` as plain HTML. That folder is what Pages serves.

Add `?vehicle=` with the car id to open that book instead of the garage: `?vehicle=Vehicle_Muldowney1977`. `?car=` does the same. The car file also works on its own: `Vehicle_Muldowney1977.html`. Each car book links to one driver page for the whole device: `driver.html`.

## Slack reads

Same credential store as Slack Integration Test. This repo does not copy the bot token.

```bash
"/Users/davidnixon/Cursor Projects/Slack Integratation Test/.venv/bin/python" tools/slack_read.py auth
```

See `Documents/runbooks/slack-read.md`.
