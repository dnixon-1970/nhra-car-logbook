<!-- Save as Documents/plans/YYYYMMDD_<topic>.plan.md -->

# <Topic> — <one-line summary of the change> (<TICKET-ID>)

- **Date**: YYYY-MM-DD
- **Status**: Draft | Reviewed (link the review doc + verdict) | In implementation | Shipped
- **Ticket(s)**: <TICKET-ID + link>
- **Branch**: `<ticket-id>-<short-description>`
- **Author / Reviewer**: <primary model or person> / <cross-model reviewer>
- **Depends on / Sibling to**: <links to related plans, if any>
- **Motivation**: <2-4 sentences: the pain, ideally with the user's own words or a concrete observed failure. Why now.>
- **Decision**: <1-3 sentences: the chosen approach, and its phasing if phased.>

---

## 0. Onboarding for a fresh agent

<!-- Numbered reading list so a different model/session can implement with zero
     conversation context. Include: repo AGENTS.md, this plan, the review doc,
     the relevant insight docs (the pain being fixed), the current code to read,
     any external contracts consumed, and any hard freezes/timing constraints. -->

1. **Repo onboarding**: `AGENTS.md` at repo root.
2. **This plan** — source of truth for the design. Decisions in §1 were confirmed by the operator; do not re-litigate. Then read the review + fixes ledger at `<review doc>`.
3. **The pain being fixed**: <insight/decision docs>.
4. **Current code**: <files to read in full>.
5. **External contracts**: <what consumes the surfaces being changed, in which repo (read-only)>.
6. **Hard freeze / timing**: <anything that must not be disturbed, and until when>.

## 1. Scope

**In scope**: <bulleted, per surface/phase>.

**Out of scope / follow-ups**: <explicitly named non-goals, each with where it's tracked instead. Naming what you're NOT doing is what prevents scope creep during implementation.>

## 2. The visual / UX story (if applicable)

<!-- Before → after for each user-visible surface. What the user sees today,
     what they'll see after, and what they can now do at a glance. -->

## 3. Surface-by-surface changes

<!-- One subsection per file/component. For each: current behavior, proposed
     behavior (with code sketches where load-bearing), edge cases named
     explicitly. Include the tests subsection - which test files, which cases. -->

### 3.1 `<file>`
### 3.2 `<file>`
### 3.x Tests

## 4. Cross-cutting concerns

<!-- Schema/fingerprint/version-pin impacts, backward compatibility with
     in-flight producers/consumers, cross-repo contract implications, skew
     windows if multiple repos are touched (see cross-repo-merge-order). -->

## 5. Rollout

<!-- Numbered steps: land order (one commit? paired PRs in which order?),
     seed/migration steps or an explicit "no seed step", deploy target,
     the acceptance signal ("the next scheduled run shows X"). -->

## 6. Rollback

<!-- What reverting looks like; whether the change is forward/backward
     compatible; any data-migration implications of rolling back. -->

## 7. Related work

<!-- Links: sibling plans, the tickets, prior decisions this builds on. -->

## 8. Open decisions

<!-- Anything genuinely unresolved, each with its options and a recommendation.
     Empty is a fine (good) state - say "None". -->
