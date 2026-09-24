<!-- Save as Documents/decisions/YYYYMMDD_<topic>.md
     A decision doc is for "we considered X, picked Y, here's why" notes too
     detailed for a commit message but not big enough for a plan. It is a
     historical record + binding-for-now: don't re-litigate without explicit
     reason. -->

# Decision — <imperative one-liner: what was decided>

**Date**: YYYY-MM-DD
**Scope**: <the surfaces/files this decision governs>
**Ticket**: <TICKET-ID, if any>
**Status**: <Decided | Shipped in <PR/commit> | Superseded by <link>>

## Problem

<What forced a choice. The observed failure, feedback, or fork in the road —
concrete, with dates/numbers where they exist.>

## Considered

<The options, each with its trade-off in a sentence or two. A table works well
when there are 3+ options:>

| Option | Trade-off | Verdict |
|---|---|---|
| <A> | <cost/benefit> | <adopted / rejected because…> |

## Chose

<The option picked, and its exact shape — constants chosen, semantics pinned,
invariants that must hold going forward.>

## Why

<The reasoning, ideally derived from independently-observable facts rather than
taste. If a number was chosen, show the derivation. If a reviewer or incident
surfaced a consequence that shaped the choice, credit it.>

## Re-evaluation trigger (optional)

<The pre-committed condition under which this decision should be revisited.
Not a task — a tripwire.>
