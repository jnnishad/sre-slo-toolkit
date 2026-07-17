# Runbook: High error rate / burn-rate alert paged

**Triggered by:** multi-window burn-rate alert (see `slo/multi_window_burn_rate.py`)
**Severity:** page or ticket, per the alert that fired

## 1. Confirm it's real

Multi-window alerting already filters out short blips, but confirm
against the dashboard before doing anything disruptive:

```bash
python3 runbooks/scripts/check_error_rate.py \
  --slo-target 0.999 \
  --long-good <good_count_long_window> --long-total <total_count_long_window> \
  --short-good <good_count_short_window> --short-total <total_count_short_window>
```

If both windows independently confirm the burn rate, proceed. If only
one window is elevated, it may resolve on its own — watch for 5
minutes before escalating.

## 2. Check recent changes first

Most incidents are caused by something that changed recently, not a
random hardware failure. In order:

```bash
kubectl rollout history deployment/<service> -n <namespace>
git log --since="2 hours ago" -- manifests/<service>/
```

If a deploy or config change correlates with the onset time, that's
your leading hypothesis. **Roll it back before continuing to
investigate root cause** — restoring service comes first, understanding
why comes second (that's what the postmortem is for).

## 3. If nothing recent changed

- Check dependency health: is a downstream service (database, external
  API) degraded? `kubectl get pods -n <namespace>` for crash loops,
  check the dependency's own dashboards.
- Check resource saturation: `kubectl top pods -n <namespace>`, HPA
  status (`kubectl get hpa -n <namespace>`) — is the service pinned at
  `maxReplicas` under load it can't handle?
- Check for a traffic anomaly: is this a real spike, a retry storm from
  a struggling downstream client, or a bot/scraper pattern?

## 4. Mitigate

Prefer the fastest safe path back to healthy over the most elegant fix:

- Roll back a bad deploy
- Scale out manually if HPA is capped (`kubectl scale deployment/<service> --replicas=N`)
- Shed load (feature-flag off a non-critical path) if the system is
  genuinely overloaded and nothing else is faster

## 5. After mitigation

- Confirm the alert clears (`check_error_rate.py` shows `OK`)
- If severity was `page`, or if error budget consumption was
  significant, open a postmortem from `postmortems/TEMPLATE.md`
