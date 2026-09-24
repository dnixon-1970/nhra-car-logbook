<!-- Save as Documents/plans/YYYYMMDD_<topic>_review.md
     Output format for a cross-model review (of a plan OR of a diff).
     The reviewer produces everything below the fix ledger; the author
     prepends the fix ledger after addressing findings. -->

# <Topic> <plan|diff> review — <reviewer model>

**Assessment**: <APPROVE | APPROVE WITH FIXES | REQUEST CHANGES>

**Status (YYYY-MM-DD, post-review)**: <Fix ledger — prepended by the author
after addressing findings. One line per finding, mapping it to its resolution:>

- **SEVERE-1** (<short name>) — fixed at `<file:line>`: <what changed>.
- **MODERATE-1** (<short name>) — declined: <why, explicitly>.
- **LOW-1** (<short name>) — <resolution>.

## Executive summary

<2-3 paragraphs: does the work match its stated intent; what class the
remaining issues fall into (blockers vs validation-quality gaps vs polish).>

## CRITICAL findings

<Deploy-blockers / correctness failures. "None." is a fine answer.
Each finding: `file:line` reference — the issue — why it matters — a concrete
alternative — and an explicit tag: Evidence-backed or Conjecture.>

## SEVERE findings

## MODERATE findings

## LOW findings

## Approved / not-a-finding notes

<Things checked and found sound — so the author knows what was verified, not
just what failed. E.g. "verified X does not reach persisted schema", "the
focused test subset passed: N selected, N passed".>
