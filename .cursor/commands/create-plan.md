# /create-plan — thin wrapper; canonical recipe lives in ai-env

<!-- Do NOT paste the recipe here. This file must stay a pointer so the
     canonical version in ai-env remains the single source of truth.
     Pattern: Project Startup Best Practices / patterns/shared-slash-commands.md -->

Resolve the canonical checkout, first match wins:

1. `$AI_ENV_ROOT` (env-var override)
2. `~/git/services/ai-env` (documented default clone path)
3. `../ai-env` (sibling of this repo)

If none of these exists, STOP and tell the user:
"Canonical commands repo not found — clone ConcreteSoftware/ai-env (or set AI_ENV_ROOT),
then re-run /create-plan."

Otherwise: read `<checkout>/.cursor/commands/create-plan.md` and follow it
exactly as if its contents were this file's contents, applying any arguments the
user provided after the slash command.

Registered-workflow projects only (SERV, APPAI). Do **not** run this against `NHRA-*`.
Use `/prep-game-task` first if the work still lives on a game ticket.
