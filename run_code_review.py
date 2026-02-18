#!/usr/bin/env python3
"""CLI entry point for running automated code reviews.

Usage:
    # Review entire project
    python run_code_review.py

    # Review specific file
    python run_code_review.py --target agents/base_agent.py

    # Review a directory
    python run_code_review.py --target scrapers/

    # Filter by minimum severity
    python run_code_review.py --min-severity high

    # Skip test files
    python run_code_review.py --no-tests

    # Output only JSON
    python run_code_review.py --format json

    # Custom output directory
    python run_code_review.py --output-dir reports/
"""

import argparse
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.code_review_agent import CodeReviewAgent
from utils.logger import get_logger

logger = get_logger(__name__)

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def filter_report_by_severity(report: dict, min_severity: str) -> dict:
    """Filter report findings to only include issues at or above min_severity.

    Args:
        report: The full review report.
        min_severity: Minimum severity to include.

    Returns:
        Filtered report (modifies file_reviews in place).
    """
    threshold = SEVERITY_ORDER.index(min_severity)
    allowed = set(SEVERITY_ORDER[: threshold + 1])

    for review in report.get("file_reviews", []):
        review["findings"] = [
            f for f in review.get("findings", [])
            if f.get("severity") in allowed
        ]

    # Recompute summary counts
    all_findings = []
    for review in report.get("file_reviews", []):
        for f in review.get("findings", []):
            f["file_path"] = review.get("file_path", "unknown")
            all_findings.append(f)

    severity_counts = {}
    category_counts = {}
    for f in all_findings:
        sev = f.get("severity", "info")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        cat = f.get("category", "other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    top_issues = [f for f in all_findings if f.get("severity") in ("critical", "high")]

    report["summary"] = {
        "total_findings": len(all_findings),
        "by_severity": severity_counts,
        "by_category": category_counts,
        "top_issues": top_issues[:10],
    }

    return report


def print_summary(report: dict) -> None:
    """Print a concise summary to stdout."""
    summary = report.get("summary", {})
    score = report.get("overall_score", "N/A")
    files = report.get("files_reviewed", 0)
    elapsed = report.get("review_time_seconds", 0)

    print(f"\n{'=' * 60}")
    print(f"  CODE REVIEW COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Files reviewed:  {files}")
    print(f"  Overall score:   {score}/10")
    print(f"  Total findings:  {summary.get('total_findings', 0)}")
    print(f"  Review time:     {elapsed:.1f}s")

    by_sev = summary.get("by_severity", {})
    if by_sev:
        print(f"\n  Findings by severity:")
        for sev in SEVERITY_ORDER:
            count = by_sev.get(sev, 0)
            if count > 0:
                marker = "!!" if sev in ("critical", "high") else "  "
                print(f"  {marker} {sev.upper():>10s}: {count}")

    top = summary.get("top_issues", [])
    if top:
        print(f"\n  Top issues:")
        for i, issue in enumerate(top[:5], 1):
            print(
                f"    {i}. [{issue.get('severity', '').upper()}] "
                f"{issue.get('file_path', '')}:{issue.get('line_range', '?')} "
                f"- {issue.get('issue', '')}"
            )

    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Automated Code Review for Brand Intelligence Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_code_review.py                          # Review entire project
  python run_code_review.py --target agents/         # Review agents directory
  python run_code_review.py --target graph.py        # Review single file
  python run_code_review.py --min-severity high      # Only high+ issues
  python run_code_review.py --no-tests --format json # Skip tests, JSON only
        """,
    )

    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="File or directory to review (default: entire project)",
    )
    parser.add_argument(
        "--min-severity",
        type=str,
        choices=SEVERITY_ORDER,
        default=None,
        help="Minimum severity level to report",
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Exclude test files from review",
    )
    parser.add_argument(
        "--format",
        type=str,
        nargs="+",
        choices=["json", "md"],
        default=["json", "md"],
        help="Output formats (default: json md)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for reports (default: output/code_review/)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print results to stdout without saving files",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Disable parallel file review (useful for debugging)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    print("\nStarting code review...")

    agent = CodeReviewAgent(project_root=str(project_root))

    # Discover files
    files = agent.discover_files(
        target=args.target,
        include_tests=not args.no_tests,
    )

    if not files:
        print("No Python files found to review.")
        sys.exit(0)

    print(f"Found {len(files)} file(s) to review")
    for f in files:
        print(f"  - {f.relative_to(project_root)}")

    # Run review
    report = agent.review_files(files, parallel=not args.sequential)

    # Filter by severity if requested
    if args.min_severity:
        report = filter_report_by_severity(report, args.min_severity)

    # Print summary
    print_summary(report)

    # Save or print
    if args.no_save:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        saved = agent.save_report(
            report,
            output_dir=args.output_dir,
            formats=args.format,
        )
        for fmt, path in saved.items():
            print(f"  {fmt.upper()} report: {path}")

    # Exit with non-zero if critical issues found
    severity_counts = report.get("summary", {}).get("by_severity", {})
    if severity_counts.get("critical", 0) > 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
