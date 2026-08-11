"""
Run AFTER pytest has fully finished. Parses the output of pytest-json-report
and produces every report format the CI workflow uploads as artifacts.

Usage:
    python tests/reporting/generate_reports.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    Workbook = None

TESTS_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = TESTS_DIR / "reporting" / "output"
JSON_REPORT_PATH = TESTS_DIR.parent / "pytest-report.json" # try backend root first

# If not found locally, check /tmp/pytest-report.json
if not JSON_REPORT_PATH.exists():
    JSON_REPORT_PATH = Path("/tmp/pytest-report.json")


# ── Colour palette (matches Report-demo.xlsx) ───────────────────────────────
_HDR_EXECUTED   = "1A5276"   # navy
_HDR_PASSED     = "1E8449"   # green
_HDR_FAILED     = "C0392B"   # red
_HDR_SKIPPED    = "B7950B"   # amber

_STATUS_CELL_COLORS = {
    "PASSED":  "D5F5E3",
    "FAILED":  "FADBD8",
    "SKIPPED": "FEF9E7",
}

PASS_RATE_THRESHOLD = 95.0

def load_results():
    if not JSON_REPORT_PATH.exists():
        print(f"WARNING: no result file found at {JSON_REPORT_PATH}", file=sys.stderr)
        return []
    with open(JSON_REPORT_PATH, encoding="utf-8") as fh:
        payload = json.load(fh)
    
    # Map pytest-json-report format to the structure expected by reports
    tests = payload.get("tests", [])
    results = []
    for t in tests:
        nodeid = t.get("nodeid", "")
        # Extract module from nodeid (e.g. tests/functional/test_foo.py::test_bar)
        module = nodeid.split("::")[0] if "::" in nodeid else nodeid
        
        # Calculate total duration
        duration = 0.0
        for phase in ("setup", "call", "teardown"):
            if phase in t:
                duration += t[phase].get("duration", 0.0)
        
        results.append({
            "nodeid": nodeid,
            "status": t.get("outcome", "unknown"),
            "duration_s": round(duration, 3),
            "module": module,
            "markers": "" # pytest-json-report doesn't easily expose markers by default unless configured
        })
    return results

def summarize(results):
    counts = Counter(r["status"] for r in results)
    total = len(results)
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0)
    skipped = counts.get("skipped", 0)
    # xfailed counts as passed in some reports, or we can handle it separately
    xfailed = counts.get("xfailed", 0)
    
    # adjust for xfailed
    passed += xfailed 
    
    executed = passed + failed  # skipped tests don't count against pass rate
    pass_rate = round((passed / executed) * 100, 2) if executed else 0.0
    total_duration = round(sum(r.get("duration_s", 0.0) for r in results), 3)
    
    by_module = {}
    for r in results:
        mod = r["module"]
        status = "passed" if r["status"] == "xfailed" else r["status"]
        by_module.setdefault(mod, Counter())[status] += 1
        
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": pass_rate,
        "total_duration_s": total_duration,
        "by_module": {k: dict(v) for k, v in by_module.items()},
    }

def write_execution_results_json(results, summary, out_path, run_at=None):
    payload = {
        "generated_at": run_at or datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return payload

def write_summary_md(summary, out_path):
    lines = [
        "# NutriScan AI — Backend Test Summary",
        "",
        f"- **Total executed:** {summary['passed'] + summary['failed']}",
        f"- **Passed:** {summary['passed']}",
        f"- **Failed:** {summary['failed']}",
        f"- **Skipped:** {summary['skipped']}",
        f"- **Pass rate:** {summary['pass_rate']}% "
        f"(threshold: {PASS_RATE_THRESHOLD}%)",
        f"- **Total duration:** {summary['total_duration_s']}s",
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
    status_color = {"passed": "#1e8e4a", "failed": "#d64545", "skipped": "#b58900", "xfailed": "#1e8e4a"}
    rows = "\n".join(
        f"<tr><td>{r['nodeid']}</td>"
        f"<td style='color:{status_color.get(r['status'], '#333')};font-weight:600'>"
        f"{r['status'].upper()}</td>"
        f"<td>{r['duration_s']}s</td></tr>"
        for r in sorted(results, key=lambda x: x["nodeid"])
    )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>NutriScan AI — Backend Execution Report</title>
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
<h1>NutriScan AI — Backend Execution Report</h1>
<p class="meta">Generated: {datetime.now(timezone.utc).isoformat()}</p>
<div class="cards">
  <div class="card">Total<b>{summary['passed'] + summary['failed'] + summary['skipped']}</b></div>
  <div class="card" style="background:#eaf7ee">Passed<b style="color:#1e8e4a">{summary['passed']}</b></div>
  <div class="card" style="background:#fdeceb">Failed<b style="color:#d64545">{summary['failed']}</b></div>
  <div class="card" style="background:#fdf3d9">Skipped<b style="color:#b58900">{summary['skipped']}</b></div>
  <div class="card">Pass rate<b>{summary['pass_rate']}%</b></div>
  <div class="card">Duration<b>{summary['total_duration_s']}s</b></div>
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
<html><head><meta charset="utf-8"><title>NutriScan AI — Backend Test Dashboard</title>
<style>
body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }}
h1 {{ margin-bottom: 0.25rem; }}
.big {{ font-size: 3rem; font-weight: 700; }}
.gate-pass {{ color: #1e8e4a; }}
.gate-fail {{ color: #d64545; }}
</style></head>
<body>
<h1>NutriScan AI — Backend Test Dashboard</h1>
<p class="big {'gate-pass' if summary['pass_rate'] >= PASS_RATE_THRESHOLD else 'gate-fail'}">
  {summary['pass_rate']}%
</p>
<p>Gate: {PASS_RATE_THRESHOLD}% required to pass CI &middot;
   {summary['passed']} passed / {summary['failed']} failed / {summary['skipped']} skipped &middot;
   {summary['total_duration_s']}s total</p>
<h2>By module</h2>
{bars}
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)

def _test_id(nodeid: str) -> str:
    return nodeid.split("::")[-1]

def _module_label(module_path: str) -> str:
    basename = os.path.basename(module_path)
    stem = basename.replace(".py", "")
    if stem.startswith("test_"):
        stem = stem[5:]
    return stem.replace("_", " ").title()

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
    sorted_results = sorted(results, key=lambda x: x["nodeid"])

    ws = wb.active
    ws.title = "Executed Tests"
    _make_header(ws, ["#", "Test ID", "Module", "Markers", "Status", "Duration (s)"], _HDR_EXECUTED)

    for seq, r in enumerate(sorted_results, start=1):
        status_upper = r["status"].upper()
        if status_upper == "XFAILED":
            status_upper = "PASSED"
        module_label = _module_label(r["module"])
        markers      = r.get("markers") or ""
        ws.append([seq, _test_id(r["nodeid"]), module_label, markers,
                   status_upper, r["duration_s"]])
        row_idx = ws.max_row
        cell_color = _STATUS_CELL_COLORS.get(status_upper)
        if cell_color:
            ws.cell(row=row_idx, column=5).fill = PatternFill(
                "solid", fgColor=cell_color
            )
        for col in range(1, 7):
            ws.cell(row=row_idx, column=col).alignment = Alignment(
                vertical="center", wrap_text=False
            )

    for col_letter, width in zip("ABCDEF", [7, 50, 39, 11, 11, 16]):
        ws.column_dimensions[col_letter].width = width

    sheet_defs = [
        ("Passed",  "passed",  _HDR_PASSED),
        ("Failed",  "failed",  _HDR_FAILED),
        ("Skipped", "skipped", _HDR_SKIPPED),
    ]
    for sheet_name, status_key, hdr_color in sheet_defs:
        sh = wb.create_sheet(sheet_name)
        _make_header(sh, ["#", "Test ID", "Module", "Duration (s)"], hdr_color)
        seq = 0
        for r in sorted_results:
            status = "passed" if r["status"] == "xfailed" else r["status"]
            if status == status_key:
                seq += 1
                sh.append([seq, _test_id(r["nodeid"]),
                            _module_label(r["module"]), r["duration_s"]])
                for col in range(1, 5):
                    sh.cell(row=sh.max_row, column=col).alignment = Alignment(
                        vertical="center"
                    )
        for col_letter, width in zip("ABCD", [7, 50, 39, 16]):
            sh.column_dimensions[col_letter].width = width

    metrics = wb.create_sheet("Execution Metrics")
    bold = Font(bold=True)
    metrics.cell(row=1, column=1, value="Metric").font = bold
    metrics.cell(row=1, column=2, value="Value").font  = bold
    metrics_rows = [
        ("Run At",           run_at or datetime.now(timezone.utc).isoformat()),
        ("Total Tests",      summary["total"]),
        ("Passed",           summary["passed"]),
        ("Failed",           summary["failed"]),
        ("Skipped",          summary["skipped"]),
        ("Pass Rate (%)",    summary["pass_rate"]),
        ("Total Duration (s)", summary["total_duration_s"]),
    ]
    for metric, value in metrics_rows:
        metrics.append([metric, value])
    metrics.column_dimensions["A"].width = 22
    metrics.column_dimensions["B"].width = 49

    defects = wb.create_sheet("Defect Summary")
    _make_header(defects, ["#", "Defect / Test ID", "Module", "Severity"], _HDR_FAILED)
    seq = 0
    for r in sorted_results:
        if r["status"] == "failed":
            seq += 1
            defects.append([seq, _test_id(r["nodeid"]),
                             _module_label(r["module"]), "LOW"])
            for col in range(1, 5):
                defects.cell(row=defects.max_row, column=col).alignment = Alignment(
                    vertical="center"
                )
    defects.column_dimensions["A"].width = 6
    defects.column_dimensions["B"].width = 50
    defects.column_dimensions["C"].width = 39
    defects.column_dimensions["D"].width = 12

    wb.save(out_path)
    print(f"Wrote {out_path}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = load_results()

    if not results:
        print("WARNING: no result found — did pytest run?", file=sys.stderr)
        return

    run_at = datetime.now(timezone.utc).isoformat()
    summary = summarize(results)
    print(f"Total={summary['total']} Passed={summary['passed']} "
          f"Failed={summary['failed']} Skipped={summary['skipped']} "
          f"PassRate={summary['pass_rate']}% Duration={summary['total_duration_s']}s")

    write_execution_results_json(
        results, summary,
        OUTPUT_DIR / "execution-results.json",
        run_at=run_at,
    )
    write_summary_md(summary, OUTPUT_DIR / "summary.md")
    write_execution_report_html(
        results, summary, OUTPUT_DIR / "execution-report.html"
    )
    write_dashboard_html(summary, OUTPUT_DIR / "dashboard.html")
    write_xlsx(
        results, summary,
        OUTPUT_DIR / "Automation_Test_Report.xlsx",
        run_at=run_at,
    )

    print("Reports written to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
