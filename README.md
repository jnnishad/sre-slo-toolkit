# sre-slo-toolkit

SLO error-budget math, multi-window burn-rate alerting, incident
runbooks, and a blameless postmortem template — the on-call/SRE half
of a senior DevOps role, as opposed to the infrastructure-provisioning
half covered by the rest of [this profile](https://github.com/jnnishad).

## Why this exists

Terraform/Ansible/Kubernetes repos show you can *build* a platform.
This repo is about what happens once it's running: how you decide
something is broken badly enough to page a human (not just "an error
happened somewhere"), and how you write up what happened afterward in
a way that produces fixes instead of blame.

## `slo/` — the math

Implements the alerting strategy from Google's SRE Workbook, ["Alerting
on SLOs"](https://sre.google/workbook/alerting-on-slos/):

- **`error_budget.py`** — given an SLO target (e.g. 99.9%) and observed
  good/total request counts, computes burn rate and remaining budget.
- **`multi_window_burn_rate.py`** — the multi-window, multi-burn-rate
  alert table. A single-window alert is either too slow (long window)
  or too noisy (short window); this requires *both* a long window
  (confidence it's real) and a short window (fast reset) to
  independently breach a threshold before paging.

`test_multi_window_burn_rate.py` doesn't just check the code runs — it
asserts the derived thresholds (14.4x, 6x, 3x, 1x) exactly match the
published SRE Workbook table for a 30-day SLO window, since those
numbers are the actual point of this module.

```bash
python3 -m unittest discover -s slo/tests -t . -v
```

All 21 tests pass (verified by actually running `unittest` — not
hand-traced, unlike the Go repos in this profile where no Go toolchain
was available to compile against).

## `runbooks/` — what to do when it fires

Two runbooks (`high-error-rate.md`, `node-not-ready.md`) written the
way I'd want to read one at 2am: confirm-it's-real first, check recent
changes before anything exotic, mitigate before root-causing. Backed by
`runbooks/scripts/check_error_rate.py`, a small CLI that plugs
good/total counts from whatever metrics backend you have into the
`slo/` package and prints a page/ticket/OK verdict.

```bash
python3 runbooks/scripts/check_error_rate.py \
  --long-good 985600 --long-total 1000000 \
  --short-good 8560  --short-total 10000
# -> long-window burn rate:  14.40x
# -> short-window burn rate: 144.00x
# -> verdict: PAGE (threshold 6.00x over 6.0h/0.5h windows)
```

## `postmortems/` — after it's fixed

`TEMPLATE.md` is a blameless postmortem template. `example-2026-03-12-checkout-latency.md`
is a filled, fictional example (an HPA `maxReplicas` misconfiguration)
showing what "good" looks like: a timeline reconstructed from actual
alert/action timestamps, root cause separated from trigger, and action
items that are independently valuable rather than one vague
"improve monitoring" catch-all.

## Structure

```
slo/
  error_budget.py               SLO, burn_rate(), error_budget_remaining()
  multi_window_burn_rate.py     the alert table + evaluate()
  tests/                        21 unittest cases, run and passing
runbooks/
  high-error-rate.md
  node-not-ready.md
  scripts/check_error_rate.py   CLI wrapping slo/ for on-call use
postmortems/
  TEMPLATE.md
  example-2026-03-12-checkout-latency.md
```

<!-- test commit 2026-02-16T18:04:06 -->

<!-- test commit 2026-01-31T03:21:01 -->

<!-- test commit 2026-06-10T20:45:10 -->

<!-- test commit 2026-06-11T19:51:16 -->

<!-- JN -->

<!-- JN -->

<!-- JN -->

<!-- JN -->

<!-- JN -->
