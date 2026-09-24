"""Read-only Slack Web API client.

Loads the bot token the same way Slack Integration Test does: `slack.bot_token`
in a gitignored `.local-config.json`. This project does not keep its own copy
of the token. Resolution order:

1. `SLACK_BOT_TOKEN`
2. this repo's `.local-config.json`
3. `~/Cursor Projects/Slack Integratation Test/.local-config.json`

Write methods are not implemented. Posting belongs in that toolkit, not here.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ModuleNotFoundError:
    WebClient = None  # type: ignore[misc, assignment]
    SlackApiError = Exception  # type: ignore[misc, assignment]

SIBLING_CONFIG = (
    Path.home()
    / "Cursor Projects"
    / "Slack Integratation Test"
    / ".local-config.json"
)


def load_bot_token() -> str:
    """Return a bot token without printing it."""
    env_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if env_token:
        return env_token
    for path in (_local_config_path(), SIBLING_CONFIG):
        token = _token_from_file(path)
        if token:
            return token
    raise FileNotFoundError(
        "No Slack bot token. Set SLACK_BOT_TOKEN, or add slack.bot_token to "
        ".local-config.json, or keep the Slack Integration Test local config in place."
    )


def _local_config_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".local-config.json"


def _token_from_file(path: Path) -> str:
    if not path.is_file():
        return ""
    with path.open() as handle:
        payload = json.load(handle)
    token = payload.get("slack", {}).get("bot_token", "")
    if not token or token == "xoxb-your-token-here":
        return ""
    return str(token)


class SlackReadClient:
    """Paginated read wrapper. Never calls chat.postMessage."""

    def __init__(self, token: Optional[str] = None):
        if WebClient is None:
            raise ModuleNotFoundError(
                "slack_sdk is not installed. Use the Slack Integration Test "
                ".venv, or install requirements.txt in this project's .venv."
            )
        self.client = WebClient(token=token or load_bot_token())

    def auth_test(self) -> dict[str, Any]:
        """Confirm the token and return team/user identity. No token in the result."""
        response = self.client.auth_test()
        return {
            "ok": response.get("ok"),
            "team": response.get("team"),
            "user": response.get("user"),
            "bot_id": response.get("bot_id"),
        }

    def list_channels(self, limit: int = 100) -> list[dict[str, Any]]:
        """Public and private channels the bot can see."""
        channels: list[dict[str, Any]] = []
        cursor = None
        while True:
            response = self.client.conversations_list(
                limit=min(limit, 200),
                cursor=cursor,
                types="public_channel,private_channel",
                exclude_archived=True,
            )
            for channel in response.get("channels", []):
                channels.append(
                    {
                        "id": channel.get("id"),
                        "name": channel.get("name"),
                        "is_private": channel.get("is_private"),
                    }
                )
                if len(channels) >= limit:
                    return channels
            cursor = response.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                return channels

    def get_messages(self, channel_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Newest-first history for one channel."""
        response = self.client.conversations_history(channel=channel_id, limit=limit)
        messages = []
        for message in response.get("messages", []):
            messages.append(
                {
                    "ts": message.get("ts"),
                    "user": message.get("user"),
                    "text": message.get("text"),
                }
            )
        return messages


def main() -> None:
    """CLI: `auth` prints identity; `channels` lists names."""
    command = sys.argv[1] if len(sys.argv) > 1 else "auth"
    client = SlackReadClient()
    if command == "auth":
        print(json.dumps(client.auth_test(), indent=2))
        return
    if command == "channels":
        print(json.dumps(client.list_channels(limit=15), indent=2))
        return
    raise SystemExit(f"Unknown command {command!r}. Use auth or channels.")


if __name__ == "__main__":
    try:
        main()
    except SlackApiError as exc:
        raise SystemExit(f"Slack API error: {exc}") from exc
