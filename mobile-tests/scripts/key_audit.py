"""
Static audit: flags interactive Flutter widgets in mobile/lib that have
no `key:` argument, so new screens/PRs don't silently regress this
suite's ability to address them.

This is a heuristic grep-based check, not a Dart AST parser — it will
have false positives (e.g. a widget whose key is set two lines below
its constructor call) and false negatives (helper widgets that forward
`key` from a parent). Treat its output as a prompt for human review,
not a hard gate — the CI workflow calls it in --report-only mode; wire
it into `exit 1` on failure once the team is happy with a period of
observation.

Usage:
    python scripts/key_audit.py [--report-only]
"""

import argparse
import re
import sys
from pathlib import Path

MOBILE_LIB = Path(__file__).resolve().parents[2] / "mobile" / "lib"

INTERACTIVE_WIDGETS = [
    "ElevatedButton", "OutlinedButton", "TextButton", "IconButton",
    "FloatingActionButton", "GestureDetector", "InkWell", "TextField",
    "TextFormField", "Switch", "Checkbox", "Radio", "ListView",
    "BottomNavigationBar",
]

WIDGET_CALL_RE = re.compile(
    r"\b(" + "|".join(INTERACTIVE_WIDGETS) + r")(?:\.\w+)?\(",
)


def audit_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    for match in WIDGET_CALL_RE.finditer(text):
        start = match.end()
        # look at the next ~200 chars for a `key:` argument at this call's depth
        window = text[start:start + 200]
        if "key:" not in window and "key :" not in window:
            line_no = text.count("\n", 0, match.start()) + 1
            findings.append((line_no, match.group(1)))
    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    if not MOBILE_LIB.exists():
        print(f"mobile/lib not found at {MOBILE_LIB}", file=sys.stderr)
        sys.exit(1)

    total_findings = 0
    for dart_file in sorted(MOBILE_LIB.rglob("*.dart")):
        if dart_file.name.endswith(".g.dart"):
            continue  # generated code (Drift/json_serializable) — not test-relevant
        findings = audit_file(dart_file)
        if findings:
            rel = dart_file.relative_to(MOBILE_LIB.parent.parent)
            for line_no, widget in findings:
                print(f"{rel}:{line_no}: {widget}(...) has no key: within 200 chars")
                total_findings += 1

    print(f"\n{total_findings} unkeyed interactive widget(s) found.")
    if total_findings and not args.report_only:
        sys.exit(1)


if __name__ == "__main__":
    main()
