"""Fetch and shape one player's NHRA race history for a car logbook.

Analytics `user_id` is the Concrete Device ID (UUID). The car id lives on
`Play_Mode_Race_Started`. Finish numbers live on `Play_Mode_Race_Complete`.
The two rows share `GUID`.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

BQ_PROJECT = "nhra-64ac5"
BQ_DATASET = "analytics_490826646"
MAX_DRY_RUN_USD = 2.0
MPS_TO_MPH = 2.2369362920544

RESULT_LABELS = {
    "PlayerWon": "WIN",
    "PlayerLost": "LOSS",
    "PlayerQuit": "QUIT",
    "PlayerDisqualified": "DQ",
    "MidRace": "DNF",
}


@dataclass
class RaceRow:
    """One finished or started race, after the GUID join."""

    guid: str
    car: str
    car_level: Optional[int]
    race_event: str
    result: str
    raced_at: str
    reaction_time: Optional[float]
    elapsed_time: Optional[float]
    total_time: Optional[float]
    time_to_60: Optional[float]
    time_to_330: Optional[float]
    top_speed_mph: Optional[float]
    red_light: Optional[bool]
    opponent_car: str
    opponent_total_time: Optional[float]
    shifts: Optional[int]
    perfect_shifts: Optional[int]
    perfect_launch: Optional[bool]
    loadout: dict[str, str] = field(default_factory=dict)


@dataclass
class Milestone:
    """A car-level change, part upgrade, or part swap."""

    car: str
    at: str
    detail: str


def humanize_car_id(car_id: str) -> str:
    """Turn a content id into a nameplate without inventing a driver or sponsor."""
    cleaned = car_id.replace("_", " ").replace("-", " ").strip()
    return cleaned.upper() if cleaned else "UNKNOWN CAR"


def humanize_event(event_id: str) -> str:
    """Turn a race-event id into a label without inventing a track or round."""
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", event_id)
    cleaned = spaced.replace("_", " ").replace("-", " ").strip()
    return cleaned.upper() if cleaned else "UNKNOWN EVENT"


def result_label(result: str) -> str:
    """Map the analytics enum to the timeslip stamp."""
    return RESULT_LABELS.get(result, result or "—")


def mph_from_mps(meters_per_second: Optional[float]) -> Optional[float]:
    """Convert telemetry top speed to miles per hour."""
    if meters_per_second is None or meters_per_second < 0:
        return None
    return round(meters_per_second * MPS_TO_MPH, 2)


def _best(values: list[Optional[float]], *, lowest: bool) -> Optional[float]:
    usable = [value for value in values if value is not None and value >= 0]
    if not usable:
        return None
    return min(usable) if lowest else max(usable)


def summarize_car(races: list[RaceRow]) -> dict[str, Any]:
    """Win-loss and best numbers for one car. Math stays in Python."""
    finished = [race for race in races if race.result]
    wins = sum(1 for race in finished if race.result == "PlayerWon")
    losses = sum(1 for race in finished if race.result == "PlayerLost")
    return {
        "races": len(races),
        "wins": wins,
        "losses": losses,
        "best_et": _best([race.total_time for race in races], lowest=True),
        "best_rt": _best(
            [race.reaction_time for race in races if race.reaction_time is not None and race.reaction_time >= 0],
            lowest=True,
        ),
        "best_60": _best([race.time_to_60 for race in races], lowest=True),
        "best_mph": _best([race.top_speed_mph for race in races], lowest=False),
    }


def driver_record(races: list[RaceRow]) -> dict[str, Any]:
    """Combined record for one player across every car in the book."""
    summary = summarize_car(races)
    best_et_race = _extreme_race(races, "total_time", lowest=True)
    best_mph_race = _extreme_race(races, "top_speed_mph", lowest=False)
    fastest = _extreme_race(races, "reaction_time", lowest=True)
    by_car: dict[str, list[RaceRow]] = {}
    for race in races:
        by_car.setdefault(race.car or "", []).append(race)
    most_car = ""
    most_count = 0
    if by_car:
        most_car = max(by_car, key=lambda car: (len(by_car[car]), car))
        most_count = len(by_car[most_car])
    cars = []
    for car, group in by_car.items():
        car_summary = summarize_car(group)
        cars.append(
            {
                "car": car,
                "races": car_summary["races"],
                "wins": car_summary["wins"],
                "losses": car_summary["losses"],
                "best_et": car_summary["best_et"],
            }
        )
    cars.sort(key=lambda item: (-item["races"], item["car"]))
    years = sorted({race.raced_at[:4] for race in races if len(race.raced_at) >= 4 and race.raced_at[:4].isdigit()})
    return {
        **summary,
        "best_et_at": best_et_race.raced_at[:10] if best_et_race else "",
        "best_mph_at": best_mph_race.raced_at[:10] if best_mph_race else "",
        "fastest_rt": fastest.reaction_time if fastest else None,
        "fastest_rt_car": fastest.car if fastest else "",
        "fastest_rt_at": fastest.raced_at[:10] if fastest else "",
        "most_raced_car": most_car,
        "most_raced_count": most_count,
        "cars": cars,
        "years": years,
    }


def daily_trend(races: list[RaceRow], attr: str) -> list[tuple[str, float]]:
    """Daily mean of one timeslip field, oldest day first."""
    buckets: dict[str, list[float]] = {}
    for race in races:
        value = getattr(race, attr)
        if value is None:
            continue
        day = (race.raced_at or "")[:10]
        if len(day) != 10:
            continue
        buckets.setdefault(day, []).append(value)
    points: list[tuple[str, float]] = []
    for day in sorted(buckets):
        values = buckets[day]
        points.append((day, sum(values) / len(values)))
    return points


def daily_win_rate(races: list[RaceRow]) -> list[tuple[str, float]]:
    """Daily win percentage. Quits and DQs stay out. Oldest day first."""
    buckets: dict[str, list[str]] = {}
    for race in races:
        day = (race.raced_at or "")[:10]
        if len(day) != 10 or race.result not in {"PlayerWon", "PlayerLost"}:
            continue
        buckets.setdefault(day, []).append(race.result)
    points: list[tuple[str, float]] = []
    for day in sorted(buckets):
        results = buckets[day]
        wins = sum(1 for result in results if result == "PlayerWon")
        points.append((day, 100.0 * wins / len(results)))
    return points


def group_by_car(races: list[RaceRow]) -> dict[str, list[RaceRow]]:
    """Bucket races by the car id from the start event."""
    grouped: dict[str, list[RaceRow]] = {}
    for race in races:
        key = race.car or "unknown"
        grouped.setdefault(key, []).append(race)
    for rows in grouped.values():
        rows.sort(key=lambda row: row.raced_at, reverse=True)
    return dict(sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True))


def _param(row: Any, key: str) -> Any:
    return row.get(key)


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number


def _as_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def win_ratio(races: list[RaceRow]) -> Optional[float]:
    """Wins divided by decided races. Quits and DQs stay out of the ratio."""
    wins = sum(1 for race in races if race.result == "PlayerWon")
    losses = sum(1 for race in races if race.result == "PlayerLost")
    decided = wins + losses
    if decided == 0:
        return None
    return wins / decided


def record_runs(races: list[RaceRow], attr: str, *, lower_is_better: bool) -> list[RaceRow]:
    """Runs that set a new best for one timeslip field, oldest first."""
    best: Optional[float] = None
    records: list[RaceRow] = []
    for race in sorted(races, key=lambda item: item.raced_at):
        value = getattr(race, attr)
        if value is None:
            continue
        if best is None or (value < best if lower_is_better else value > best):
            best = value
            records.append(race)
    return records


def config_milestones(races: list[RaceRow]) -> list[Milestone]:
    """Changes in car level or part loadout between consecutive runs of one car."""
    by_car: dict[str, list[RaceRow]] = {}
    for race in races:
        by_car.setdefault(race.car, []).append(race)
    found: list[Milestone] = []
    for car, rows in by_car.items():
        ordered = sorted(rows, key=lambda race: race.raced_at)
        for previous, current in zip(ordered, ordered[1:]):
            if (
                previous.car_level is not None
                and current.car_level is not None
                and current.car_level != previous.car_level
            ):
                found.append(
                    Milestone(
                        car=car,
                        at=current.raced_at,
                        detail=f"Car level {previous.car_level} to {current.car_level}",
                    )
                )
            slots = set(previous.loadout) | set(current.loadout)
            for slot in sorted(slots):
                if _is_vehicle_body(slot):
                    continue
                old = previous.loadout.get(slot, "")
                new = current.loadout.get(slot, "")
                if not new or old == new:
                    continue
                found.append(Milestone(car=car, at=current.raced_at, detail=_part_change_text(slot, old, new)))
    return _dedupe_milestones(found)


def part_event_milestones(raw_rows: list[dict[str, Any]], races: list[RaceRow]) -> list[Milestone]:
    """Explicit Part Equipped and Part Upgraded events."""
    found: list[Milestone] = []
    for row in raw_rows:
        name = row.get("event_name")
        at = str(row.get("raced_at") or "")
        if name == "Part_Equipped":
            car = str(row.get("car") or "")
            if not car or not at:
                continue
            part = str(row.get("part") or "")
            previous = str(row.get("previous_part") or "")
            slot = str(row.get("part_type") or "part")
            if _is_vehicle_body(slot, part):
                continue
            if previous:
                detail = f"Swap {slot}: {previous} to {part}"
            else:
                detail = f"Equip {slot} {part}".strip()
            found.append(Milestone(car=car, at=at, detail=detail))
        elif name == "Part_Upgraded":
            part = str(row.get("part") or "")
            if _is_vehicle_body("", part):
                continue
            level = _as_int(row.get("part_level"))
            car = _car_for_part(part, at, races)
            if not car or not part:
                continue
            level_text = f" to level {level}" if level is not None else ""
            found.append(Milestone(car=car, at=at, detail=f"Upgrade {part}{level_text}"))
    return _dedupe_milestones(found)


def _mean(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _win_percent(rows: list[RaceRow]) -> Optional[float]:
    decided = [race for race in rows if race.result in {"PlayerWon", "PlayerLost"}]
    if not decided:
        return None
    wins = sum(1 for race in decided if race.result == "PlayerWon")
    return 100.0 * wins / len(decided)


def crew_chief_note(races: list[RaceRow], milestones: Optional[list[Milestone]] = None) -> str:
    """Crew note led by whatever this car's book actually shows."""
    if not races:
        return "No runs in this window. Nothing to call yet."
    ordered = sorted(races, key=lambda race: race.raced_at)
    wins = sum(1 for race in ordered if race.result == "PlayerWon")
    losses = sum(1 for race in ordered if race.result == "PlayerLost")
    reds = sum(1 for race in ordered if race.red_light)
    ets = [race.total_time for race in ordered if race.total_time is not None]
    reaction = [race.reaction_time for race in ordered if race.reaction_time is not None and race.reaction_time >= 0]
    sixty = [race.time_to_60 for race in ordered if race.time_to_60 is not None]
    best_et = min(ets) if ets else None
    mean_et = _mean(ets)
    mean_rt = _mean(reaction)
    mean_60 = _mean(sixty)
    best_60 = min(sixty) if sixty else None
    mid = max(len(ordered) // 2, 1)
    early, late = ordered[:mid], ordered[mid:]
    early_et, late_et = _mean([race.total_time for race in early if race.total_time is not None]), _mean(
        [race.total_time for race in late if race.total_time is not None]
    )
    early_win, late_win = _win_percent(early), _win_percent(late)
    changes = [item for item in (milestones or []) if not is_vehicle_body_change(item.detail)]
    repeated = ""
    if changes:
        counts: dict[str, int] = {}
        for item in changes:
            counts[item.detail] = counts.get(item.detail, 0) + 1
        repeated = max(counts, key=lambda detail: counts[detail])
        if counts[repeated] < 2:
            repeated = ""
    if len(ordered) == 1:
        race = ordered[0]
        slip = f"{race.total_time:.3f}" if race.total_time is not None else "no ET"
        light = f" on a {race.reaction_time:.3f} light" if race.reaction_time is not None else ""
        outcome = "a win" if race.result == "PlayerWon" else "a loss" if race.result == "PlayerLost" else "not a decision"
        return f"One slip in the book, and it was {outcome}: {slip}{light}. Do not build a setup off a single run."
    sentences: list[str] = []
    red_rate = reds / len(ordered)
    win_drop = early_win - late_win if early_win is not None and late_win is not None else 0.0
    et_delta = (early_et - late_et) if early_et is not None and late_et is not None else 0.0
    held_wins = (
        early_win is not None
        and late_win is not None
        and early_win >= 65
        and abs(early_win - late_win) < 8
    )
    if len(ordered) >= 400 and held_wins and best_60 is not None and mean_60 is not None:
        sentences.append(
            f"This is a winning book, {wins} wins and {losses} losses, and the win rate stayed near {late_win:.0f}%. "
            f"The ET came in from {early_et:.3f} to {late_et:.3f}. "
            f"What did not come in is the 60-foot: {mean_60:.3f} average against a {best_60:.3f} best."
        )
    elif win_drop >= 12 and early_win is not None and late_win is not None and early_et is not None and late_et is not None:
        quicker = "even while the ET came in" if et_delta > 0.05 else "and the ET did not save it"
        sentences.append(
            f"Win rate fell from {early_win:.0f}% to {late_win:.0f}% {quicker}, "
            f"{early_et:.3f} in the first half and {late_et:.3f} in the second. "
            f"{reds} red lights in {len(ordered)} runs."
        )
    elif red_rate >= 0.18 and best_et is not None and mean_et is not None:
        sentences.append(
            f"{reds} red lights in {len(ordered)} runs. "
            f"The car has a {best_et:.3f} in it and the average is {mean_et:.3f}, "
            f"but a foul spends the round before that ET matters."
        )
    elif red_rate <= 0.08 and mean_rt is not None and mean_rt >= 0.35 and early_win is not None and late_win is not None:
        red_word = "red light" if reds == 1 else "red lights"
        if late_win + 3 < early_win:
            move = f"Win rate slid from {early_win:.0f}% to {late_win:.0f}% on late leaves, not on broken parts."
        else:
            move = f"The win rate held near {late_win:.0f}%. The rounds that get away are the late light, not a foul."
        sentences.append(f"{reds} {red_word} in the book, and the light is still {mean_rt:.3f}. {move}")
    elif et_delta >= 0.2 and held_wins and early_et is not None and late_et is not None and mean_rt is not None:
        sentences.append(
            f"Leave the combination. ET moved from {early_et:.3f} to {late_et:.3f} and the win rate held around {late_win:.0f}%. "
            f"The leftover is the light at {mean_rt:.3f}, with {reds} reds."
        )
    elif et_delta <= -0.15 and early_et is not None and late_et is not None:
        sentences.append(
            f"ET went the wrong way, {early_et:.3f} in the first half and {late_et:.3f} in the second."
        )
    elif best_et is not None and mean_et is not None and wins + losses:
        sentences.append(
            f"{wins} wins and {losses} losses. Best ET is {best_et:.3f}. The average is {mean_et - best_et:.3f} behind that number."
        )
    if repeated and win_drop >= 8:
        sentences.append(f"While the wins fell off, the same change kept showing up: {repeated}.")
    elif repeated and red_rate >= 0.18:
        sentences.append(f"Parts are not the round. The repeated change is {repeated}, and the tree is still the loss.")
    elif best_60 is not None and mean_60 is not None and mean_60 - best_60 >= 0.5 and len(ordered) < 400:
        sentences.append(f"60-foot is scattered, {best_60:.3f} best and {mean_60:.3f} average.")
    if not sentences:
        sentences.append("Not enough of a pattern yet. Log more runs before you change the car.")
    return " ".join(sentences[:2])


def is_vehicle_body_change(detail: str) -> bool:
    """True when a milestone is a swap or upgrade of the car body itself."""
    compact = detail.replace(" ", "").lower()
    if "vehiclebody" in compact:
        return True
    return detail.lower().startswith("upgrade vehicle_")


def _is_vehicle_body(slot: str, part: str = "") -> bool:
    """The vehicle body is the car this book is already about."""
    if slot.replace("_", "").lower() == "vehiclebody":
        return True
    return part.startswith("Vehicle_")


def _part_change_text(slot: str, old: str, new: str) -> str:
    label = slot.replace("_", " ")
    old_name, old_level = _split_part(old)
    new_name, new_level = _split_part(new)
    if old_name == new_name and old_level is not None and new_level is not None and new_level != old_level:
        return f"Upgrade {label} to level {new_level}"
    if not old:
        return f"Equip {label} {new}"
    return f"Swap {label} to {new}"


def _split_part(value: str) -> tuple[str, Optional[int]]:
    index = len(value)
    while index > 0 and value[index - 1].isdigit():
        index -= 1
    if index == 0 or index == len(value):
        return value, None
    return value[:index], int(value[index:])


def _car_for_part(part: str, at: str, races: list[RaceRow]) -> str:
    """Attribute an upgrade to the car whose loadout held that part just before it."""
    if not part:
        return ""
    candidates = []
    for race in races:
        if race.raced_at > at:
            continue
        if any(value == part or value.startswith(part) for value in race.loadout.values()):
            candidates.append(race)
    if not candidates:
        return ""
    candidates.sort(key=lambda race: race.raced_at, reverse=True)
    return candidates[0].car


def _dedupe_milestones(items: list[Milestone]) -> list[Milestone]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[Milestone] = []
    for item in items:
        key = (item.car, item.at, item.detail)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _loadout_from_row(row: dict[str, Any]) -> dict[str, str]:
    text = row.get("loadout_json")
    if not text:
        return {}
    try:
        items = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {}
    loadout: dict[str, str] = {}
    for item in items:
        key = str(item.get("k") or "")
        value = item.get("v")
        if not key or value is None:
            continue
        loadout[key] = str(value)
    return loadout


def history_from_query(raw_rows: list[dict[str, Any]]) -> tuple[list[RaceRow], list[Milestone]]:
    """Races plus config, upgrade, and swap milestones."""
    races = rows_from_query(raw_rows)
    milestones = config_milestones(races) + part_event_milestones(raw_rows, races)
    milestones = _dedupe_milestones(milestones)
    milestones.sort(key=lambda item: item.at, reverse=True)
    return races, milestones


def rows_from_query(raw_rows: list[dict[str, Any]]) -> list[RaceRow]:
    """Join start and complete rows that share a GUID."""
    starts: dict[str, dict[str, Any]] = {}
    completes: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        guid = str(row.get("guid") or "")
        if not guid:
            continue
        if row.get("event_name") == "Play_Mode_Race_Started":
            starts[guid] = row
        elif row.get("event_name") == "Play_Mode_Race_Complete":
            completes[guid] = row

    races: list[RaceRow] = []
    for guid, complete in completes.items():
        start = starts.get(guid, {})
        races.append(
            RaceRow(
                guid=guid,
                car=str(start.get("car") or "unknown"),
                car_level=_as_int(start.get("car_level")),
                race_event=str(complete.get("race_event") or start.get("race_event") or ""),
                result=str(complete.get("result") or ""),
                raced_at=str(complete.get("raced_at") or ""),
                reaction_time=_as_float(complete.get("reaction_time")),
                elapsed_time=_as_float(complete.get("elapsed_time")),
                total_time=_as_float(complete.get("total_time")),
                time_to_60=_as_float(complete.get("time_to_60")),
                time_to_330=_as_float(complete.get("time_to_330")),
                top_speed_mph=mph_from_mps(_as_float(complete.get("top_speed_mps"))),
                red_light=_as_bool(complete.get("red_light")),
                opponent_car=str(complete.get("opponent_car") or ""),
                opponent_total_time=_as_float(complete.get("opponent_total_time")),
                shifts=_as_int(complete.get("shifts")),
                perfect_shifts=_as_int(complete.get("perfect_shifts")),
                perfect_launch=_as_bool(complete.get("perfect_launch_timing")),
                loadout=_loadout_from_row(start),
            )
        )
    races.sort(key=lambda race: race.raced_at, reverse=True)
    return races


HISTORY_DAYS = 60


def chart_window(days: int = HISTORY_DAYS, today: Optional[datetime] = None) -> tuple[str, str]:
    """Inclusive UTC dates for the trend axis, oldest day first."""
    end = (today or datetime.now(timezone.utc)).date()
    start = end - timedelta(days=max(days, 1) - 1)
    return start.isoformat(), end.isoformat()


def chart_ticks(start: str, end: str, count: int = 5) -> list[str]:
    """Evenly spaced dates across the axis, including both ends."""
    start_day = datetime.fromisoformat(start).date()
    end_day = datetime.fromisoformat(end).date()
    if count < 2:
        return [start_day.isoformat()]
    span = (end_day - start_day).days
    ticks = []
    for index in range(count):
        day = start_day + timedelta(days=round(index * span / (count - 1)))
        ticks.append(day.isoformat())
    return ticks


def calendar_fraction(day: str, start: str, end: str) -> Optional[float]:
    """Position of a calendar day on the axis. 0 is the first day, 1 is the last."""
    start_day = datetime.fromisoformat(start).date()
    end_day = datetime.fromisoformat(end).date()
    day_value = datetime.fromisoformat(day[:10]).date()
    span = (end_day - start_day).days
    offset = (day_value - start_day).days
    if span <= 0:
        return 0.0 if day_value == start_day else None
    if offset < 0 or offset > span:
        return None
    return offset / span


def _date_suffix(days: int) -> tuple[str, str]:
    start, end = chart_window(days)
    return start.replace("-", ""), end.replace("-", "")


def _history_sql(start_suffix: str, end_suffix: str) -> str:
    table = f"`{BQ_PROJECT}.{BQ_DATASET}.events_*`"
    return f"""
SELECT
  event_name,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M UTC', TIMESTAMP_MICROS(event_timestamp)) AS raced_at,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'GUID') AS guid,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'car') AS car,
  (SELECT COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64))
     FROM UNNEST(event_params) WHERE key = 'carLevel') AS car_level,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'raceEvent') AS race_event,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'result') AS result,
  (SELECT COALESCE(value.double_value, value.float_value, SAFE_CAST(value.string_value AS FLOAT64))
     FROM UNNEST(event_params) WHERE key = 'reactionTime') AS reaction_time,
  (SELECT COALESCE(value.double_value, value.float_value, SAFE_CAST(value.string_value AS FLOAT64))
     FROM UNNEST(event_params) WHERE key = 'elapsedTime') AS elapsed_time,
  (SELECT COALESCE(value.double_value, value.float_value, SAFE_CAST(value.string_value AS FLOAT64))
     FROM UNNEST(event_params) WHERE key = 'totalTime') AS total_time,
  (SELECT COALESCE(value.double_value, value.float_value, SAFE_CAST(value.string_value AS FLOAT64))
     FROM UNNEST(event_params) WHERE key = 'timeTo60Feet') AS time_to_60,
  (SELECT COALESCE(value.double_value, value.float_value, SAFE_CAST(value.string_value AS FLOAT64))
     FROM UNNEST(event_params) WHERE key = 'timeTo330Feet') AS time_to_330,
  (SELECT COALESCE(value.double_value, value.float_value, SAFE_CAST(value.string_value AS FLOAT64))
     FROM UNNEST(event_params) WHERE key = 'topSpeedMetersPerSecond') AS top_speed_mps,
  (SELECT COALESCE(CAST(value.int_value AS STRING), value.string_value)
     FROM UNNEST(event_params) WHERE key = 'redLight') AS red_light,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'opponentCar') AS opponent_car,
  (SELECT COALESCE(value.double_value, value.float_value)
     FROM UNNEST(event_params) WHERE key = 'opponentTotalTime') AS opponent_total_time,
  (SELECT COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64))
     FROM UNNEST(event_params) WHERE key = 'shifts') AS shifts,
  (SELECT COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64))
     FROM UNNEST(event_params) WHERE key = 'perfectShifts') AS perfect_shifts,
  (SELECT COALESCE(CAST(value.int_value AS STRING), value.string_value)
     FROM UNNEST(event_params) WHERE key = 'perfectLaunchTiming') AS perfect_launch_timing,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'part') AS part,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'previousPart') AS previous_part,
  (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'partType') AS part_type,
  (SELECT COALESCE(value.int_value, SAFE_CAST(value.string_value AS INT64))
     FROM UNNEST(event_params) WHERE key = 'level') AS part_level,
  (SELECT TO_JSON_STRING(ARRAY(
     SELECT AS STRUCT ep.key AS k,
       COALESCE(ep.value.string_value, CAST(ep.value.int_value AS STRING), CAST(ep.value.double_value AS STRING)) AS v
     FROM UNNEST(event_params) ep
     WHERE ep.key NOT IN (
       'GUID','car','carLevel','playerRaceNumber','carRaceNumber','raceEvent','lossStreakAtStart',
       'result','reactionTime','elapsedTime','totalTime','timeTo60Feet','timeTo330Feet',
       'topSpeedMetersPerSecond','redLight','opponentCar','opponentTotalTime','shifts',
       'perfectShifts','perfectLaunchTiming','perfectLaunchRevs','perfectRace','raceAvgFps',
       'devicePerfScore','graphicsQualityLevel','finalTargetWinRate','opponentSource',
       'part','previousPart','partType','level','source','additionalParts'
     )
     AND NOT STARTS_WITH(ep.key, 'ga_')
     AND NOT STARTS_WITH(ep.key, 'firebase_')
  ))) AS loadout_json
FROM {table}
WHERE _TABLE_SUFFIX BETWEEN '{start_suffix}' AND '{end_suffix}'
  AND user_id = @user_id
  AND event_name IN ('Play_Mode_Race_Started', 'Play_Mode_Race_Complete', 'Part_Equipped', 'Part_Upgraded')
"""


def _client():
    from google.cloud import bigquery

    return bigquery.Client(project=BQ_PROJECT)


def fetch_races(user_id: str, days: int = HISTORY_DAYS) -> tuple[list[RaceRow], list[Milestone]]:
    """Query production telemetry for one Concrete Device ID."""
    from google.cloud import bigquery

    user_id = user_id.strip()
    if not user_id:
        raise ValueError("user_id is required")
    start_suffix, end_suffix = _date_suffix(days)
    sql = _history_sql(start_suffix, end_suffix)
    client = _client()
    dry = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            dry_run=True,
            use_query_cache=False,
            query_parameters=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)],
        ),
    )
    cost = dry.total_bytes_processed / (1024 ** 4) * 6.25
    if cost > MAX_DRY_RUN_USD:
        raise RuntimeError(f"Query refused: estimated ${cost:.2f} exceeds ${MAX_DRY_RUN_USD:.2f}")
    job = client.query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)],
        ),
    )
    raw = [dict(row.items()) for row in job.result()]
    return history_from_query(raw)


def find_active_user(days: int = 2) -> str:
    """Pick a production user with recent completed races. For the demo only."""
    from google.cloud import bigquery

    start_suffix, end_suffix = _date_suffix(days)
    table = f"`{BQ_PROJECT}.{BQ_DATASET}.events_*`"
    sql = f"""
SELECT user_id
FROM {table}
WHERE _TABLE_SUFFIX BETWEEN '{start_suffix}' AND '{end_suffix}'
  AND event_name = 'Play_Mode_Race_Complete'
  AND user_id IS NOT NULL
  AND user_id != ''
GROUP BY user_id
ORDER BY COUNT(*) DESC
LIMIT 1
"""
    client = _client()
    dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    cost = dry.total_bytes_processed / (1024 ** 4) * 6.25
    if cost > MAX_DRY_RUN_USD:
        raise RuntimeError(f"Sample-user query refused: estimated ${cost:.2f}")
    rows = list(client.query(sql).result())
    if not rows or not rows[0]["user_id"]:
        raise RuntimeError("No recent production user_id found")
    return str(rows[0]["user_id"])


def _extreme_race(races: list[RaceRow], attr: str, *, lowest: bool) -> Optional[RaceRow]:
    """Race with the lowest or highest value of one timeslip field."""
    chosen: Optional[RaceRow] = None
    chosen_value: Optional[float] = None
    for race in races:
        value = getattr(race, attr)
        if value is None or value < 0:
            continue
        if chosen_value is None or (value < chosen_value if lowest else value > chosen_value):
            chosen = race
            chosen_value = value
    return chosen


def cache_path(user_id: str) -> Path:
    """Gitignored JSON cache so a refresh does not rescan BigQuery."""
    safe = "".join(ch for ch in user_id if ch.isalnum() or ch in "-")
    return Path(__file__).resolve().parent.parent / "data" / f"{safe}.json"


CACHE_VERSION = 3


def save_cache(user_id: str, races: list[RaceRow], milestones: list[Milestone]) -> None:
    """Write races and config changes so a refresh does not rescan BigQuery."""
    path = cache_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": CACHE_VERSION,
        "days": HISTORY_DAYS,
        "user_id": user_id,
        "races": [asdict(race) for race in races],
        "milestones": [asdict(item) for item in milestones],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_cache(user_id: str) -> Optional[tuple[list[RaceRow], list[Milestone]]]:
    """Return cached races and milestones, or None when this user needs a new pull."""
    path = cache_path(user_id)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != CACHE_VERSION or payload.get("days") != HISTORY_DAYS:
        return None
    races = [RaceRow(**row) for row in payload.get("races", [])]
    milestones = [Milestone(**row) for row in payload.get("milestones", [])]
    return races, milestones
