"""
Generates two handover artifacts from this test suite:

  1. test-case-catalog.xlsx -- every test, with its CATEGORY / TITLE /
     OBJECTIVE / EXPECTED / SEVERITY metadata (parsed straight out of each
     test's docstring) plus its most recent pass/fail/xfail result.
  2. findings.xlsx -- just the subset of tests whose docstring is tagged
     with a real finding (SEVERITY != none, or the docstring literally
     contains "[FINDING" / "[CONFIRMED BUG" / "[KNOWN GAP"), with the full
     objective/impact/remediation text so it reads as a standalone report.

Usage:
    # 1. Run pytest once with the JSON report plugin so this script has
    #    real pass/fail data to attach (not required, but recommended):
    pytest tests/ --json-report --json-report-file=/tmp/pytest-report.json

    # 2. Generate the workbooks:
    python tests/reporting/generate_reports.py

This is a plain regex/AST scan over the test files themselves -- it does not
import pytest internals, so it works even if the test run itself had
collection errors, and it never fabricates a row for a test that doesn't
exist in the source.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    print("openpyxl is required: pip install openpyxl (see requirements-test.txt)", file=sys.stderr)
    raise

TESTS_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = TESTS_DIR.parent
OUTPUT_DIR = TESTS_DIR / "reporting" / "output"
JSON_REPORT_PATH = Path("/tmp/pytest-report.json")

# ── Execution-report colour palette (matches Report-demo.xlsx) ───────────────
_HDR_EXECUTED = "1A5276"   # navy
_HDR_PASSED   = "1E8449"   # green
_HDR_FAILED   = "C0392B"   # red
_HDR_SKIPPED  = "B7950B"   # amber
_STATUS_CELL  = {"passed": "D5F5E3", "failed": "FADBD8", "skipped": "FEF9E7"}

FIELD_PATTERN = re.compile(
    r"^\s*(CATEGORY|TITLE|OBJECTIVE|EXPECTED|IMPACT|REMEDIATION|SEVERITY|ACTUAL)\s*:\s*(.*)$"
)
FINDING_MARKERS = ("[FINDING", "[CONFIRMED BUG", "[KNOWN GAP", "[TEST-INFRA FINDING", "[INFORMATIONAL")


@dataclass
class TestCase:
    file: str
    name: str
    qualified_id: str
    line: int
    category: str = "Uncategorized"
    title: str = ""
    objective: str = ""
    expected: str = ""
    actual: str = ""
    impact: str = ""
    remediation: str = ""
    severity: str = ""
    is_finding: bool = False
    raw_docstring: str = ""
    result: str = "not run"
    parametrized_count: int = 1


def _parse_docstring(docstring: str) -> dict:
    fields: dict[str, list[str]] = {}
    current_field = None
    for line in (docstring or "").splitlines():
        match = FIELD_PATTERN.match(line)
        if match:
            current_field = match.group(1).upper()
            fields[current_field] = [match.group(2).strip()]
        elif current_field and line.strip():
            fields[current_field].append(line.strip())
    return {k: " ".join(v).strip() for k, v in fields.items()}


def _extract_from_file(path: Path) -> list[TestCase]:
    source = path.read_text()
    tree = ast.parse(source, filename=str(path))
    cases = []
    module_rel = path.relative_to(TESTS_DIR)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_"):
            continue
        docstring = ast.get_docstring(node) or ""
        parsed = _parse_docstring(docstring)

        param_count = 1
        for deco in node.decorator_list:
            deco_src = ast.get_source_segment(source, deco) or ""
            if "parametrize" in deco_src:
                # crude but reliable enough for a report: count top-level commas
                # in the first list/tuple literal argument as case-count - 1
                list_match = re.search(r"\[(.*)\]\s*,?\s*\)?\s*$", deco_src, re.S)
                if list_match:
                    depth = 0
                    commas = 0
                    for ch in list_match.group(1):
                        if ch in "([{":
                            depth += 1
                        elif ch in ")]}":
                            depth -= 1
                        elif ch == "," and depth == 0:
                            commas += 1
                    if commas:
                        param_count = commas + 1

        is_finding = any(marker in docstring for marker in FINDING_MARKERS)

        cases.append(
            TestCase(
                file=str(module_rel),
                name=node.name,
                qualified_id=f"{module_rel}::{node.name}",
                line=node.lineno,
                category=parsed.get("CATEGORY", "Uncategorized"),
                title=parsed.get("TITLE", node.name.replace("test_", "").replace("_", " ")),
                objective=parsed.get("OBJECTIVE", ""),
                expected=parsed.get("EXPECTED", ""),
                actual=parsed.get("ACTUAL", ""),
                impact=parsed.get("IMPACT", ""),
                remediation=parsed.get("REMEDIATION", ""),
                severity=parsed.get("SEVERITY", ""),
                is_finding=is_finding,
                raw_docstring=docstring.strip(),
                parametrized_count=param_count,
            )
        )
    return cases


def collect_all_test_cases() -> list[TestCase]:
    cases: list[TestCase] = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "reporting/output" in str(path):
            continue
        cases.extend(_extract_from_file(path))
    return cases


def attach_results(cases: list[TestCase]) -> tuple[int, int]:
    """Returns (collected_total, ran_total) from the JSON report, or (0, 0) if absent."""
    if not JSON_REPORT_PATH.exists():
        print(
            f"[info] no pytest-json-report found at {JSON_REPORT_PATH} -- "
            "run pytest with --json-report first for pass/fail columns and "
            "an authoritative total-case count. Continuing with the static "
            "catalog only (parametrized-case counts will be estimated from "
            "source, which can undercount cases using a named list variable "
            "rather than an inline literal in @pytest.mark.parametrize)."
        )
        return (0, 0)

    data = json.loads(JSON_REPORT_PATH.read_text())
    outcomes: dict[str, str] = {}
    case_run_counts: dict[str, int] = {}
    for test in data.get("tests", []):
        # nodeid looks like "functional/test_scan_functional.py::test_x[param]"
        base_id = re.sub(r"\[.*\]$", "", test["nodeid"])
        outcome = test.get("outcome", "unknown")
        case_run_counts[base_id] = case_run_counts.get(base_id, 0) + 1
        # if any parametrized variant failed, mark the whole case failed
        if base_id in outcomes and outcomes[base_id] == "failed":
            continue
        outcomes[base_id] = outcome

    for case in cases:
        case.result = outcomes.get(case.qualified_id, "not run")
        if case.qualified_id in case_run_counts:
            # authoritative count from the actual pytest run beats the
            # regex-based estimate parsed from source
            case.parametrized_count = case_run_counts[case.qualified_id]

    summary = data.get("summary", {})
    return (summary.get("collected", 0), summary.get("total", 0))


SEVERITY_COLORS = {
    "critical": "FFC7CE",
    "high": "FFD8B1",
    "medium": "FFEB9C",
    "low": "E2EFDA",
    "informational": "DDEBF7",
}
RESULT_COLORS = {
    "passed": "C6EFCE",
    "failed": "FFC7CE",
    "xfailed": "FFEB9C",
    "not run": "F2F2F2",
}


def _style_header(ws, columns):
    header_fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for idx, col in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=idx, value=col)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


def write_catalog(cases: list[TestCase], out_path: Path, authoritative_total: int = 0) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Case Catalog"
    columns = [
        "File", "Test Name", "Category", "Title", "Objective", "Expected",
        "Severity", "Parametrized Cases", "Result",
    ]
    _style_header(ws, columns)

    for case in sorted(cases, key=lambda c: (c.category, c.file, c.line)):
        row = [
            case.file, case.name, case.category, case.title, case.objective,
            case.expected, case.severity, case.parametrized_count, case.result,
        ]
        ws.append(row)
        r = ws.max_row
        result_key = case.result.lower()
        if result_key in RESULT_COLORS:
            ws.cell(row=r, column=9).fill = PatternFill(
                start_color=RESULT_COLORS[result_key], end_color=RESULT_COLORS[result_key], fill_type="solid"
            )
        for c in range(1, len(columns) + 1):
            ws.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)

    widths = [32, 42, 22, 46, 60, 40, 12, 10, 12]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Summary sheet
    summary = wb.create_sheet("Summary")
    total_cases = authoritative_total if authoritative_total else sum(c.parametrized_count for c in cases)
    by_category: dict[str, int] = {}
    for c in cases:
        by_category[c.category] = by_category.get(c.category, 0) + c.parametrized_count
    summary.append(["Metric", "Value"])
    summary["A1"].font = Font(bold=True)
    summary["B1"].font = Font(bold=True)
    summary.append(["Total test functions", len(cases)])
    summary.append([
        "Total test cases (incl. parametrized)"
        + ("" if authoritative_total else " [estimated from source]"),
        total_cases,
    ])
    summary.append(["Confirmed findings (bugs/gaps documented via tests)", sum(1 for c in cases if c.is_finding)])
    summary.append([])
    summary.append(["By category", "Case count"])
    summary["A6"].font = Font(bold=True)
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        summary.append([cat, count])
    summary.column_dimensions["A"].width = 48
    summary.column_dimensions["B"].width = 16

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    print(f"Wrote {out_path} ({len(cases)} test functions, {total_cases} test cases)")


def write_findings(cases: list[TestCase], out_path: Path) -> None:
    findings = [c for c in cases if c.is_finding]
    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"
    columns = ["Severity", "Title", "Category", "Objective / Root Cause", "Impact", "Remediation", "Regression Test"]
    _style_header(ws, columns)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4, "": 5}
    for case in sorted(findings, key=lambda c: severity_order.get(c.severity.lower(), 5)):
        row = [case.severity, case.title, case.category, case.objective, case.impact, case.remediation, case.qualified_id]
        ws.append(row)
        r = ws.max_row
        sev_key = case.severity.lower()
        if sev_key in SEVERITY_COLORS:
            ws.cell(row=r, column=1).fill = PatternFill(
                start_color=SEVERITY_COLORS[sev_key], end_color=SEVERITY_COLORS[sev_key], fill_type="solid"
            )
        for c in range(1, len(columns) + 1):
            ws.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)

    widths = [14, 46, 22, 60, 50, 50, 46]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    print(f"Wrote {out_path} ({len(findings)} findings)")


# ── Execution-report helpers ─────────────────────────────────────────────────

def _make_exec_header(ws, columns: list[str], fill_color: str) -> None:
    """Write a bold white-on-colour header row and freeze pane at A2."""
    fill  = PatternFill("solid", fgColor=fill_color)
    font  = Font(bold=True, color="FFFFFF")
    align = Alignment(horizontal="center", vertical="center")
    for idx, col_name in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=idx, value=col_name)
        cell.fill  = fill
        cell.font  = font
        cell.alignment = align
    ws.freeze_panes = "A2"


def _test_id_from_nodeid(nodeid: str) -> str:
    """Return just the test function name from a full pytest nodeid."""
    return re.sub(r"\[.*\]$", "", nodeid).split("::")[-1]


def _module_label_from_path(module_path: str) -> str:
    """Convert a file-path module string to a human-readable category label.

    e.g. 'functional/test_scan_functional.py' → 'Scan Functional'
    """
    stem = Path(module_path).stem          # test_scan_functional
    if stem.startswith("test_"):
        stem = stem[5:]                    # scan_functional
    return stem.replace("_", " ").title()  # Scan Functional


def write_execution_xlsx(out_path: Path) -> None:
    """Produce Automation_Test_Report.xlsx in the same 6-sheet format as
    Report-demo.xlsx, populated from the pytest JSON report if available.

    Sheets
    ------
    1. Executed Tests  – every test with #, Test ID, Module, Markers, Status,
                         Duration (s); Status cell is colour-coded.
    2. Passed          – #, Test ID, Module, Duration (s)
    3. Failed          – #, Test ID, Module, Duration (s)
    4. Skipped         – #, Test ID, Module, Duration (s)
    5. Execution Metrics – Run At / Base URL / counts / pass rate / duration
    6. Defect Summary  – one row per failed test with Severity = LOW
    """
    # ── Load pytest JSON report ──────────────────────────────────────────────
    tests: list[dict] = []
    run_at = datetime.now(timezone.utc).isoformat()
    if JSON_REPORT_PATH.exists():
        data = json.loads(JSON_REPORT_PATH.read_text())
        run_at = data.get("created", run_at)
        for t in data.get("tests", []):
            # Keep one entry per parametrized variant (matches demo behaviour).
            tests.append({
                "nodeid":     t["nodeid"],
                "status":     t.get("outcome", "unknown"),
                "duration_s": round(t.get("duration", 0.0), 3),
                "module":     t["nodeid"].split("::")[0],
                "markers":    "",   # pytest-json-report doesn't surface markers
            })
    else:
        print(
            f"[info] no pytest-json-report at {JSON_REPORT_PATH}; "
            "producing an empty execution report.",
            file=sys.stderr,
        )

    sorted_tests = sorted(tests, key=lambda t: t["nodeid"])
    passed  = [t for t in sorted_tests if t["status"] == "passed"]
    failed  = [t for t in sorted_tests if t["status"] == "failed"]
    skipped = [t for t in sorted_tests if t["status"] == "skipped"]
    executed = len(passed) + len(failed)
    pass_rate = round(len(passed) / executed * 100, 2) if executed else 0.0
    total_duration = round(sum(t["duration_s"] for t in sorted_tests), 3)

    wb = Workbook()

    # ── Sheet 1: Executed Tests ──────────────────────────────────────────────
    ws = wb.active
    ws.title = "Executed Tests"
    _make_exec_header(
        ws, ["#", "Test ID", "Module", "Markers", "Status", "Duration (s)"],
        _HDR_EXECUTED,
    )
    for seq, t in enumerate(sorted_tests, start=1):
        status_upper = t["status"].upper()
        ws.append([
            seq,
            _test_id_from_nodeid(t["nodeid"]),
            _module_label_from_path(t["module"]),
            t.get("markers") or "",
            status_upper,
            t["duration_s"],
        ])
        row_idx = ws.max_row
        cell_color = _STATUS_CELL.get(t["status"])
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

    # ── Sheets 2-4: Passed / Failed / Skipped ───────────────────────────────
    sheet_defs = [
        ("Passed",  passed,  _HDR_PASSED),
        ("Failed",  failed,  _HDR_FAILED),
        ("Skipped", skipped, _HDR_SKIPPED),
    ]
    for sheet_name, subset, hdr_color in sheet_defs:
        sh = wb.create_sheet(sheet_name)
        _make_exec_header(sh, ["#", "Test ID", "Module", "Duration (s)"], hdr_color)
        for seq, t in enumerate(subset, start=1):
            sh.append([
                seq,
                _test_id_from_nodeid(t["nodeid"]),
                _module_label_from_path(t["module"]),
                t["duration_s"],
            ])
            for col in range(1, 5):
                sh.cell(row=sh.max_row, column=col).alignment = Alignment(
                    vertical="center"
                )
        for col_letter, width in zip("ABCD", [7, 50, 39, 16]):
            sh.column_dimensions[col_letter].width = width

    # ── Sheet 5: Execution Metrics ───────────────────────────────────────────
    metrics = wb.create_sheet("Execution Metrics")
    bold_font = Font(bold=True)
    metrics.cell(row=1, column=1, value="Metric").font = bold_font
    metrics.cell(row=1, column=2, value="Value").font  = bold_font
    for metric, value in [
        ("Run At",             run_at),
        ("Base URL",           "(backend API tests — no browser URL)"),
        ("Total Tests",        len(sorted_tests)),
        ("Passed",             len(passed)),
        ("Failed",             len(failed)),
        ("Skipped",            len(skipped)),
        ("Pass Rate (%)",      pass_rate),
        ("Total Duration (s)", total_duration),
    ]:
        metrics.append([metric, value])
    metrics.column_dimensions["A"].width = 22
    metrics.column_dimensions["B"].width = 49

    # ── Sheet 6: Defect Summary ──────────────────────────────────────────────
    defects = wb.create_sheet("Defect Summary")
    _make_exec_header(
        defects, ["#", "Defect / Test ID", "Module", "Severity"], _HDR_FAILED
    )
    for seq, t in enumerate(failed, start=1):
        defects.append([
            seq,
            _test_id_from_nodeid(t["nodeid"]),
            _module_label_from_path(t["module"]),
            "LOW",
        ])
        for col in range(1, 5):
            defects.cell(row=defects.max_row, column=col).alignment = Alignment(
                vertical="center"
            )
    defects.column_dimensions["A"].width = 6
    defects.column_dimensions["B"].width = 50
    defects.column_dimensions["C"].width = 39
    defects.column_dimensions["D"].width = 12

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    print(
        f"Wrote {out_path} "
        f"({len(sorted_tests)} tests · {len(passed)} passed · "
        f"{len(failed)} failed · {len(skipped)} skipped)"
    )


def main():
    cases = collect_all_test_cases()
    collected_total, ran_total = attach_results(cases)
    write_catalog(cases, OUTPUT_DIR / "test-case-catalog.xlsx", authoritative_total=collected_total)
    write_findings(cases, OUTPUT_DIR / "findings.xlsx")
    write_execution_xlsx(OUTPUT_DIR / "Automation_Test_Report.xlsx")


if __name__ == "__main__":
    main()
