import unittest

from slo.error_budget import SLO, burn_rate, error_budget_remaining


class TestSLO(unittest.TestCase):
    def test_invalid_target_rejected(self):
        for bad in (0, 1, -0.1, 1.5):
            with self.assertRaises(ValueError):
                SLO(target=bad)

    def test_invalid_window_rejected(self):
        with self.assertRaises(ValueError):
            SLO(target=0.999, window_days=0)

    def test_allowed_error_ratio(self):
        self.assertAlmostEqual(SLO(target=0.999).allowed_error_ratio, 0.001)
        self.assertAlmostEqual(SLO(target=0.99).allowed_error_ratio, 0.01)

    def test_error_budget_minutes_for_three_nines_thirty_days(self):
        slo = SLO(target=0.999, window_days=30)
        # 30 days * 24h * 60m * 0.001 = 43.2 minutes
        self.assertAlmostEqual(slo.error_budget_minutes, 43.2)


class TestBurnRate(unittest.TestCase):
    def test_zero_errors_is_zero_burn(self):
        slo = SLO(target=0.999, window_days=30)
        self.assertEqual(burn_rate(slo, good_count=1000, total_count=1000), 0.0)

    def test_on_pace_burn_rate_is_one(self):
        slo = SLO(target=0.999, window_days=30)
        # 1 bad out of 1000 = 0.1% error rate = exactly the allowed ratio
        self.assertAlmostEqual(burn_rate(slo, good_count=999, total_count=1000), 1.0)

    def test_page_threshold_burn_rate(self):
        slo = SLO(target=0.999, window_days=30)
        # 144 bad out of 10000 = 1.44% error rate = 14.4x the 0.1% budget
        self.assertAlmostEqual(burn_rate(slo, good_count=9856, total_count=10000), 14.4)

    def test_no_traffic_is_zero_burn(self):
        slo = SLO(target=0.999, window_days=30)
        self.assertEqual(burn_rate(slo, good_count=0, total_count=0), 0.0)

    def test_good_exceeds_total_raises(self):
        slo = SLO(target=0.999, window_days=30)
        with self.assertRaises(ValueError):
            burn_rate(slo, good_count=10, total_count=5)


class TestErrorBudgetRemaining(unittest.TestCase):
    def test_no_errors_full_budget_remaining(self):
        slo = SLO(target=0.999, window_days=30)
        self.assertAlmostEqual(error_budget_remaining(slo, 1000, 1000), 1.0)

    def test_exactly_on_pace_zero_remaining(self):
        slo = SLO(target=0.999, window_days=30)
        self.assertAlmostEqual(error_budget_remaining(slo, 999, 1000), 0.0)

    def test_over_budget_is_negative(self):
        slo = SLO(target=0.999, window_days=30)
        # 20 bad out of 1000 = 2% error rate = 20x the 0.1% budget -> remaining = 1 - 20 = -19
        self.assertAlmostEqual(error_budget_remaining(slo, 980, 1000), -19.0)

    def test_no_traffic_full_budget_remaining(self):
        slo = SLO(target=0.999, window_days=30)
        self.assertEqual(error_budget_remaining(slo, 0, 0), 1.0)


if __name__ == "__main__":
    unittest.main()
