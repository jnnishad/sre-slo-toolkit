"""Multi-window, multi-burn-rate alerting -- the alerting strategy from
Google's SRE Workbook (ch. 5, "Alerting on SLOs").

The problem with a single-window burn-rate alert: a short window pages
on any brief blip (noisy), a long window takes hours to notice a real
outage (slow). The fix is requiring *both* a long window (confidence
that this is real, not a blip) and a short window (fast reset -- once
the short window recovers, the page clears quickly even while the long
window is still catching up) to independently exceed the threshold.
"""
from dataclasses import dataclass
from typing import List, Optional

_SEVERITY_ORDER = {"page": 0, "ticket": 1}


@dataclass(frozen=True)
class BurnRateAlert:
    severity: str  # "page" or "ticket"
    long_window_hours: float
    short_window_hours: float
    burn_rate_threshold: float
    budget_consumed_if_sustained: float  # fraction of the SLO window's budget


def required_burn_rate_for_budget_consumption(
    slo_window_days: float, alert_window_hours: float, budget_fraction: float
) -> float:
    """What burn rate, sustained for exactly alert_window_hours, would
    consume budget_fraction of the total slo_window_days error budget?

    Derivation: consuming the whole budget takes slo_window_hours at
    burn rate 1.0. Consuming budget_fraction of it in alert_window_hours
    requires:

        burn_rate * alert_window_hours = budget_fraction * slo_window_hours
        burn_rate = budget_fraction * slo_window_hours / alert_window_hours
    """
    slo_window_hours = slo_window_days * 24
    return budget_fraction * slo_window_hours / alert_window_hours


def default_alert_windows(slo_window_days: float = 30.0) -> List[BurnRateAlert]:
    """The alert table from the SRE Workbook, generalized to any SLO
    window via required_burn_rate_for_budget_consumption -- for the
    standard 30-day window this reproduces the book's published
    thresholds (14.4, 6, 3, 1) exactly.
    """
    specs = [
        ("page", 1.0, 1.0 / 12.0, 0.02),
        ("page", 6.0, 0.5, 0.05),
        ("ticket", 24.0, 2.0, 0.10),
        ("ticket", 72.0, 6.0, 0.10),
    ]
    return [
        BurnRateAlert(
            severity=severity,
            long_window_hours=long_h,
            short_window_hours=short_h,
            burn_rate_threshold=required_burn_rate_for_budget_consumption(
                slo_window_days, long_h, budget_fraction
            ),
            budget_consumed_if_sustained=budget_fraction,
        )
        for severity, long_h, short_h, budget_fraction in specs
    ]


def evaluate(
    long_window_burn_rate: float,
    short_window_burn_rate: float,
    alerts: Optional[List[BurnRateAlert]] = None,
) -> Optional[BurnRateAlert]:
    """Return the highest-severity alert that should fire, or None.

    Both windows must independently exceed the threshold -- that's the
    "multi-window" part. A short-lived spike that hasn't dragged the
    long-window average up yet does not page.
    """
    if alerts is None:
        alerts = default_alert_windows()

    candidates = [
        a
        for a in alerts
        if long_window_burn_rate >= a.burn_rate_threshold
        and short_window_burn_rate >= a.burn_rate_threshold
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda a: _SEVERITY_ORDER[a.severity])
