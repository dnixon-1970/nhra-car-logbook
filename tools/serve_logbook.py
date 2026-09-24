"""Local logbook site: Concrete Device ID, car list, one car's timeslips.

Run from the repo root:

    python3 tools/serve_logbook.py

Then open http://127.0.0.1:8787
"""

from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.logbook_data import fetch_races, load_cache, save_cache
from tools.logbook_render import render_home, render_logbook, render_picker

CSS_PATH = ROOT / "logbook" / "logbook.css"
HOST = "127.0.0.1"
PORT = 8787


def history_for(user_id: str) -> tuple[list, list]:
    """Use the local cache, otherwise query production telemetry and store it."""
    cached = load_cache(user_id)
    if cached is not None:
        return cached
    races, milestones = fetch_races(user_id)
    save_cache(user_id, races, milestones)
    return races, milestones


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        user_id = (params.get("user_id") or [""])[0].strip()
        car = (params.get("car") or [""])[0]
        try:
            if parsed.path == "/logbook.css":
                self._send(CSS_PATH.read_text(encoding="utf-8"), "text/css; charset=utf-8")
                return
            if parsed.path in {"/", ""}:
                self._send(render_home())
                return
            if parsed.path == "/cars":
                if not user_id:
                    self._send(render_home("Enter a Concrete Device ID."))
                    return
                self._send(render_picker(user_id, history_for(user_id)[0]))
                return
            if parsed.path == "/logbook":
                if not user_id or not car:
                    self._send(render_home("User id and car are both required."))
                    return
                races, milestones = history_for(user_id)
                self._send(render_logbook(user_id, car, races, milestones))
                return
            self._send(render_home("That page is not in the book."), status=404)
        except Exception as exc:  # noqa: BLE001 — show the failure on the page
            self._send(render_home(str(exc)), status=500)

    def _send(self, body: str, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Logbook at http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
