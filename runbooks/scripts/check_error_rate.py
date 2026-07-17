#!/usr/bin/env python3
"""CLI that evaluates the current burn rate against the multi-window
alert table and prints the verdict a runbook step would act on.

Designed to be fed by whatever your metrics backend is -- Prometheus,
CloudWatch, Mimir -- via the --good/--total flags computed from your
own query. Kept decoupled from any specific metrics client so it has
zero external dependencies and is easy to wire into any pipeline:

    good=$(promql_query 'sum(rate(http_requests_total{code!~"5.."}[1h]))')
    total=$(promql_query 'sum(rate(http_requests_total[1h]))')
    check_error_rate.py --slo-target 0.999 \\
        --long-good "$good_1h" --long-total "$total_1h" \\
        --short-good "$good_5m" --short-total "$total_5m"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from slo.error_budget import SLO, burn_rate
from slo.multi_window_burn_rate import evaluate


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slo-target", type=float, default=0.999, help="e.g. 0.999 for three nines (default: %(default)s)")
    p.add_argument("--slo-window-days", type=float, default=30.0, help="default: %(default)s")
    p.add_argument("--long-good", type=int, required=True)
    p.add_argument("--long-total", type=int, required=True)
    p.add_argument("--short-good", type=int, required=True)
    p.add_argument("--short-total", type=int, required=True)
    return p


def run(args) -> int:
    slo = SLO(target=args.slo_target, window_days=args.slo_window_days)

    long_rate = burn_rate(slo, args.long_good, args.long_total)
    short_rate = burn_rate(slo, args.short_good, args.short_total)

    alert = evaluate(long_rate, short_rate)

    print(f"long-window burn rate:  {long_rate:.2f}x")
    print(f"short-window burn rate: {short_rate:.2f}x")

    if alert is None:
        print("verdict: OK -- no threshold breached")
        return 0

    print(f"verdict: {alert.severity.upper()} "
          f"(threshold {alert.burn_rate_threshold:.2f}x over "
          f"{alert.long_window_hours}h/{alert.short_window_hours}h windows)")
    return 1 if alert.severity == "page" else 2


def main() -> None:
    args = build_parser().parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
