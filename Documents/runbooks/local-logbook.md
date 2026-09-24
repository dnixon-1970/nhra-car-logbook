# Run the logbook locally

From the repo root:

```bash
python3 tools/serve_logbook.py
```

Open http://127.0.0.1:8787

1. Paste a Concrete Device ID (Analytics `user_id`).
2. The server queries `nhra-64ac5.analytics_490826646` for the last 60 days, joins start and complete on `GUID`, and caches JSON under `data/` (gitignored).
3. Pick a car. The timeslip page is that car only.

A second visit for the same id uses the cache. Delete `data/<id>.json` to force a new query.

Queries dry-run first and refuse an estimate over $2.

BigQuery uses Application Default Credentials (`gcloud auth application-default login`). `google-cloud-bigquery` must be importable. Unit tests do not need it:

```bash
python3 -m unittest tests/test_logbook.py
```

There is no production deploy. This process binds to `127.0.0.1` only. Port 8787 avoids the other local Python server already bound to 8765.
