# Decision — Logbook identity and telemetry source

**Date**: 2026-09-24  
**Scope**: `tools/logbook_data.py`, the lookup form  
**Ticket**: none  
**Status**: Decided

## Problem

A Firebase Auth uid was the first id tried against production telemetry. It is not what NHRA writes into Analytics.

## Chose

The form takes the Concrete Device ID. Queries hit `nhra-64ac5.analytics_490826646` for the last 60 days. Car identity comes from `Play_Mode_Race_Started.car`, joined to `Play_Mode_Race_Complete` on `GUID`. The trend chart spans the days that car actually raced.

## Why

`FirebaseAnalytics.SetUserID` is called with `ConcreteDeviceID`. Race complete events do not include the car. Both facts were confirmed in `#data-analysis-assistant` on 2026-09-24 and in `AnalyticsGameplayEvents.cs`.

## Re-evaluation trigger

If the game starts sending the Auth uid as `user_id`, or if race complete gains its own `car` field, update `Knowledge Packs/race-telemetry.md` before changing the join.
