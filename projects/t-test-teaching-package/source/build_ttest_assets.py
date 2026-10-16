"""Generate the synthetic teaching observations and Welch-test assets."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats


PACKAGE_DIR = Path(__file__).resolve().parent.parent


def sample(n, mean, sd, seed):
    # Engineered synthetic samples: exact teaching means/SD, no real workers.
    rng = np.random.default_rng(seed)
    z = rng.normal(size=n)
    z = (z - z.mean()) / z.std(ddof=1)
    return mean + sd * z


def build_assets(output_dir):
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    source_out = out / "source"
    source_out.mkdir(parents=True, exist_ok=True)
    scenarios = {}
    for key, n, gap, sd in [
        ("baseline", 20, 6, 8),
        ("gap", 20, 12, 8),
        ("scatter", 20, 6, 14),
        ("size", 80, 6, 14),
    ]:
        a = sample(n, 48, sd, 246)
        b = sample(n, 48 - gap, sd, 739)
        assert min(a.min(), b.min()) > 0
        v1, v2 = a.var(ddof=1) / n, b.var(ddof=1) / n
        se = np.sqrt(v1 + v2)
        df = (v1 + v2) ** 2 / (v1 * v1 / (n - 1) + v2 * v2 / (n - 1))
        t = (a.mean() - b.mean()) / se
        p = 2 * stats.t.sf(abs(t), df)
        ci = (gap - stats.t.ppf(.975, df) * se, gap + stats.t.ppf(.975, df) * se)
        check = stats.ttest_ind(a, b, equal_var=False)
        assert abs(t - check.statistic) < 1e-12 and abs(p - check.pvalue) < 1e-12
        scenarios[key] = dict(
            n=n, gap=gap, sd=sd, meanA=48, meanB=48 - gap,
            se=float(se), df=float(df), t=float(t), p=float(p),
            ci=[float(value) for value in ci], a=a.tolist(), b=b.tolist(),
        )

    # Fixed shared axis across all teaching examples.
    all_values = [v for d in scenarios.values() for k in ["a", "b"] for v in d[k]]
    lo = 10 * np.floor(min(all_values) / 10)
    hi = 10 * np.ceil(max(all_values) / 10)
    tx = np.linspace(-5.5, 5.5, 551)
    curve = [(float(x), float(stats.t.pdf(x, 38))) for x in tx]
    assets = dict(scenarios=scenarios, domain=[float(lo), float(hi)], curve=curve)
    (source_out / "assets.json").write_text(
        json.dumps(assets, separators=(",", ":")), encoding="utf-8", newline="\n"
    )

    with (out / "ramp_hazard_training.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["worker_id", "training", "report_seconds"])
        for group, key in [(1, "a"), (2, "b")]:
            for i, value in enumerate(scenarios["baseline"][key], 1):
                writer.writerow([f"{group}{i:02d}", group, f"{value:.9f}"])

    sps = """* RSCH 650: synthetic ramp hazard reporting example.
* Each row is one different worker; all observations are invented for teaching.
* Group 1 = standard briefing; group 2 = scenario practice.
* Outcome = seconds to correctly report a hazard in a standardized simulator task.
* Read the Equal variances not assumed row for the Welch test.
DATA LIST FREE /worker_id (F3.0) training (F1.0) report_seconds (F12.9).
BEGIN DATA
"""
    for group, key in [(1, "a"), (2, "b")]:
        for i, value in enumerate(scenarios["baseline"][key], 1):
            sps += f"{group}{i:02d} {group} {value:.9f}\n"
    sps += """END DATA.
DATASET NAME RampHazard.
VARIABLE LABELS training 'Assigned training method'
 report_seconds 'Time to correctly report a simulated ramp hazard (seconds)'.
VALUE LABELS training 1 'Standard briefing' 2 'Scenario practice'.
VARIABLE LEVEL training (NOMINAL) report_seconds (SCALE).
FORMATS report_seconds (F8.2).
T-TEST GROUPS=training(1 2)
 /VARIABLES=report_seconds
 /MISSING=ANALYSIS
 /CRITERIA=CI(.95).
"""
    (out / "ramp_hazard_training.sps").write_text(sps, encoding="utf-8", newline="\n")
    return scenarios


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR,
                        help="Destination for generated data (default: package directory).")
    args = parser.parse_args()
    scenarios = build_assets(args.output_dir)
    print(json.dumps({key: {name: value[name] for name in
                    ["n", "gap", "sd", "se", "df", "t", "p", "ci"]}
                    for key, value in scenarios.items()}, indent=2))


if __name__ == "__main__":
    main()
