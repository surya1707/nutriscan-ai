"""
Run AFTER pytest has fully finished (never inside a pytest hook — xdist
workers finish at different times and would race each other for a
shared output file). Globs every per-worker result file, merges them,
and produces every report format the CI workflow uploads as artifacts.

Usage:
    python scripts/generate_reports.py
"""

import glob
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
    from openpyxl.utils import get_column_letter
except ImportError:
    Workbook = None


def load_all_results():
    """Recursive glob — a flat glob missed nested shard output before;
    always search recursively so no worker's file is silently dropped."""
    pattern = os.path.join(config.RESULTS_DIR, "**", "result_*.json")
    files = sorted(glob.glob(pattern, recursive=True))
    merged = []
    workers_seen = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        workers_seen.append(payload.get("worker", "unknown"))
        merged.extend(payload.get("results", []))
    return merged, workers_seen, files


def summarize(results):
    counts = Counter(r["status"] for r in results)
    total = len(results)
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0)
    skipped = counts.get("skipped", 0)
    executed = passed + failed  # skipped tests don't count against pass rate
    pass_rate = round((passed / executed) * 100, 2) if executed else 0.0
    by_module = {}
    for r in results:
        mod = r["module"]
        by_module.setdefault(mod, Counter())[r["status"]] += 1
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": pass_rate,
        "by_module": {k: dict(v) for k, v in by_module.items()},
    }


def write_execution_results_json(results, summary, out_path):
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": config.BASE_URL,
        "summary": summary,
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return payload


def write_summary_md(summary, out_path):
    lines = [
        "# NutriScan AI — Selenium Web Test Summary",
        "",
        f"- **Total executed:** {summary['passed'] + summary['failed']}",
        f"- **Passed:** {summary['passed']}",
        f"- **Failed:** {summary['failed']}",
        f"- **Skipped:** {summary['skipped']}",
        f"- **Pass rate:** {summary['pass_rate']}% "
        f"(threshold: {config.PASS_RATE_THRESHOLD}%)",
        "",
        "## By module",
        "",
        "| Module | Passed | Failed | Skipped |",
        "|---|---|---|---|",
    ]
    for mod, counts in sorted(summary["by_module"].items()):
        lines.append(
            f"| `{mod}` | {counts.get('passed', 0)} | "
            f"{counts.get('failed', 0)} | {counts.get('skipped', 0)} |"
        )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def write_execution_report_html(results, summary, out_path):
    status_color = {"passed": "#1e8e4a", "failed": "#d64545", "skipped": "#b58900"}
    rows = "\n".join(
        f"<tr><td>{r['nodeid']}</td>"
        f"<td style='color:{status_color.get(r['status'], '#333')};font-weight:600'>"
        f"{r['status'].upper()}</td>"
        f"<td>{r['duration_s']}s</td></tr>"
        for r in sorted(results, key=lambda x: x["nodeid"])
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>NutriScan AI — Selenium Execution Report</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; color: #1a1a1a; }}
h1 {{ margin-bottom: 0.25rem; }}
.meta {{ color: #666; margin-bottom: 1.5rem; }}
.cards {{ display: flex; gap: 1rem; margin-bottom: 2rem; }}
.card {{ padding: 1rem 1.5rem; border-radius: 10px; background: #f4f4f4; min-width: 120px; }}
.card b {{ display:block; font-size: 1.6rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }}
th {{ background: #fafafa; position: sticky; top: 0; }}
</style></head>
<body>
<h1>NutriScan AI — Selenium Execution Report</h1>
<p class="meta">Target: {config.BASE_URL} &middot; Generated: {datetime.now(timezone.utc).isoformat()}</p>
<div class="cards">
  <div class="card">Total<b>{summary['passed'] + summary['failed'] + summary['skipped']}</b></div>
  <div class="card" style="background:#eaf7ee">Passed<b style="color:#1e8e4a">{summary['passed']}</b></div>
  <div class="card" style="background:#fdeceb">Failed<b style="color:#d64545">{summary['failed']}</b></div>
  <div class="card" style="background:#fdf3d9">Skipped<b style="color:#b58900">{summary['skipped']}</b></div>
  <div class="card">Pass rate<b>{summary['pass_rate']}%</b></div>
</div>
<table>
<thead><tr><th>Test</th><th>Status</th><th>Duration</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)


def write_dashboard_html(summary, out_path):
    by_module = summary["by_module"]
    bars = ""
    for mod, counts in sorted(by_module.items()):
        total = sum(counts.values()) or 1
        passed_pct = counts.get("passed", 0) / total * 100
        failed_pct = counts.get("failed", 0) / total * 100
        skipped_pct = counts.get("skipped", 0) / total * 100
        short_mod = mod.split("/")[-1].replace(".py", "")
        bars += f"""
<div style="margin-bottom:0.75rem">
  <div style="font-size:0.85rem;margin-bottom:0.2rem">{short_mod} ({total})</div>
  <div style="display:flex;height:14px;border-radius:7px;overflow:hidden;background:#eee">
    <div style="width:{passed_pct}%;background:#1e8e4a"></div>
    <div style="width:{failed_pct}%;background:#d64545"></div>
    <div style="width:{skipped_pct}%;background:#b58900"></div>
  </div>
</div>"""
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>NutriScan AI — Test Dashboard</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }}
h1 {{ margin-bottom: 0.25rem; }}
.big {{ font-size: 3rem; font-weight: 700; }}
.gate-pass {{ color: #1e8e4a; }}
.gate-fail {{ color: #d64545; }}
</style></head>
<body>
<h1>NutriScan AI — Test Dashboard</h1>
<p class="big {'gate-pass' if summary['pass_rate'] >= config.PASS_RATE_THRESHOLD else 'gate-fail'}">
  {summary['pass_rate']}%
</p>
<p>Gate: {config.PASS_RATE_THRESHOLD}% required to pass CI &middot;
   {summary['passed']} passed / {summary['failed']} failed / {summary['skipped']} skipped</p>
<h2>By module</h2>
{bars}
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)


def write_xlsx(results, summary, out_path):
    if Workbook is None:
        print("openpyxl not installed — skipping .xlsx report", file=sys.stderr)
        return

    wb = Workbook()

    # Executed Tests sheet
    ws = wb.active
    ws.title = "Executed Tests"
    headers = ["Test Case ID", "Module", "Status", "Duration (s)", "Failure Reason"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2D4A3E")
        cell.alignment = Alignment(horizontal="center")
    for i, r in enumerate(sorted(results, key=lambda x: x["nodeid"]), start=1):
        ws.append([
            f"TC-{i:04d}",
            r["module"],
            r["status"].upper(),
            r["duration_s"],
            (r.get("longrepr") or "")[:500],
        ])
    for col, width in zip("ABCDE", [12, 40, 12, 14, 60]):
        ws.column_dimensions[col].width = width

    # Summary sheets
    for name, statuses in [("Passed", ["passed"]), ("Failed", ["failed"]), ("Skipped", ["skipped"])]:
        sheet = wb.create_sheet(name)
        sheet.append(["Test", "Duration (s)"])
        for r in results:
            if r["status"] in statuses:
                sheet.append([r["nodeid"], r["duration_s"]])

    # Execution Metrics
    metrics = wb.create_sheet("Execution Metrics")
    metrics.append(["Metric", "Value"])
    metrics.append(["Total executed", summary["passed"] + summary["failed"]])
    metrics.append(["Passed", summary["passed"]])
    metrics.append(["Failed", summary["failed"]])
    metrics.append(["Skipped", summary["skipped"]])
    metrics.append(["Pass rate (%)", summary["pass_rate"]])
    metrics.append(["Threshold (%)", config.PASS_RATE_THRESHOLD])
    metrics.append(["Target URL", config.BASE_URL])
    metrics.column_dimensions["A"].width = 22
    metrics.column_dimensions["B"].width = 50

    # Defect Summary (failures only, grouped by module)
    defects = wb.create_sheet("Defect Summary")
    defects.append(["Module", "Failed Count", "Example Failure"])
    by_mod_fail = {}
    for r in results:
        if r["status"] == "failed":
            by_mod_fail.setdefault(r["module"], []).append(r)
    for mod, fails in sorted(by_mod_fail.items()):
        defects.append([mod, len(fails), (fails[0].get("longrepr") or "")[:300]])
    defects.column_dimensions["A"].width = 40
    defects.column_dimensions["C"].width = 60

    wb.save(out_path)


def main():
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    results, workers, files = load_all_results()

    if not results:
        print("WARNING: no result files found under "
              f"{config.RESULTS_DIR} — did pytest run?", file=sys.stderr)

    summary = summarize(results)
    print(f"Merged {len(files)} worker file(s): {workers}")
    print(f"Total={summary['total']} Passed={summary['passed']} "
          f"Failed={summary['failed']} Skipped={summary['skipped']} "
          f"PassRate={summary['pass_rate']}%")

    write_execution_results_json(
        results, summary, os.path.join(config.REPORTS_DIR, "execution-results.json")
    )
    write_summary_md(summary, os.path.join(config.REPORTS_DIR, "summary.md"))
    write_execution_report_html(
        results, summary, os.path.join(config.REPORTS_DIR, "execution-report.html")
    )
    write_dashboard_html(summary, os.path.join(config.REPORTS_DIR, "dashboard.html"))
    write_xlsx(
        results, summary,
        os.path.join(config.REPORTS_DIR, "Automation_Test_Report.xlsx"),
    )

    print("Reports written to", config.REPORTS_DIR)


if __name__ == "__main__":
    main()
