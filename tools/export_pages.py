"""Write a static snapshot of one cached logbook for GitHub Pages.

GitHub Pages cannot run the local server or query BigQuery. The export
rewrites car links to HTML files under docs/.
"""

from __future__ import annotations

import re
import shutil
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.logbook_data import group_by_car, load_cache
from tools.logbook_render import render_logbook, render_picker

DOCS = ROOT / "docs"
CSS = ROOT / "logbook" / "logbook.css"


def to_static(page: str) -> str:
    """Point stylesheet and car links at files in the same folder."""
    page = page.replace('href="/logbook.css"', 'href="logbook.css"')
    page = page.replace('href="/"', 'href="index.html"')
    page = re.sub(r"/cars\?user_id=[^\"\s]+", "index.html", page)

    def _car_file(match: re.Match[str]) -> str:
        return f"{unescape(match.group(1))}.html"

    return re.sub(r"/logbook\?user_id=[^\"&\s]+(?:&|&amp;)car=([^\"\s]+)", _car_file, page)


_VEHICLE_REDIRECT = """<script>
(function () {
  var params = new URLSearchParams(location.search);
  var vehicle = params.get("vehicle") || params.get("car");
  if (!vehicle) return;
  var wanted = vehicle.replace(/\\.html$/i, "").toLowerCase();
  var links = document.querySelectorAll("a.car-card");
  for (var i = 0; i < links.length; i++) {
    var href = links[i].getAttribute("href") || "";
    var stem = href.split("/").pop().replace(/\\.html$/i, "").toLowerCase();
    if (stem === wanted) {
      location.replace(href);
      return;
    }
  }
})();
</script>
"""


def with_vehicle_redirect(page: str) -> str:
    """Open a car book when the garage URL includes ?vehicle= or ?car=."""
    if "</body>" in page:
        return page.replace("</body>", _VEHICLE_REDIRECT + "</body>", 1)
    return page + _VEHICLE_REDIRECT


def export_snapshot(user_id: str) -> Path:
    """Render the cached garage and one page per car into docs/."""
    cached = load_cache(user_id)
    if cached is None:
        raise SystemExit(f"No cache for {user_id}. Open that book locally before exporting.")
    races, milestones = cached
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    shutil.copyfile(CSS, DOCS / "logbook.css")
    garage = with_vehicle_redirect(to_static(render_picker(user_id, races)))
    (DOCS / "index.html").write_text(garage, encoding="utf-8")
    for car_id in group_by_car(races):
        page = render_logbook(user_id, car_id, races, milestones)
        (DOCS / f"{car_id}.html").write_text(to_static(page), encoding="utf-8")
    return DOCS


def main() -> None:
    user_id = sys.argv[1] if len(sys.argv) > 1 else "526d41cb-58f3-47a9-86e4-8a74d4084547"
    path = export_snapshot(user_id)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
