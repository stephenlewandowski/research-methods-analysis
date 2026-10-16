"""Verify both teaching examples with Python's standard library (Python 3.10+).

No SPSS installation or third-party package is needed. Run without arguments to
check the committed reference values and the agreement of CSV and inline data.
--write regenerates expected_results.json after an intentional dataset change.
These calculations are an independent numerical reference, not SPSS output.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent


def _beta_fraction(a: float, b: float, x: float) -> float:
    """Modified Lentz evaluation of the incomplete-beta continued fraction."""
    tiny = 1e-300
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    value = d
    for m in range(1, 501):
        even = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        odd = -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))
        for coefficient in (even, odd):
            d = 1.0 + coefficient * d
            if abs(d) < tiny:
                d = tiny
            c = 1.0 + coefficient / c
            if abs(c) < tiny:
                c = tiny
            d = 1.0 / d
            change = d * c
            value *= change
        if abs(change - 1.0) < 3e-14:
            return value
    raise ArithmeticError("Incomplete-beta continued fraction did not converge")


def regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    factor = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                      + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * _beta_fraction(a, b, x) / a
    return 1.0 - factor * _beta_fraction(b, a, 1.0 - x) / b


def two_sided_p(t: float, df: float) -> float:
    return regularized_beta(df / (df + t * t), df / 2.0, 0.5)


def t_critical_95(df: float) -> float:
    lo, hi = 0.0, 1.0
    while two_sided_p(hi, df) > 0.05:
        hi *= 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if two_sided_p(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def descriptives(values: list[float]) -> dict:
    return {
        "n": len(values), "mean": statistics.mean(values),
        "sd": statistics.stdev(values),
        "sem": statistics.stdev(values) / math.sqrt(len(values)),
        "min": min(values), "max": max(values),
    }


def test_result(difference: float, se: float, df: float) -> dict:
    t = difference / se
    margin = t_critical_95(df) * se
    return {
        "mean_difference": difference, "se_difference": se, "t": t,
        "df": df, "p_two_sided": two_sided_p(t, df),
        "ci95_lower": difference - margin, "ci95_upper": difference + margin,
    }


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def assert_inline_matches(csv_path: Path, syntax_path: Path) -> None:
    rows = read_rows(csv_path)
    columns = list(rows[0])
    expected = [[float(row[column]) for column in columns] for row in rows]
    syntax = syntax_path.read_text(encoding="utf-8")
    block = re.search(r"BEGIN DATA\s*\n(.*?)\nEND DATA\.", syntax,
                      flags=re.IGNORECASE | re.DOTALL)
    if block is None:
        raise AssertionError(f"No inline data in {syntax_path.name}")
    actual = [[float(value) for value in line.split()]
              for line in block.group(1).strip().splitlines()]
    if actual != expected:
        raise AssertionError(f"Inline data differ from {csv_path.name}")


def calculate() -> dict:
    independent_csv = HERE.parent / "ramp_hazard_training.csv"
    paired_csv = HERE / "ramp_hazard_paired.csv"
    assert_inline_matches(independent_csv, HERE.parent / "ramp_hazard_training.sps")
    assert_inline_matches(paired_csv, HERE / "ramp_hazard_paired.sps")

    original = read_rows(independent_csv)
    if len({row["worker_id"] for row in original}) != len(original):
        raise AssertionError("Independent worker IDs must be unique")
    if len(original) != 40 or {row["training"] for row in original} != {"1", "2"}:
        raise AssertionError("Expected the original 40-worker independent study")
    groups = [[float(row["report_seconds"]) for row in original
               if row["training"] == group] for group in ("1", "2")]
    group_stats = [descriptives(group) for group in groups]
    variance_parts = [s["sd"] ** 2 / s["n"] for s in group_stats]
    welch_se = math.sqrt(sum(variance_parts))
    welch_df = sum(variance_parts) ** 2 / sum(
        v ** 2 / (s["n"] - 1) for v, s in zip(variance_parts, group_stats))
    welch = test_result(group_stats[0]["mean"] - group_stats[1]["mean"],
                        welch_se, welch_df)

    paired = read_rows(paired_csv)
    ids = [int(row["worker_id"]) for row in paired]
    if len(paired) != 20 or len(set(ids)) != 20 or set(ids) & {
        int(row["worker_id"]) for row in original
    }:
        raise AssertionError("Expected 20 new and uniquely identified matched workers")
    before = [float(row["before_seconds"]) for row in paired]
    after = [float(row["after_seconds"]) for row in paired]
    if any(not math.isfinite(value) or value <= 0 for value in before + after):
        raise AssertionError("All times must be complete, finite, positive seconds")
    differences = [b - a for b, a in zip(before, after)]
    before_stats, after_stats = descriptives(before), descriptives(after)
    diff_stats = descriptives(differences)
    r = statistics.correlation(before, after)
    variance_identity = before_stats["sd"] ** 2 + after_stats["sd"] ** 2 - (
        2 * r * before_stats["sd"] * after_stats["sd"])
    if not math.isclose(variance_identity, diff_stats["sd"] ** 2, abs_tol=1e-10):
        raise AssertionError("Paired variance identity failed")
    return {
        "schema_version": 1,
        "provenance": "Independent standard-library calculations; not native SPSS output",
        "units": "seconds",
        "independent": {
            "source": "../ramp_hazard_training.csv",
            "difference_order": "standard_briefing_minus_scenario_practice",
            "standard_briefing": group_stats[0],
            "scenario_practice": group_stats[1], "welch": welch,
        },
        "paired": {
            "source": "ramp_hazard_paired.csv", "complete_pairs": len(paired),
            "difference_order": "before_minus_after", "before": before_stats,
            "after": after_stats, "differences": diff_stats,
            "before_after_correlation": r,
            "correlation_p_two_sided": two_sided_p(
                r * math.sqrt((len(paired) - 2) / (1 - r * r)), len(paired) - 2),
            "test": test_result(diff_stats["mean"], diff_stats["sem"], len(paired) - 1),
            "faster_after_count": sum(d > 0 for d in differences),
            "slower_after_count": sum(d < 0 for d in differences),
            "unchanged_count": sum(d == 0 for d in differences),
            "sd_difference_from_covariance_identity": math.sqrt(variance_identity),
            "se_if_covariance_term_omitted_for_teaching_only": math.sqrt(
                (before_stats["sd"] ** 2 + after_stats["sd"] ** 2) / len(paired)),
        },
    }


def compare(expected, actual, location="results") -> None:
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            raise AssertionError(f"Different fields at {location}")
        for key in expected:
            compare(expected[key], actual[key], f"{location}.{key}")
    elif isinstance(expected, (float, int)) and not isinstance(expected, bool):
        if not math.isclose(expected, actual, rel_tol=1e-10, abs_tol=1e-10):
            raise AssertionError(f"{location}: expected {expected}, got {actual}")
    elif expected != actual:
        raise AssertionError(f"{location}: expected {expected}, got {actual}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="regenerate the committed numerical reference")
    args = parser.parse_args()
    # Elementary reference checks independent of the dataset calculations.
    for value in (0.0, 0.5, 1.0, 3.0):
        cauchy_p = 1.0 - 2.0 * math.atan(abs(value)) / math.pi
        assert math.isclose(two_sided_p(value, 1), cauchy_p, abs_tol=1e-12)
    result = calculate()
    target = HERE / "expected_results.json"
    if args.write:
        target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                          encoding="utf-8")
        print(f"Wrote {target.name}")
    else:
        compare(json.loads(target.read_text(encoding="utf-8")), result)
        print("PASS: CSV/inline data, expected statistics, complete pairs, variance identity")
    for name, test in (("Welch", result["independent"]["welch"]),
                       ("Paired", result["paired"]["test"])):
        print(f"{name}: t({test['df']:.6f})={test['t']:.9f}, "
              f"p={test['p_two_sided']:.12g}, "
              f"95% CI [{test['ci95_lower']:.9f}, {test['ci95_upper']:.9f}] s")


if __name__ == "__main__":
    main()
