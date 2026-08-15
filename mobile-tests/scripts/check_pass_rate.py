"""
Reads reports/execution-results.json (written by generate_reports.py,
AFTER it has aggregated reports/raw-results.jsonl) and exits non-zero
only if the pass rate is below config.PASS_RATE_THRESHOLD. Run as its
own CI step AFTER report generation and artifact upload, so a failing
run still leaves every report/screenshot downloadable.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402


def main():
    path = os.path.join(config.REPORTS_DIR, "execution-results.json")
    if not os.path.exists(path):
        print(f"::error::{path} not found — report generation must have failed", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)

    summary = payload["summary"]
    pass_rate = summary["pass_rate"]
    threshold = config.PASS_RATE_THRESHOLD

    print(f"Pass rate: {pass_rate}% (threshold {threshold}%)")
    print(f"Passed={summary['passed']} Failed={summary['failed']} Skipped={summary['skipped']}")

    if pass_rate >= threshold:
        print(f"::notice::Pass rate {pass_rate}% meets the {threshold}% gate.")
        sys.exit(0)
    else:
        print(f"::error::Pass rate {pass_rate}% is BELOW the {threshold}% gate.")
        sys.exit(1)


if __name__ == "__main__":
    main()
