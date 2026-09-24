# Read Slack

This project uses the same bot token as Slack Integration Test. It does not store a second copy.

## Token resolution

`tools/slack_read.py` checks, in order:

1. `SLACK_BOT_TOKEN`
2. This repo's gitignored `.local-config.json` (`slack.bot_token`)
3. `~/Cursor Projects/Slack Integratation Test/.local-config.json`

## Check that it works

Use that project's virtualenv, which already has `slack_sdk`:

```bash
"/Users/davidnixon/Cursor Projects/Slack Integratation Test/.venv/bin/python" tools/slack_read.py auth
"/Users/davidnixon/Cursor Projects/Slack Integratation Test/.venv/bin/python" tools/slack_read.py channels
```

`auth` should print the workspace name and bot user. It must not print the token.

## What is allowed

`auth.test`, `conversations.list`, `conversations.history`. No `chat.postMessage`, no edits, no deletes.

Cursor's Slack plugin in the editor is a separate login. The bot-token client above is the one this repo owns.
