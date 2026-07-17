"""Error budget and burn-rate math for SLO-based alerting.

Core reference: Google's SRE Workbook, "Alerting on SLOs"
https://sre.google/workbook/alerting-on-slos/
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SLO:
    """A single SLO, e.g. 99.9% of requests succeed over a 30-day window."""

    target: float
    window_days: float = 30.0

    def __post_init__(self) -> None:
        if not 0 < self.target < 1:
            raise ValueError(f"target must be between 0 and 1 (exclusive), got {self.target}")
        if self.window_days <= 0:
            raise ValueError(f"window_days must be positive, got {self.window_days}")

    @property
    def allowed_error_ratio(self) -> float:
        """Fraction of requests allowed to fail without breaching the SLO."""
        return 1 - self.target

    @property
    def error_budget_minutes(self) -> float:
        """Total downtime budget across the window, in minutes."""
        return self.window_days * 24 * 60 * self.allowed_error_ratio


def _observed_error_ratio(good_count: int, total_count: int) -> float:
    if total_count < 0 or good_count < 0:
        raise ValueError("counts must be non-negative")
    if good_count > total_count:
        raise ValueError("good_count cannot exceed total_count")
    if total_count == 0:
        return 0.0
    bad_count = total_count - good_count
    return bad_count / total_count


def burn_rate(slo: SLO, good_count: int, total_count: int) -> float:
    """How many times faster than sustainable the error budget is being
    consumed.

    A burn rate of 1.0 means "exactly on pace to exhaust the budget by
    the end of the window." A burn rate of 14.4 means the budget would
    be exhausted in window_days / 14.4 -- for a 30-day window that's
    exactly 50 hours ~= 1 hour of a 30-day/99.9% budget, which is why
    14.4 is the page-level threshold in Google's default alert table.
    """
    if total_count == 0:
        return 0.0
    observed = _observed_error_ratio(good_count, total_count)
    if slo.allowed_error_ratio == 0:
        return float("inf") if observed > 0 else 0.0
    return observed / slo.allowed_error_ratio


def error_budget_remaining(slo: SLO, good_count: int, total_count: int) -> float:
    """Fraction of the error budget remaining.

    1.0 = no errors consumed yet. 0.0 = budget exactly exhausted.
    Negative = the SLO has already been breached for this window.
    """
    if total_count == 0:
        return 1.0
    return 1 - burn_rate(slo, good_count, total_count)
