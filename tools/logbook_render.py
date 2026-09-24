"""Render a car logbook as HTML using the NHRA Legends trackside palette.

Voice is crew-chief: short, mechanical, no banned marketing words.
Car ids are shown as telemetry recorded them. This page does not invent
drivers, sponsors, or liveries.
"""

from __future__ import annotations

import html
import json
from typing import Any, Optional
from urllib.parse import quote

from tools.logbook_data import (
    Milestone,
    RaceRow,
    calendar_fraction,
    chart_ticks,
    crew_chief_note,
    daily_trend,
    daily_win_rate,
    driver_record,
    is_vehicle_body_change,
    group_by_car,
    humanize_car_id,
    result_label,
    summarize_car,
    win_ratio,
)

# Dark field, then the bright livery color. Each pair is that car's paint, not the page default.
# Dark field, then the bright livery color. Pairs follow published photos and race reports.
CAR_THEMES = {
    "Vehicle_SoxMartin": ("#6e1520", "#1d4f9a"),
    "Vehicle_RonnieSox1968": ("#1a3f86", "#f4f7fb"),
    "Vehicle_RickDobbertin1986": ("#3d3408", "#ffe14a"),
    "Vehicle_BobRiggle1966": ("#14110c", "#d4a017"),
    "Vehicle_Muldowney1977": ("#4e1436", "#e23d8c"),
    "Vehicle_CaliforniaCharger": ("#0e3a78", "#f4f7fb"),
    "Vehicle_Pedregon2014": ("#2c1214", "#e10600"),
    "Vehicle_WarrenJohnson1992": ("#0c2148", "#f4f7fb"),
    "Vehicle_Snake": ("#3d3208", "#c8102e"),
    "Vehicle_SwindlerA": ("#0e2a55", "#e2c15a"),
    "Vehicle_WarrenJohnson1997": ("#121212", "#c5c8ce"),
    "Vehicle_WingedExpress": ("#5c181c", "#f4f1e6"),
    "Vehicle_AustinProck2025": ("#0e2748", "#7eb6ff"),
    "Vehicle_JimmyTaylor2025": ("#0e3048", "#4aa3d8"),
    "Vehicle_BobGlidden1972": ("#0c2348", "#f4f7fb"),
    "Vehicle_DallasGlenn2025": ("#2a1408", "#ff7a1a"),
    "Vehicle_PlanA": ("#0e2a4a", "#3d7ec8"),
    "Vehicle_DallasGlenn2026": ("#2a1408", "#ff7a1a"),
    "Vehicle_Reher": ("#5c1418", "#f6f1e4"),
}


def car_theme(car_id: str) -> tuple[str, str]:
    """Dark field and bright livery color. Nitro gold when this car has no recorded paint."""
    return CAR_THEMES.get(car_id, ("#2a1212", "#fcc83c"))


TREND_METRICS = (
    ("et", "ET", "total_time", 3, True),
    ("rt", "RT", "reaction_time", 3, True),
    ("sixty", "60-FT", "time_to_60", 3, True),
    ("three30", "330-FT", "time_to_330", 3, True),
    ("mph", "MPH", "top_speed_mph", 1, False),
    ("win", "WIN %", "win_rate", 0, False),
)

BANNED = (
    "epic",
    "ultimate",
    "insane",
    "unleash",
    "next-level",
    "game-changer",
    "buckle up",
    "experience the thrill",
)


def _fmt(value: Optional[float], digits: int = 3) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def _esc(value: object) -> str:
    return html.escape(str(value if value is not None else ""))


def render_picker(user_id: str, races: list[RaceRow], error: str = "") -> str:
    """Car list for one Concrete Device ID."""
    grouped = group_by_car(races)
    cards = []
    for car_id, car_races in grouped.items():
        summary = summarize_car(car_races)
        level = next((race.car_level for race in car_races if race.car_level is not None), None)
        level_text = f"LEVEL {level}" if level is not None else "LEVEL —"
        cards.append(
            f"""
            <a class="car-card" href="/logbook?user_id={_esc(user_id)}&car={_esc(car_id)}">
              <p class="eyebrow">{_esc(level_text)} · {_esc(summary['races'])} RUNS</p>
              <h2>{_esc(humanize_car_id(car_id))}</h2>
              <p class="meta">{_esc(summary['wins'])} WINS · {_esc(summary['losses'])} LOSSES · BEST ET {_esc(_fmt(summary['best_et']))}</p>
              <p class="id">{_esc(car_id)}</p>
            </a>
            """
        )
    body = "\n".join(cards) if cards else "<p class='empty'>No completed races in this window.</p>"
    error_html = f"<p class='error'>{_esc(error)}</p>" if error else ""
    return _page(
        title="Pick a car",
        body=f"""
        <header class="mast">
          <p class="brand">NHRA LEGENDS · CAR LOGBOOK</p>
          <h1>Garage</h1>
          <p class="lead">Concrete Device ID {_esc(user_id)}. Pick the car whose book you want open.</p>
        </header>
        {error_html}
        <section class="cards">{body}</section>
        <p class="back"><a href="/">Different id</a></p>
        """,
    )


def _title_name(car_id: str) -> str:
    """Nameplate without the Vehicle_ prefix or the raw content id."""
    name = humanize_car_id(car_id)
    if name.startswith("VEHICLE "):
        return name[len("VEHICLE ") :]
    return name


def _level_line(level: Optional[int], races: list[RaceRow]) -> str:
    """Level, race count, and win percentage for this car."""
    level_text = f"LEVEL {level}" if level is not None else "LEVEL —"
    race_text = "1 RACE" if len(races) == 1 else f"{len(races)} RACES"
    ratio = win_ratio(races)
    win_text = "—" if ratio is None else f"{round(ratio * 100)}%"
    return (
        f'<p class="eyebrow"><span>{_esc(level_text)}</span>'
        f'<span>{_esc(race_text)}</span><span>{_esc(win_text)} WINS</span></p>'
    )


def _car_picker(user_id: str, car_id: str, races: list[RaceRow]) -> str:
    """Title-sized menu of every car this device has raced."""
    grouped = group_by_car(races)
    if car_id not in grouped:
        grouped = {car_id: [], **grouped}
    options = []
    for other_id, other_races in grouped.items():
        href = f"/logbook?user_id={quote(user_id)}&car={quote(other_id)}"
        selected = " selected" if other_id == car_id else ""
        label = _title_name(other_id)
        options.append(f'<option value="{_esc(href)}"{selected}>{_esc(label)}</option>')
    return f"""
    <label class="title-picker">
      <span class="sr">Car</span>
      <select class="car-title" onchange="if (this.value) location.href = this.value">
        {''.join(options)}
      </select>
    </label>
    """


def render_logbook(
    user_id: str,
    car_id: str,
    races: list[RaceRow],
    milestones: Optional[list[Milestone]] = None,
) -> str:
    """Timeslip page for one car."""
    car_races = [race for race in races if race.car == car_id]
    car_marks = [item for item in (milestones or []) if item.car == car_id]
    entries = _ordered_entries(car_races, car_marks)
    level = next((race.car_level for race in car_races if race.car_level is not None), None)
    rows = _raw_rows(entries)
    if not rows:
        rows = "<tr><td colspan='8'>No runs for this car in the window.</td></tr>"
    return _page(
        title=_title_name(car_id),
        wash=car_theme(car_id)[0],
        stripe=car_theme(car_id)[1],
        body=f"""
        <header class="mast">
          <p class="brand">NHRA LEGENDS · CAR LOGBOOK</p>
          {_level_line(level, car_races)}
          {_car_picker(user_id, car_id, races)}
        </header>
        {_trend_panel(car_races)}
        <section class="chief">
          <h2>Tips from your crew chief</h2>
          <p>{_esc(crew_chief_note(car_races, car_marks))}</p>
        </section>
        <details class="sheet" id="raw-data">
          <summary>Raw Data</summary>
          <table>
            <thead>
              <tr>
                <th>When</th><th>Event</th><th>RT</th><th>60</th><th>330</th><th>ET</th><th>MPH</th><th>Result</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </details>
        <p class="note">Numbers come from production telemetry for this device id. Opponent and part names are ids, not invented history.</p>
        {_book_links(user_id)}
        """,
    )


def render_driver(user_id: str, races: list[RaceRow]) -> str:
    """Player home: every car's races in one record."""
    record = driver_record(races)
    years = " · ".join(record["years"]) if record["years"] else "THIS BOOK"
    most = _title_name(record["most_raced_car"]) if record["most_raced_car"] else "—"
    fastest_car = _title_name(record["fastest_rt_car"]) if record["fastest_rt_car"] else ""
    fastest_detail = fastest_car
    if record["fastest_rt_at"]:
        fastest_detail = f"{fastest_car} · {record['fastest_rt_at']}" if fastest_car else record["fastest_rt_at"]
    return _page(
        title="Driver",
        body=f"""
        <header class="mast">
          <p class="brand">NHRA LEGENDS · DRIVER</p>
          <p class="eyebrow">{_esc(years)} · {_esc(len(record['cars']))} CARS</p>
          <h1>Driver</h1>
          <p class="lead">Every race on this device, across every car.</p>
        </header>
        <section class="driver-stats">
          <article><strong>{_esc(record['wins'])}</strong><span>WINS</span></article>
          <article><strong>{_esc(record['races'])}</strong><span>RACES</span></article>
          <article><strong>{_esc(_fmt(record['best_et']))}</strong><span>BEST ET</span></article>
          <article><strong>{_esc(_fmt(record['best_mph'], 1))}</strong><span>BEST MPH</span></article>
        </section>
        <section class="callouts">
          <article>
            <span>MOST RACED CAR</span>
            <strong>{_esc(most)}</strong>
            <em>{_esc(record['most_raced_count'])} RACES</em>
          </article>
          <article>
            <span>FASTEST RT</span>
            <strong>{_esc(_fmt(record['fastest_rt']))}</strong>
            <em>{_esc(fastest_detail)}</em>
          </article>
        </section>
        <section class="driver-block">
          <h2>Cars</h2>
          {_car_table(user_id, record)}
        </section>
        <p class="back"><a href="/cars?user_id={_esc(user_id)}">All cars</a></p>
        """,
    )


def _book_links(user_id: str) -> str:
    """All-cars link and the player's driver page."""
    cars = f'<a href="/cars?user_id={_esc(user_id)}">All cars</a>'
    driver = f'<a href="/driver?user_id={_esc(user_id)}">Driver</a>'
    return f'<p class="back links">{cars}{driver}</p>'


def _car_table(user_id: str, record: dict[str, Any]) -> str:
    """One row per car in the player's book, most raced first. The name opens that car."""
    if not record["cars"]:
        return "<p class='empty'>No completed races in this window.</p>"
    rows = []
    for car in record["cars"]:
        href = f"/logbook?user_id={_esc(user_id)}&car={_esc(car['car'])}"
        rows.append(
            "<tr>"
            f"<td><a class=\"car-link\" href=\"{href}\">{_esc(_title_name(car['car']))}</a></td>"
            f"<td>{_esc(car['races'])}</td>"
            f"<td>{_esc(car['wins'])}-{_esc(car['losses'])}</td>"
            f"<td class='et'>{_esc(_fmt(car['best_et']))}</td>"
            "</tr>"
        )
    return (
        "<div class='sheet'><table><thead><tr>"
        "<th>Car</th><th>Runs</th><th>W-L</th><th>Best ET</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def _ordered_entries(
    races: list[RaceRow], milestones: list[Milestone]
) -> list[tuple[str, int, RaceRow | Milestone]]:
    """Newest first. The index is the Raw Data row id."""
    tagged: list[tuple[str, str, RaceRow | Milestone]] = [("race", race.raced_at, race) for race in races]
    tagged.extend(("mark", item.at, item) for item in milestones if not is_vehicle_body_change(item.detail))
    tagged.sort(key=lambda item: item[1], reverse=True)
    return [(kind, index, obj) for index, (kind, _, obj) in enumerate(tagged)]


def _trend_panel(races: list[RaceRow]) -> str:
    """One chart. The menu redraws that line across the days this car actually raced."""
    options = []
    series: dict[str, dict[str, Any]] = {}
    for key, label, attr, digits, _lower_is_better in TREND_METRICS:
        selected = " selected" if key == "et" else ""
        options.append(f'<option value="{key}"{selected}>{label}</option>')
        trend = daily_win_rate(races) if attr == "win_rate" else daily_trend(races, attr)
        if trend:
            axis_start, axis_end = trend[0][0], trend[-1][0]
            ticks = chart_ticks(axis_start, axis_end)
        else:
            axis_start, axis_end, ticks = "", "", []
        points = []
        for day, value in trend:
            placed = calendar_fraction(day, axis_start, axis_end)
            if placed is None:
                continue
            points.append({"day": day, "value": value, "x": placed})
        series[key] = {
            "digits": digits,
            "ticks": [{"day": day, "x": calendar_fraction(day, axis_start, axis_end)} for day in ticks],
            "points": points,
        }
    et_points = [(point["day"], point["value"], point["x"]) for point in series["et"]["points"]]
    payload = json.dumps(series).replace("<", "\\u003c")
    return f"""
    <section class="trend">
      <label class="metric-picker">
        <span>Daily average</span>
        <select id="trend-metric" onchange="showTrend(this.value)">
          {''.join(options)}
        </select>
      </label>
      <p id="trend-empty" class="trend-empty" hidden>No times for this metric.</p>
      {_trend_svg(et_points, series["et"]["digits"], series["et"]["ticks"])}
    </section>
    <script id="trend-series" type="application/json">{payload}</script>
    <script>
      function showTrend(name) {{
        var series = JSON.parse(document.getElementById("trend-series").textContent)[name];
        var chart = document.getElementById("trend-chart");
        var empty = document.getElementById("trend-empty");
        var points = series.points;
        if (!points.length) {{
          chart.hidden = true;
          empty.hidden = false;
          return;
        }}
        chart.hidden = false;
        empty.hidden = true;
        var width = 720, height = 260, left = 72, right = 16, top = 16, bottom = 36;
        var low = points[0].value, high = points[0].value;
        points.forEach(function (point) {{
          if (point.value < low) low = point.value;
          if (point.value > high) high = point.value;
        }});
        if (high === low) {{ low -= 0.05; high += 0.05; }}
        var span = high - low;
        var plotW = width - left - right;
        var plotH = height - top - bottom;
        var coords = points.map(function (point) {{
          var x = left + point.x * plotW;
          var y = top + (1 - ((point.value - low) / span)) * plotH;
          return x.toFixed(1) + "," + y.toFixed(1);
        }});
        document.getElementById("trend-line").setAttribute("points", coords.join(" "));
        var dot = document.getElementById("trend-dot");
        if (points.length === 1) {{
          var pair = coords[0].split(",");
          dot.setAttribute("cx", pair[0]);
          dot.setAttribute("cy", pair[1]);
          dot.removeAttribute("display");
        }} else {{
          dot.setAttribute("display", "none");
        }}
        var digits = series.digits;
        document.getElementById("trend-high").textContent = high.toFixed(digits);
        document.getElementById("trend-low").textContent = low.toFixed(digits);
        series.ticks.forEach(function (tick, index) {{
          var node = document.getElementById("trend-tick-" + index);
          if (!node) return;
          node.textContent = tick.day.slice(5);
          node.setAttribute("x", (left + tick.x * plotW).toFixed(1));
        }});
      }}
      showTrend("et");
    </script>
    """


def _trend_svg(
    points: list[tuple[str, float, float]],
    digits: int,
    ticks: list[dict[str, Any]],
) -> str:
    """Scoreboard line for the default series. Later metrics reuse this SVG."""
    width, height = 720, 260
    left, right, top, bottom = 72, 16, 16, 36
    plot_w = width - left - right
    if not points:
        return f'<svg id="trend-chart" class="trend-chart" viewBox="0 0 {width} {height}" role="img" hidden></svg>'
    values = [value for _, value, _ in points]
    low = min(values)
    high = max(values)
    if high == low:
        low -= 0.05
        high += 0.05
    span = high - low
    plot_h = height - top - bottom
    coords = []
    for _, value, placed in points:
        x = left + placed * plot_w
        y = top + (1 - ((value - low) / span)) * plot_h
        coords.append((x, y))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    dot_x, dot_y = coords[0]
    dot_display = "" if len(coords) == 1 else ' display="none"'
    tick_nodes = []
    for index, tick in enumerate(ticks):
        anchor = "start" if index == 0 else "end" if index == len(ticks) - 1 else "middle"
        x = left + float(tick["x"]) * plot_w
        tick_nodes.append(
            f'<text id="trend-tick-{index}" x="{x:.1f}" y="{height - 8}" text-anchor="{anchor}">{_esc(str(tick["day"])[5:])}</text>'
        )
    return f"""
    <svg id="trend-chart" class="trend-chart" viewBox="0 0 {width} {height}" role="img">
      <line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#a2938d" stroke-width="1"/>
      <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#a2938d" stroke-width="1"/>
      <text id="trend-high" x="{left - 8}" y="{top + 10}" text-anchor="end">{_esc(_fmt(high, digits))}</text>
      <text id="trend-low" x="{left - 8}" y="{height - bottom}" text-anchor="end">{_esc(_fmt(low, digits))}</text>
      {''.join(tick_nodes)}
      <polyline id="trend-line" points="{poly}" fill="none" stroke="var(--stripe)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>
      <circle id="trend-dot" cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="4" fill="var(--stripe)"{dot_display}/>
    </svg>
    """


def _raw_rows(entries: list[tuple[str, int, RaceRow | Milestone]]) -> str:
    """Race rows and config changes, newest first, with ids the chart can open."""
    rows = []
    for kind, index, obj in entries:
        if kind == "mark" and isinstance(obj, Milestone):
            rows.append(_milestone_row(obj, f"row-{index}"))
        elif isinstance(obj, RaceRow):
            rows.append(_slip_row(obj, f"row-{index}"))
    return "\n".join(rows)


def _milestone_row(item: Milestone, row_id: str) -> str:
    return f"""
    <tr class="config-row" id="{row_id}">
      <td>{_esc(item.at)}</td>
      <td colspan="7">{_esc(item.detail)}</td>
    </tr>
    """


def _slip_row(race: RaceRow, row_id: str) -> str:
    stamp = result_label(race.result)
    foul = " foul" if race.red_light else ""
    return f"""
    <tr id="{row_id}">
      <td>{_esc(race.raced_at)}</td>
      <td>{_esc(race.race_event or '—')}</td>
      <td>{_esc(_fmt(race.reaction_time))}</td>
      <td>{_esc(_fmt(race.time_to_60))}</td>
      <td>{_esc(_fmt(race.time_to_330))}</td>
      <td class="et">{_esc(_fmt(race.total_time))}</td>
      <td>{_esc(_fmt(race.top_speed_mph, 1))}</td>
      <td class="stamp {stamp.lower()}">{_esc(stamp)}{_esc(foul)}</td>
    </tr>
    """


def render_home(error: str = "") -> str:
    """Ask for the Concrete Device ID."""
    error_html = f"<p class='error'>{_esc(error)}</p>" if error else ""
    return _page(
        title="Car logbook",
        body=f"""
        <header class="mast">
          <p class="brand">NHRA LEGENDS · CAR LOGBOOK</p>
          <h1>Open a book</h1>
          <p class="lead">Paste a Concrete Device ID. That is the Analytics user id. A Firebase Auth uid will not match.</p>
        </header>
        {error_html}
        <form action="/cars" method="get" class="lookup">
          <label for="user_id">Concrete Device ID</label>
          <input id="user_id" name="user_id" required placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" autocomplete="off">
          <button type="submit">Look up races</button>
        </form>
        """,
    )


def _page(title: str, body: str, wash: str = "#2a1212", stripe: str = "#fcc83c") -> str:
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)} · Car Logbook</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Saira:ital,wght@0,400;0,600;1,400;1,700;1,800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/logbook.css">
</head>
<body style="--wash: {_esc(wash)}; --car: {_esc(stripe)}; --stripe: {_esc(stripe)}">
  <div class="stage">
    <div class="phone">
      <div class="phone-screen">
        <main>{body}</main>
      </div>
    </div>
  </div>
</body>
</html>
"""
    lowered = document.lower()
    for word in BANNED:
        if word in lowered:
            raise RuntimeError(f"Banned word in logbook HTML: {word}")
    return document


def assert_clean_copy(text: str) -> None:
    """Fail if generated copy uses a banned marketing word."""
    lowered = text.lower()
    for word in BANNED:
        if word in lowered:
            raise RuntimeError(f"Banned word in logbook HTML: {word}")
