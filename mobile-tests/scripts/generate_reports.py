"""
Run AFTER pytest has fully finished. Reads reports/execution-results.json
(one JSON object per line, appended by conftest.py's _record_result
fixture during the run) and produces every report format the
android-e2e CI workflow uploads as artifacts.

Mirrors selenium-tests/scripts/generate_reports.py's xlsx schema exactly
(same 6 sheets, same colours) so the two suites' reports are visually
and structurally consistent.

Usage:
    python scripts/generate_reports.py
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError:
    Workbook = None

_HDR_EXECUTED = "1A5276"
_HDR_PASSED = "1E8449"
_HDR_FAILED = "C0392B"
_HDR_SKIPPED = "B7950B"

_STATUS_CELL_COLORS = {
    "PASSED": "D5F5E3",
    "FAILED": "FADBD8",
    "SKIPPED": "FEF9E7",
    "UNKNOWN": "EAECEE",
}

RAW_RESULTS_PATH = os.path.join(config.REPORTS_DIR, "raw-results.jsonl")
EXECUTION_RESULTS_PATH = os.path.join(config.REPORTS_DIR, "execution-results.json")


def load_raw_rows():
    """Every attempt (original + reruns from `--reruns 1`), unmodified."""
    if not os.path.exists(RAW_RESULTS_PATH):
        return []
    rows = []
    with open(RAW_RESULTS_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def dedupe_to_final_attempt(raw_rows):
    """Collapse repeated rows for the same test_id (pytest-rerunfailures
    logs the original attempt AND every rerun as separate rows) down to
    ONE result per test -- the last attempt, since that's what pytest
    itself treats as the test's real outcome. Also tags each kept row
    with `attempts` so a test that failed then passed on rerun is still
    visible as flaky rather than silently looking clean.

    Without this step, a run with 450 unique tests where ~410 failed at
    least once produces ~800+ raw rows, and both the total test count
    and the pass/fail split get double-counted in the summary/xlsx (a
    test can land in both the Passed and Failed sheets: once per
    attempt).
    """
    order = {}
    by_test = {}
    for i, r in enumerate(raw_rows):
        tid = r["test_id"]
        order.setdefault(tid, i)
        by_test.setdefault(tid, []).append(r)

    final = []
    for tid, attempts in by_test.items():
        last = dict(attempts[-1])
        last["attempts"] = len(attempts)
        last["flaky"] = len(attempts) > 1 and last["status"] == "passed"
        final.append(last)
    final.sort(key=lambda r: order[r["test_id"]])
    return final


def load_results():
    return dedupe_to_final_attempt(load_raw_rows())


def write_execution_results_json(results, summary, run_at):
    """Aggregated summary (schema matches selenium-tests/) — this is the
    file scripts/check_pass_rate.py reads, NOT the raw per-test JSONL."""
    payload = {
        "generated_at": run_at,
        "app_package": config.APP_PACKAGE,
        "summary": summary,
        "results": results,
    }
    with open(EXECUTION_RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def load_collected_ids():
    """Test IDs pytest --collect-only saw before the run started (written
    per-shard by ci_run_shard.sh, merged by the CI workflow into
    collected-all.txt). Empty list if that file isn't present (e.g. a
    local/manual run), in which case never-executed detection is simply
    skipped rather than false-alarming."""
    path = os.path.join(config.REPORTS_DIR, "collected-all.txt")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


def summarize(results, collected_ids=None):
    counts = Counter(r["status"] for r in results)
    total = len(results)  # unique tests with at least one recorded attempt
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0)
    skipped = counts.get("skipped", 0)
    executed = passed + failed
    pass_rate = round((passed / executed) * 100, 2) if executed else 0.0
    total_duration = round(sum(r.get("duration_s", 0.0) for r in results), 3)
    total_attempts = sum(r.get("attempts", 1) for r in results)
    flaky = sum(1 for r in results if r.get("flaky"))
    by_module = {}
    for r in results:
        mod = r.get("module", "unknown")
        by_module.setdefault(mod, Counter())[r["status"]] += 1

    never_executed = []
    if collected_ids:
        seen = {r["test_id"] for r in results}
        never_executed = sorted(tid for tid in collected_ids if tid not in seen)

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": pass_rate,
        "total_duration_s": total_duration,
        "total_attempts": total_attempts,  # rows in raw-results.jsonl, incl. reruns
        "flaky": flaky,  # failed at least once but passed on a rerun
        "collected": len(collected_ids) if collected_ids else None,
        "never_executed": len(never_executed),
        "never_executed_ids": never_executed,
        "by_module": {k: dict(v) for k, v in by_module.items()},
    }


def _module_label(module_path: str) -> str:
    basename = os.path.basename(module_path.replace(".", "/") + ".py") if "." in module_path else os.path.basename(module_path)
    stem = basename.replace(".py", "")
    if stem.startswith("test_"):
        stem = stem[5:]
    return stem.replace("_", " ").title()


def _test_id(test_id: str) -> str:
    return test_id.split("::")[-1]


def _make_header(ws, columns, fill_color):
    fill = PatternFill("solid", fgColor=fill_color)
    font = Font(bold=True, color="FFFFFF")
    align = Alignment(horizontal="center", vertical="center")
    for col_idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = fill
        cell.font = font
        cell.alignment = align
    ws.freeze_panes = "A2"


def write_xlsx(results, summary, out_path, run_at=None):
    if Workbook is None:
        print("openpyxl not installed — skipping .xlsx report", file=sys.stderr)
        return

    wb = Workbook()
    sorted_results = sorted(results, key=lambda x: x["test_id"])

    ws = wb.active
    ws.title = "Executed Tests"
    _make_header(ws, ["#", "Test ID", "Module", "Shard", "Status", "Duration (s)"], _HDR_EXECUTED)
    for seq, r in enumerate(sorted_results, start=1):
        status_upper = r["status"].upper()
        ws.append([seq, _test_id(r["test_id"]), _module_label(r["module"]),
                   r.get("shard", "default"), status_upper, r["duration_s"]])
        row_idx = ws.max_row
        cell_color = _STATUS_CELL_COLORS.get(status_upper)
        if cell_color:
            ws.cell(row=row_idx, column=5).fill = PatternFill("solid", fgColor=cell_color)
        for col in range(1, 7):
            ws.cell(row=row_idx, column=col).alignment = Alignment(vertical="center")
    for col_letter, width in zip("ABCDEF", [7, 60, 30, 14, 11, 16]):
        ws.column_dimensions[col_letter].width = width

    for sheet_name, status_key, hdr_color in [
        ("Passed", "passed", _HDR_PASSED),
        ("Failed", "failed", _HDR_FAILED),
        ("Skipped", "skipped", _HDR_SKIPPED),
    ]:
        sh = wb.create_sheet(sheet_name)
        _make_header(sh, ["#", "Test ID", "Module", "Duration (s)"], hdr_color)
        seq = 0
        for r in sorted_results:
            if r["status"] == status_key:
                seq += 1
                sh.append([seq, _test_id(r["test_id"]), _module_label(r["module"]), r["duration_s"]])
                for col in range(1, 5):
                    sh.cell(row=sh.max_row, column=col).alignment = Alignment(vertical="center")
        for col_letter, width in zip("ABCD", [7, 60, 30, 16]):
            sh.column_dimensions[col_letter].width = width

    metrics = wb.create_sheet("Execution Metrics")
    bold = Font(bold=True)
    metrics.cell(row=1, column=1, value="Metric").font = bold
    metrics.cell(row=1, column=2, value="Value").font = bold
    for metric, value in [
        ("Run At", run_at or datetime.now(timezone.utc).isoformat()),
        ("App Package", config.APP_PACKAGE),
        ("Device", config.DEVICE_NAME),
        ("Total Tests (unique)", summary["total"]),
        ("Passed", summary["passed"]),
        ("Failed", summary["failed"]),
        ("Skipped", summary["skipped"]),
        ("Flaky (failed then passed on rerun)", summary["flaky"]),
        ("Pass Rate (%)", summary["pass_rate"]),
        ("Total Duration (s)", summary["total_duration_s"]),
        ("Total Attempts (incl. reruns)", summary["total_attempts"]),
        ("Collected (expected)", summary["collected"] if summary["collected"] is not None else "n/a"),
        ("Never Executed", summary["never_executed"]),
    ]:
        metrics.append([metric, value])
    metrics.column_dimensions["A"].width = 30
    metrics.column_dimensions["B"].width = 49

    defects = wb.create_sheet("Defect Summary")
    _make_header(defects, ["#", "Defect / Test ID", "Module", "Severity"], _HDR_FAILED)
    seq = 0
    for r in sorted_results:
        if r["status"] == "failed":
            seq += 1
            defects.append([seq, _test_id(r["test_id"]), _module_label(r["module"]), "LOW"])
            for col in range(1, 5):
                defects.cell(row=defects.max_row, column=col).alignment = Alignment(vertical="center")
    defects.column_dimensions["A"].width = 6
    defects.column_dimensions["B"].width = 60
    defects.column_dimensions["C"].width = 30
    defects.column_dimensions["D"].width = 12

    if summary.get("never_executed_ids"):
        never = wb.create_sheet("Never Executed")
        _make_header(never, ["#", "Test ID"], _HDR_SKIPPED)
        for seq, tid in enumerate(summary["never_executed_ids"], start=1):
            never.append([seq, _test_id(tid)])
        never.column_dimensions["A"].width = 6
        never.column_dimensions["B"].width = 60

    wb.save(out_path)
    print(f"Wrote {out_path}")


def write_summary_md(summary, out_path):
    lines = [
        "# NutriScan AI — Android E2E Test Summary",
        "",
        f"- **Total executed (unique tests):** {summary['passed'] + summary['failed']}",
        f"- **Passed:** {summary['passed']}",
        f"- **Failed:** {summary['failed']}",
        f"- **Skipped:** {summary['skipped']}",
        f"- **Flaky (failed once, passed on rerun):** {summary['flaky']}",
        f"- **Pass rate:** {summary['pass_rate']}% (threshold: {config.PASS_RATE_THRESHOLD}%)",
        f"- **Total duration:** {summary['total_duration_s']}s",
        f"- **Total attempts recorded (incl. reruns):** {summary['total_attempts']}",
    ]
    if summary.get("collected") is not None:
        lines.append(
            f"- **Collected (expected):** {summary['collected']} — "
            f"**Never executed:** {summary['never_executed']}"
            + (" ⚠️ some tests did not run (likely a timeout mid-shard)" if summary['never_executed'] else "")
        )
    lines += [
        "",
        "## By module",
        "",
        "| Module | Passed | Failed | Skipped |",
        "|---|---|---|---|",
    ]
    for mod, counts in sorted(summary["by_module"].items()):
        lines.append(f"| `{mod}` | {counts.get('passed', 0)} | {counts.get('failed', 0)} | {counts.get('skipped', 0)} |")
    if summary.get("never_executed_ids"):
        lines += ["", "## Never executed", ""]
        lines += [f"- `{tid}`" for tid in summary["never_executed_ids"]]
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    results = load_results()
    if not results:
        print(f"WARNING: no results found at {RAW_RESULTS_PATH} — did pytest run?", file=sys.stderr)
    collected_ids = load_collected_ids()
    run_at = datetime.now(timezone.utc).isoformat()
    summary = summarize(results, collected_ids)
    print(f"Total(unique)={summary['total']} Passed={summary['passed']} Failed={summary['failed']} "
          f"Skipped={summary['skipped']} PassRate={summary['pass_rate']}% Duration={summary['total_duration_s']}s "
          f"Attempts={summary['total_attempts']} NeverExecuted={summary['never_executed']}")
    write_execution_results_json(results, summary, run_at)
    write_summary_md(summary, os.path.join(config.REPORTS_DIR, "summary.md"))
    write_xlsx(results, summary, os.path.join(config.REPORTS_DIR, "Automation_Test_Report.xlsx"), run_at=run_at)
    print("Reports written to", config.REPORTS_DIR)


if __name__ == "__main__":
    main()
