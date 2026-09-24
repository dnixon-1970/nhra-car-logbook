"""Pure helpers for the car logbook. No BigQuery."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timezone

from tools.logbook_data import (  # noqa: E402
    Milestone,
    RaceRow,
    calendar_fraction,
    chart_window,
    config_milestones,
    daily_trend,
    daily_win_rate,
    driver_record,
    record_runs,
    group_by_car,
    humanize_car_id,
    mph_from_mps,
    result_label,
    rows_from_query,
    summarize_car,
)
from tools.export_pages import to_static, with_vehicle_redirect  # noqa: E402
from tools.logbook_render import render_driver, render_logbook  # noqa: E402


def _race(**overrides) -> RaceRow:
    base = dict(
        guid="g",
        car="usa_1",
        car_level=4,
        race_event="pomona_round_1",
        result="PlayerWon",
        raced_at="2026-09-23 18:00 UTC",
        reaction_time=0.051,
        elapsed_time=6.4,
        total_time=6.451,
        time_to_60=1.02,
        time_to_330=3.2,
        top_speed_mph=198.4,
        red_light=False,
        opponent_car="opponent",
        opponent_total_time=6.8,
        shifts=3,
        perfect_shifts=2,
        perfect_launch=True,
    )
    base.update(overrides)
    return RaceRow(**base)


class LogbookDataTests(unittest.TestCase):
    def test_humanize_does_not_invent_a_driver(self):
        self.assertEqual(humanize_car_id("usa_1"), "USA 1")

    def test_result_labels(self):
        self.assertEqual(result_label("PlayerWon"), "WIN")
        self.assertEqual(result_label("PlayerDisqualified"), "DQ")

    def test_mph_conversion(self):
        self.assertEqual(mph_from_mps(100), 223.69)
        self.assertIsNone(mph_from_mps(-1))

    def test_join_uses_car_from_start(self):
        races = rows_from_query(
            [
                {
                    "event_name": "Play_Mode_Race_Started",
                    "guid": "abc",
                    "car": "snake",
                    "car_level": 2,
                    "race_event": "indy",
                    "raced_at": "2026-09-01 00:00 UTC",
                },
                {
                    "event_name": "Play_Mode_Race_Complete",
                    "guid": "abc",
                    "race_event": "indy",
                    "result": "PlayerLost",
                    "raced_at": "2026-09-01 00:01 UTC",
                    "reaction_time": 0.2,
                    "total_time": 7.1,
                    "time_to_60": 1.2,
                    "top_speed_mps": 80,
                    "red_light": "0",
                },
            ]
        )
        self.assertEqual(len(races), 1)
        self.assertEqual(races[0].car, "snake")
        self.assertEqual(races[0].result, "PlayerLost")
        self.assertEqual(races[0].top_speed_mph, 178.95)

    def test_summary_best_et_is_lowest(self):
        summary = summarize_car(
            [
                _race(total_time=8.2, result="PlayerLost"),
                _race(guid="b", total_time=6.1, result="PlayerWon", top_speed_mph=210),
            ]
        )
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["losses"], 1)
        self.assertEqual(summary["best_et"], 6.1)
        self.assertEqual(summary["best_mph"], 210)

    def test_group_orders_by_race_count(self):
        grouped = group_by_car([_race(car="a"), _race(guid="2", car="b"), _race(guid="3", car="b")])
        self.assertEqual(list(grouped), ["b", "a"])

    def test_record_run_is_a_new_best_et(self):
        slower = _race(raced_at="2026-09-01 01:00 UTC", total_time=8.0)
        quicker = _race(guid="b", raced_at="2026-09-02 01:00 UTC", total_time=6.0)
        tied = _race(guid="c", raced_at="2026-09-03 01:00 UTC", total_time=6.0)
        records = record_runs([quicker, slower, tied], "total_time", lower_is_better=True)
        self.assertEqual([race.guid for race in records], ["g", "b"])

    def test_config_change_between_runs(self):
        marks = config_milestones(
            [
                _race(raced_at="2026-09-01 01:00 UTC", car_level=1, loadout={"Engine": "Blower1"}),
                _race(
                    guid="b",
                    raced_at="2026-09-02 01:00 UTC",
                    car_level=2,
                    loadout={"Engine": "Blower4", "Tire": "Slick2"},
                ),
            ]
        )
        details = [mark.detail for mark in marks]
        self.assertIn("Car level 1 to 2", details)
        self.assertIn("Upgrade Engine to level 4", details)
        self.assertIn("Equip Tire Slick2", details)

    def test_vehicle_body_swap_stays_out_of_the_book(self):
        marks = config_milestones(
            [
                _race(raced_at="2026-09-01 01:00 UTC", loadout={"VehicleBody": "Vehicle_SoxMartin", "Engine": "Blower1"}),
                _race(
                    guid="b",
                    raced_at="2026-09-02 01:00 UTC",
                    loadout={"VehicleBody": "Vehicle_Muldowney1977", "Engine": "Blower4"},
                ),
            ]
        )
        details = [mark.detail for mark in marks]
        self.assertIn("Upgrade Engine to level 4", details)
        self.assertFalse(any("VehicleBody" in detail or detail.startswith("Upgrade Vehicle_") for detail in details))

    def test_milestone_sits_on_its_calendar_day(self):
        start, end = chart_window(today=datetime(2026, 9, 24, tzinfo=timezone.utc))
        self.assertEqual((end, (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days), ("2026-09-24", 59))
        self.assertEqual(calendar_fraction("2026-09-23", start, end), 58 / 59)
        self.assertIsNone(calendar_fraction("2026-07-01", start, end))

    def test_daily_trend_averages_a_day(self):
        points = daily_trend(
            [
                _race(raced_at="2026-09-01 01:00 UTC", total_time=6.0),
                _race(guid="b", raced_at="2026-09-01 02:00 UTC", total_time=8.0),
                _race(guid="c", raced_at="2026-09-02 01:00 UTC", total_time=7.0),
            ],
            "total_time",
        )
        self.assertEqual(points, [("2026-09-01", 7.0), ("2026-09-02", 7.0)])

    def test_daily_win_rate_skips_undecided_races(self):
        points = daily_win_rate(
            [
                _race(raced_at="2026-09-01 01:00 UTC", result="PlayerWon"),
                _race(guid="b", raced_at="2026-09-01 02:00 UTC", result="PlayerLost"),
                _race(guid="c", raced_at="2026-09-01 03:00 UTC", result="PlayerDisqualified"),
                _race(guid="d", raced_at="2026-09-02 01:00 UTC", result="PlayerWon"),
            ]
        )
        self.assertEqual(points, [("2026-09-01", 50.0), ("2026-09-02", 100.0)])

    def test_rendered_page_has_timeslip_and_no_banned_words(self):
        page = render_logbook(
            "device-1",
            "usa_1",
            [_race(), _race(guid="z", car="snake_fc", raced_at="2026-09-24 12:00 UTC", total_time=7.2)],
            [Milestone(car="usa_1", at="2026-09-23 17:00 UTC", detail="Upgrade Engine to level 4")],
        )
        self.assertIn("USA 1", page)
        self.assertNotIn('class="id"', page)
        self.assertNotIn(" RUNS", page)
        self.assertIn("1 RACE", page)
        self.assertIn("100% WINS", page)
        self.assertIn("SNAKE FC", page)
        self.assertIn("/logbook?user_id=device-1&amp;car=snake_fc", page)
        self.assertIn("6.451", page)
        self.assertIn("Saira", page)
        self.assertIn('class="phone"', page)
        self.assertIn("aspect-ratio: 9 / 16", (ROOT / "logbook" / "logbook.css").read_text(encoding="utf-8"))
        self.assertIn('value="et" selected', page)
        self.assertIn('id="raw-data"', page)
        self.assertIn("<summary>Raw Data</summary>", page)
        self.assertIn("Tips from your crew chief", page)
        self.assertIn("One slip in the book, and it was a win", page)
        self.assertIn("Upgrade Engine to level 4", page)
        self.assertIn("class=\"config-row\"", page)
        self.assertNotIn("openRow", page)
        self.assertNotIn("Record ET", page)
        self.assertIn('id="row-', page)
        self.assertEqual(page.count("<svg"), 1)
        self.assertEqual(page.count("<polyline"), 1)
        self.assertIn('"mph"', page)
        self.assertIn(">330-FT<", page)
        self.assertIn(">WIN %<", page)
        self.assertIn("showTrend", page)
        self.assertNotIn("BEST ET", page)
        self.assertNotIn("epic", page.lower())
        pink = render_logbook("device-1", "Vehicle_Muldowney1977", [_race(car="Vehicle_Muldowney1977")])
        self.assertIn("--wash: #4e1436", pink)
        self.assertIn("--car: #e23d8c", pink)
        sox = render_logbook("device-1", "Vehicle_SoxMartin", [_race(car="Vehicle_SoxMartin")])
        self.assertIn("--stripe: #1d4f9a", sox)
        prock = render_logbook("device-1", "Vehicle_AustinProck2025", [_race(car="Vehicle_AustinProck2025")])
        self.assertIn("--stripe: #7eb6ff", prock)
        charger = render_logbook("device-1", "Vehicle_CaliforniaCharger", [_race(car="Vehicle_CaliforniaCharger")])
        self.assertIn("--wash: #0e3a78", charger)
        self.assertIn("--stripe: #f4f7fb", charger)

    def test_driver_page_combines_every_car(self) -> None:
        races = [
            _race(car="Vehicle_SoxMartin", reaction_time=0.201, total_time=8.1),
            _race(car="Vehicle_SoxMartin", reaction_time=0.090, total_time=8.4, result="PlayerLost"),
            _race(
                car="Vehicle_Muldowney1977",
                reaction_time=0.041,
                total_time=4.012,
                top_speed_mph=300.2,
                raced_at="2026-09-23 18:00 UTC",
            ),
        ]
        record = driver_record(races)
        self.assertEqual(record["races"], 3)
        self.assertEqual(record["most_raced_car"], "Vehicle_SoxMartin")
        self.assertEqual(record["most_raced_count"], 2)
        self.assertEqual(record["fastest_rt"], 0.041)
        self.assertEqual(record["fastest_rt_car"], "Vehicle_Muldowney1977")
        page = render_driver("device-1", races)
        self.assertIn("MOST RACED CAR", page)
        self.assertIn("FASTEST RT", page)
        self.assertIn("SOXMARTIN", page)
        self.assertIn("0.041", page)
        self.assertIn(">All cars<", page)
        self.assertIn('href="/logbook?user_id=device-1&car=Vehicle_SoxMartin"', page)
        self.assertNotIn("Hometown", page)
        book = render_logbook("device-1", "Vehicle_Muldowney1977", races)
        self.assertIn('href="/driver?user_id=device-1"', book)
        self.assertIn(">All cars<", book)


class StaticExportTests(unittest.TestCase):
    def test_links_become_files(self) -> None:
        page = (
            '<link rel="stylesheet" href="/logbook.css">'
            '<a href="/">Different id</a>'
            '<a href="/cars?user_id=device-1">All cars</a>'
            '<a href="/logbook?user_id=device-1&amp;car=Vehicle_SoxMartin">Sox</a>'
            '<a href="/driver?user_id=device-1">Driver</a>'
        )
        static = to_static(page)
        self.assertIn('href="logbook.css"', static)
        self.assertIn('href="index.html"', static)
        self.assertIn('href="Vehicle_SoxMartin.html"', static)
        self.assertIn('href="driver.html"', static)
        self.assertNotIn("/logbook?", static)

    def test_garage_honors_vehicle_query(self) -> None:
        page = with_vehicle_redirect('<a class="car-card" href="Vehicle_SoxMartin.html"></a></body>')
        self.assertIn('params.get("vehicle")', page)
        self.assertIn('params.get("car")', page)
        self.assertIn("location.replace", page)


if __name__ == "__main__":
    unittest.main()
