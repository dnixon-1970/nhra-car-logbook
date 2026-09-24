# /prep-game-task — thin wrapper; canonical recipe lives in ai-env

<!-- Do NOT paste the recipe here. This file must stay a pointer so the
     canonical version in ai-env remains the single source of truth.
     Pattern: Project Startup Best Practices / patterns/shared-slash-commands.md -->

Resolve the canonical checkout, first match wins:

1. `$AI_ENV_ROOT` (env-var override)
2. `~/git/services/ai-env` (documented default clone path)
3. `../ai-env` (sibling of this repo)

If none of these exists, STOP and tell the user:
"Canonical commands repo not found — clone ConcreteSoftware/ai-env (or set AI_ENV_ROOT),
then re-run /prep-game-task."

Otherwise: read `<checkout>/.cursor/commands/prep-game-task.md` and follow it
exactly as if its contents were this file's contents, applying any arguments the
user provided after the slash command.

Typical use here: if the logbook later needs a Unity or content-repo change,
route the game ticket through `/prep-game-task` rather than `/create-plan` on `NHRA-*`.
A public website deploy is a later human-gated session, not this prototype.
