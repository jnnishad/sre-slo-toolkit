import unittest

from slo.multi_window_burn_rate import (
    default_alert_windows,
    evaluate,
    required_burn_rate_for_budget_consumption,
)


class TestRequiredBurnRate(unittest.TestCase):
    def test_reproduces_published_thresholds_for_thirty_day_window(self):
        # These four numbers (14.4, 6, 3, 1) are the exact thresholds
        # published in the SRE Workbook for a 30-day SLO window --
        # this checks the formula derives them, not just that it runs.
        cases = [
            (1.0, 0.02, 14.4),
            (6.0, 0.05, 6.0),
            (24.0, 0.10, 3.0),
            (72.0, 0.10, 1.0),
        ]
        for alert_window_hours, budget_fraction, want in cases:
            got = required_burn_rate_for_budget_consumption(30.0, alert_window_hours, budget_fraction)
            self.assertAlmostEqual(got, want, places=6)

    def test_scales_with_slo_window(self):
        # Halve the SLO window -> half the hours available -> same
        # budget fraction now requires double the burn rate.
        a = required_burn_rate_for_budget_consumption(30.0, 1.0, 0.02)
        b = required_burn_rate_for_budget_consumption(15.0, 1.0, 0.02)
        self.assertAlmostEqual(b, a / 2)


class TestDefaultAlertWindows(unittest.TestCase):
    def test_thresholds_match_sre_workbook(self):
        alerts = default_alert_windows(slo_window_days=30.0)
        thresholds = {a.severity + f"-{a.long_window_hours}h": a.burn_rate_threshold for a in alerts}
        self.assertAlmostEqual(thresholds["page-1.0h"], 14.4)
        self.assertAlmostEqual(thresholds["page-6.0h"], 6.0)
        self.assertAlmostEqual(thresholds["ticket-24.0h"], 3.0)
        self.assertAlmostEqual(thresholds["ticket-72.0h"], 1.0)


class TestEvaluate(unittest.TestCase):
    def test_no_alert_when_below_all_thresholds(self):
        self.assertIsNone(evaluate(long_window_burn_rate=0.5, short_window_burn_rate=0.5))

    def test_pages_when_both_windows_exceed_page_threshold(self):
        alert = evaluate(long_window_burn_rate=20.0, short_window_burn_rate=20.0)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "page")

    def test_short_lived_spike_does_not_page(self):
        # Short window is spiking (would page alone) but the long
        # window hasn't moved -- this is exactly the "noisy blip"
        # multi-window is designed to suppress.
        alert = evaluate(long_window_burn_rate=0.3, short_window_burn_rate=50.0)
        self.assertIsNone(alert)

    def test_ticket_severity_when_only_lower_threshold_met(self):
        # 3.0 clears the ticket-24h threshold but not the page thresholds (6, 14.4).
        alert = evaluate(long_window_burn_rate=3.5, short_window_burn_rate=3.5)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "ticket")

    def test_page_takes_priority_over_ticket_when_both_match(self):
        # A burn rate of 20 clears every threshold in the table at once
        # -- page severity must win, not the first match in list order.
        alert = evaluate(long_window_burn_rate=20.0, short_window_burn_rate=20.0)
        self.assertEqual(alert.severity, "page")


if __name__ == "__main__":
    unittest.main()
