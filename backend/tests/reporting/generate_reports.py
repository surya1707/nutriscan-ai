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


def main():
    cases = collect_all_test_cases()
    collected_total, ran_total = attach_results(cases)
    write_catalog(cases, OUTPUT_DIR / "test-case-catalog.xlsx", authoritative_total=collected_total)
    write_findings(cases, OUTPUT_DIR / "findings.xlsx")


if __name__ == "__main__":
    main()
