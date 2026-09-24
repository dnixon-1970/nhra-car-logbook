# Race telemetry for the logbook

Production export: `nhra-64ac5.analytics_490826646.events_*`.

Confirmed in Slack on 2026-09-24 (`#data-analysis-assistant`) and in `unity-nhra` `AnalyticsGameplayEvents.cs`.

## Which id

| Id | In the logbook? |
|---|---|
| Concrete Device ID | Yes. This is Analytics `user_id`. |
| Firebase Auth uid (`gondorUserId`) | No. Not written to Analytics. |
| `user_pseudo_id` | Install id only. Not the form field. |

`SetUserId` is called with `ConcreteIDs.ConcreteDeviceID`. Dev builds (`com.concretesoftware.dragracingcar`) export to `nhra-dev-f81f2`, which this prototype does not query.

## Join

`Play_Mode_Race_Complete` does not carry `car`. Take `car` and `carLevel` from `Play_Mode_Race_Started` with the same `GUID`.

Finish fields used on the timeslip: `result`, `raceEvent`, `reactionTime`, `elapsedTime`, `totalTime`, `timeTo60Feet`, `timeTo330Feet`, `topSpeedMetersPerSecond`, `redLight`, `opponentCar`, `shifts`, `perfectShifts`, `perfectLaunchTiming`.

`result` values seen in code: `PlayerWon`, `PlayerLost`, `PlayerQuit`, `PlayerDisqualified`, `MidRace`.

Speed is stored in meters per second. The page converts to mph in Python.
