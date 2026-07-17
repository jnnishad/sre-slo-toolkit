# Postmortem: <title>

**Status:** Draft / In Review / Complete
**Date of incident:** YYYY-MM-DD
**Authors:** 
**Severity:** SEV1 / SEV2 / SEV3
**Error budget consumed:** <fraction>% of the <window>-day budget for <SLO name>

> This document is blameless. The goal is to understand what happened
> and reduce the chance of recurrence — not to assign fault. If a
> section reads like it's building a case against a person, rewrite it
> around the system and decision context instead.

## Summary

Two or three sentences: what broke, user impact, how long, how it was
resolved. Someone who wasn't on the call should understand the shape
of the incident from this paragraph alone.

## Impact

- User-facing impact (error rate, latency, feature unavailability)
- Duration
- Number of requests/users affected (estimate is fine)
- Error budget consumed (use `slo.error_budget.burn_rate` against the
  actual good/total counts for the incident window)

## Timeline

All times in UTC.

| Time | Event |
|---|---|
| HH:MM | First anomaly (from monitoring, not necessarily when noticed) |
| HH:MM | Alert fired / paged |
| HH:MM | Acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Confirmed resolved |

## Root cause

What actually caused this, at the level of "if this specific thing
hadn't happened, the incident wouldn't have." Distinguish the trigger
(what set it off) from the root cause (why the system was vulnerable
to that trigger at all).

## What went well

- 

## What went poorly

- 

## Where we got lucky

Things that limited the blast radius but weren't the result of
deliberate design — call these out explicitly so they turn into real
fixes instead of remaining implicit assumptions.

- 

## Action items

| Action | Owner | Priority | Ticket |
|---|---|---|---|
|  |  | P0/P1/P2 |  |

Every action item should be independently valuable even if none of the
others get done — no "fix the whole alerting pipeline" mega-items that
never close.
