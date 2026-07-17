# Postmortem: Checkout API latency SLO breach

**Status:** Complete
**Date of incident:** 2026-03-12
**Authors:** Jaihind Nishad
**Severity:** SEV2
**Error budget consumed:** ~9% of the 30-day budget for `checkout-api-availability`

> This is a fictional, illustrative postmortem written to demonstrate
> the format and the burn-rate math in `slo/`, not a record of a real
> production incident.

## Summary

A configuration change to the checkout service's HPA (Horizontal Pod
Autoscaler) lowered its max replica count during a routine cleanup of
unused resource quotas. During a normal traffic peak, the service
could not scale out, request queueing pushed p99 latency past the SLO
threshold, and a fraction of checkout requests began timing out and
retrying. Detected by the page-level burn-rate alert (6h/30m windows)
19 minutes after onset; mitigated by reverting the HPA change 11
minutes after acknowledgment.

## Impact

- Elevated error rate on `POST /checkout` for ~30 minutes (peak 4.2%,
  vs. an SLO target of 99.9% success)
- Estimated 1,800 failed checkout attempts (most succeeded on retry)
- Error budget: long-window burn rate hit 6.4x during the incident,
  consuming approximately 9% of the 30-day error budget for this SLO
  in a single 30-minute window

## Timeline

All times UTC.

| Time | Event |
|---|---|
| 14:02 | HPA `maxReplicas` for `checkout-api` reduced from 40 to 12 as part of an unrelated quota cleanup PR |
| 14:41 | Traffic ramps into the daily peak window; pod count hits the new ceiling of 12 |
| 14:47 | Request queue depth climbs; p99 latency crosses the SLO threshold |
| 14:53 | 6h/30m page-level burn-rate alert fires (`evaluate()` returns severity="page") |
| 14:55 | On-call acknowledges, begins investigating recent changes |
| 15:02 | HPA diff identified as the likely cause via `kubectl get hpa -o yaml` + git blame on the manifest |
| 15:04 | `maxReplicas` reverted to 40 |
| 15:06 | Pods scale out; queue depth begins draining |
| 15:13 | Error rate back under threshold; alert auto-resolves |

## Root cause

The HPA `maxReplicas` change was reviewed and merged as part of a
quota-cleanup PR whose stated purpose was removing *unused* headroom.
`checkout-api`'s actual peak replica count (recorded in its dashboard,
not in the manifest or PR description) was 28-34 during daily peak --
higher than the reviewer's assumption. The trigger was the daily
traffic peak; the root cause is that peak capacity requirements for
this service lived only in a dashboard, not anywhere the PR's reviewer
would naturally check before approving a "safe-looking" quota change.

## What went well

- The multi-window burn-rate alert fired quickly (19 minutes from
  onset to page) and did not false-positive during the ramp-up before
  the actual threshold breach.
- Root cause was identified fast once paged -- `git blame` on the HPA
  manifest immediately surfaced the same-day change.

## What went poorly

- No automated check compared a proposed `maxReplicas` value against
  recent observed peak replica count before merge.
- The PR reviewer had no easy way to see "this service peaks at 30+
  replicas" without separately knowing to check a dashboard.

## Where we got lucky

The change merged mid-morning, several hours before the daily peak --
if it had merged 30 minutes before peak, detection-to-mitigation would
have overlapped with peak traffic for longer, increasing impact.

## Action items

| Action | Owner | Priority | Ticket |
|---|---|---|---|
| Add a CI check that fails a PR reducing `maxReplicas` below the 7-day p95 observed replica count | Platform team | P1 | INFRA-1042 |
| Add current peak replica count as a comment in the HPA manifest itself, next to `maxReplicas` | Platform team | P2 | INFRA-1043 |
| Lower the page-level alert window from 30m short-window to 15m to shave detection time further | SRE | P2 | INFRA-1044 |
