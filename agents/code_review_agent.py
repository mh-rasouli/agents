"""Code Review Agent - Automated code review using LLM analysis."""

import json
import os
import ast
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.base_agent import BaseAgent
from models import BrandIntelligenceState
from config.prompts import CODE_REVIEW_PROMPT
from utils import llm_client, get_logger, generate_timestamp, save_json

logger = get_logger(__name__)

# Files/directories to skip during review
SKIP_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    "data", "output", "state", "logs", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "cache", "test_data", ".claude",
}

SKIP_FILES = {
    "__init__.py",  # Usually just imports
}

MAX_FILE_SIZE = 50_000  # Skip files larger than 50KB (likely generated)
MAX_WORKERS = 3  # Parallel LLM review calls


class FileMetrics:
    """Compute basic code metrics from a Python source file."""

    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.total_lines = len(self.lines)
        self._tree = None
        try:
            self._tree = ast.parse(source)
        except SyntaxError:
            pass

    @property
    def function_count(self) -> int:
        if not self._tree:
            return 0
        return sum(
            1 for node in ast.walk(self._tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )

    @property
    def class_count(self) -> int:
        if not self._tree:
            return 0
        return sum(
            1 for node in ast.walk(self._tree)
            if isinstance(node, ast.ClassDef)
        )

    @property
    def import_count(self) -> int:
        if not self._tree:
            return 0
        return sum(
            1 for node in ast.walk(self._tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )

    @property
    def comment_ratio(self) -> str:
        comment_lines = sum(1 for line in self.lines if line.strip().startswith("#"))
        if self.total_lines == 0:
            return "0%"
        return f"{(comment_lines / self.total_lines) * 100:.1f}%"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_lines": self.total_lines,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "import_count": self.import_count,
            "comment_ratio": self.comment_ratio,
        }


class CodeReviewAgent(BaseAgent):
    """Agent that performs automated code review on Python source files.

    Can operate in two modes:
    1. Standalone mode: Review arbitrary files/directories via review_files()
    2. Pipeline mode: Review project files via execute() (LangGraph compatible)
    """

    def __init__(self, project_root: str = None):
        """Initialize the CodeReviewAgent.

        Args:
            project_root: Root directory of the project to review.
                         Defaults to the current working directory.
        """
        super().__init__(agent_name="CodeReviewAgent")
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.reviews: List[Dict[str, Any]] = []

    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Execute code review as part of the LangGraph pipeline.

        Reviews all Python files in the project and attaches results to state.

        Args:
            state: Current workflow state

        Returns:
            Updated state with code review results in state["outputs"]["code_review"]
        """
        self._log_start()

        try:
            files = self.discover_files()
            logger.info(f"Discovered {len(files)} Python files to review")

            results = self.review_files(files)

            # Attach to state outputs
            if "outputs" not in state or not state["outputs"]:
                state["outputs"] = {}
            state["outputs"]["code_review"] = results

            self._log_end(success=True)
        except Exception as e:
            self._add_error(state, f"Code review failed: {e}")
            self._log_end(success=False)

        return state

    def discover_files(
        self,
        target: str = None,
        include_tests: bool = True,
    ) -> List[Path]:
        """Discover Python files to review.

        Args:
            target: Specific file or directory to review. None = entire project.
            include_tests: Whether to include test files.

        Returns:
            List of Path objects for files to review.
        """
        if target:
            target_path = Path(target)
            if target_path.is_file():
                return [target_path]
            search_root = target_path
        else:
            search_root = self.project_root

        files = []
        for path in sorted(search_root.rglob("*.py")):
            # Skip excluded directories
            if any(skip in path.parts for skip in SKIP_DIRS):
                continue

            # Skip __init__.py unless it has significant content
            if path.name in SKIP_FILES:
                try:
                    if path.stat().st_size < 500:
                        continue
                except OSError:
                    continue

            # Skip test files if not wanted
            if not include_tests and path.name.startswith("test_"):
                continue

            # Skip oversized files
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    logger.warning(f"Skipping large file: {path} ({path.stat().st_size} bytes)")
                    continue
            except OSError:
                continue

            files.append(path)

        return files

    def review_files(
        self,
        files: List[Path],
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """Review a list of Python files.

        Args:
            files: List of file paths to review.
            parallel: Whether to review files in parallel.

        Returns:
            Complete review report as a dictionary.
        """
        start_time = time.time()
        self.reviews = []
        errors = []

        if parallel and len(files) > 1 and self.llm.is_available():
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(self._review_single_file, f): f for f in files
                }
                for future in as_completed(futures):
                    filepath = futures[future]
                    try:
                        result = future.result()
                        if result:
                            self.reviews.append(result)
                    except Exception as e:
                        logger.error(f"Review failed for {filepath}: {e}")
                        errors.append({"file": str(filepath), "error": str(e)})
        else:
            for f in files:
                try:
                    result = self._review_single_file(f)
                    if result:
                        self.reviews.append(result)
                except Exception as e:
                    logger.error(f"Review failed for {f}: {e}")
                    errors.append({"file": str(f), "error": str(e)})

        elapsed = time.time() - start_time

        report = self._build_report(elapsed, errors)
        return report

    def _review_single_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Review a single Python file.

        Args:
            filepath: Path to the file to review.

        Returns:
            Review result dict, or None if file can't be read.
        """
        try:
            source = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Cannot read {filepath}: {e}")
            return None

        if not source.strip():
            return None

        # Compute local metrics (no LLM needed)
        metrics = FileMetrics(source)

        # If LLM is available, get AI-powered review
        if self.llm.is_available():
            review = self._llm_review(filepath, source, metrics)
        else:
            review = self._static_review(filepath, source, metrics)

        return review

    def _llm_review(
        self, filepath: Path, source: str, metrics: FileMetrics
    ) -> Dict[str, Any]:
        """Perform LLM-powered code review.

        Args:
            filepath: Path to the file.
            source: File source code.
            metrics: Pre-computed file metrics.

        Returns:
            Review result dictionary.
        """
        relative_path = str(filepath.relative_to(self.project_root))

        # Truncate very long files to fit context window
        truncated = source[:30_000] if len(source) > 30_000 else source
        truncation_note = (
            "\n\n[FILE TRUNCATED - only first 30,000 characters shown]"
            if len(source) > 30_000
            else ""
        )

        prompt = (
            f"Review the following Python file: `{relative_path}`\n\n"
            f"```python\n{truncated}{truncation_note}\n```"
        )

        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=CODE_REVIEW_PROMPT,
                json_mode=True,
                temperature=0.3,  # Lower temperature for more consistent reviews
            )

            review = json.loads(response) if response else {}

            # Override file_path and metrics with our computed values
            review["file_path"] = relative_path
            review["metrics"] = metrics.to_dict()

            return review

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"LLM review failed for {relative_path}, falling back to static: {e}")
            return self._static_review(filepath, source, metrics)

    def _static_review(
        self, filepath: Path, source: str, metrics: FileMetrics
    ) -> Dict[str, Any]:
        """Perform static analysis without LLM (fallback mode).

        Checks for common issues using AST and pattern matching.

        Args:
            filepath: Path to the file.
            source: File source code.
            metrics: Pre-computed file metrics.

        Returns:
            Review result dictionary.
        """
        relative_path = str(filepath.relative_to(self.project_root))
        findings = []

        lines = source.splitlines()

        # Check for bare except
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == "except:" or stripped == "except Exception:":
                findings.append({
                    "severity": "medium",
                    "category": "error_handling",
                    "line_range": str(i),
                    "issue": "Bare or overly broad except clause",
                    "suggestion": "Catch specific exceptions instead of bare except",
                    "code_snippet": stripped,
                })

        # Check for hardcoded secrets patterns
        secret_patterns = ["password", "secret", "api_key", "token"]
        for i, line in enumerate(lines, 1):
            lower = line.lower().replace(" ", "")
            if any(f"{p}=" in lower or f"{p} =" in line.lower() for p in secret_patterns):
                # Skip if it's a parameter name or env var lookup
                if "os.environ" in line or "settings." in line or "getenv" in line:
                    continue
                if '""' in line or "''" in line or "None" in line:
                    continue
                # Skip function parameter defaults and type annotations
                if "def " in line or "->" in line:
                    continue
                findings.append({
                    "severity": "high",
                    "category": "security",
                    "line_range": str(i),
                    "issue": "Possible hardcoded secret detected",
                    "suggestion": "Use environment variables or a secrets manager",
                    "code_snippet": line.strip()[:80],
                })

        # Check for eval/exec usage
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "eval(" in stripped or "exec(" in stripped:
                findings.append({
                    "severity": "critical",
                    "category": "security",
                    "line_range": str(i),
                    "issue": "Use of eval() or exec() detected",
                    "suggestion": "Avoid eval/exec. Use ast.literal_eval for safe parsing or refactor logic",
                    "code_snippet": stripped[:80],
                })

        # Check for mutable default arguments
        if metrics._tree:
            for node in ast.walk(metrics._tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in node.args.defaults + node.args.kw_defaults:
                        if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            findings.append({
                                "severity": "medium",
                                "category": "best_practices",
                                "line_range": str(node.lineno),
                                "issue": f"Mutable default argument in function '{node.name}'",
                                "suggestion": "Use None as default and initialize inside the function",
                                "code_snippet": None,
                            })

        # Check for long functions
        if metrics._tree:
            for node in ast.walk(metrics._tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end_line = getattr(node, "end_lineno", node.lineno + 50)
                    length = end_line - node.lineno
                    if length > 50:
                        findings.append({
                            "severity": "low",
                            "category": "code_quality",
                            "line_range": f"{node.lineno}-{end_line}",
                            "issue": f"Function '{node.name}' is {length} lines long",
                            "suggestion": "Consider breaking into smaller functions for readability",
                            "code_snippet": None,
                        })

        # Check for TODO/FIXME/HACK comments
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            for tag in ("TODO", "FIXME", "HACK", "XXX"):
                if tag in stripped and stripped.startswith("#"):
                    findings.append({
                        "severity": "info",
                        "category": "code_quality",
                        "line_range": str(i),
                        "issue": f"{tag} comment found",
                        "suggestion": "Track in issue tracker and resolve",
                        "code_snippet": stripped[:80],
                    })

        # Score based on findings
        severity_weights = {"critical": 3, "high": 2, "medium": 1, "low": 0.5, "info": 0}
        penalty = sum(severity_weights.get(f["severity"], 0) for f in findings)
        score = max(1, min(10, round(10 - penalty)))

        return {
            "file_path": relative_path,
            "overall_score": score,
            "summary": f"Static analysis found {len(findings)} issue(s) in {relative_path}.",
            "findings": findings,
            "strengths": [],
            "metrics": metrics.to_dict(),
        }

    def _build_report(
        self, elapsed: float, errors: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Build the final aggregated review report.

        Args:
            elapsed: Total review time in seconds.
            errors: List of file-level errors encountered.

        Returns:
            Complete review report dictionary.
        """
        all_findings = []
        for review in self.reviews:
            for finding in review.get("findings", []):
                finding["file_path"] = review.get("file_path", "unknown")
                all_findings.append(finding)

        # Count by severity
        severity_counts = {}
        for f in all_findings:
            sev = f.get("severity", "info")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Count by category
        category_counts = {}
        for f in all_findings:
            cat = f.get("category", "other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Average score
        scores = [r.get("overall_score", 5) for r in self.reviews if r.get("overall_score")]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        # Total metrics
        total_lines = sum(
            r.get("metrics", {}).get("total_lines", 0) for r in self.reviews
        )
        total_functions = sum(
            r.get("metrics", {}).get("function_count", 0) for r in self.reviews
        )
        total_classes = sum(
            r.get("metrics", {}).get("class_count", 0) for r in self.reviews
        )

        # Top issues (critical + high)
        top_issues = [
            f for f in all_findings if f.get("severity") in ("critical", "high")
        ]

        report = {
            "timestamp": generate_timestamp(),
            "project_root": str(self.project_root),
            "files_reviewed": len(self.reviews),
            "review_time_seconds": round(elapsed, 2),
            "overall_score": avg_score,
            "summary": {
                "total_findings": len(all_findings),
                "by_severity": severity_counts,
                "by_category": category_counts,
                "top_issues": top_issues[:10],
            },
            "project_metrics": {
                "total_lines": total_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
            },
            "file_reviews": self.reviews,
            "errors": errors,
        }

        return report

    def generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Convert a review report dict to a readable Markdown string.

        Args:
            report: The report dict from review_files().

        Returns:
            Formatted Markdown report string.
        """
        lines = []
        lines.append("# Code Review Report")
        lines.append(f"\n**Date:** {report.get('timestamp', 'N/A')}")
        lines.append(f"**Project:** `{report.get('project_root', 'N/A')}`")
        lines.append(f"**Files Reviewed:** {report.get('files_reviewed', 0)}")
        lines.append(f"**Review Time:** {report.get('review_time_seconds', 0):.1f}s")
        lines.append(f"**Overall Score:** {report.get('overall_score', 'N/A')}/10")

        # Summary
        summary = report.get("summary", {})
        lines.append("\n## Summary")
        lines.append(f"\nTotal findings: **{summary.get('total_findings', 0)}**")

        by_sev = summary.get("by_severity", {})
        if by_sev:
            lines.append("\n| Severity | Count |")
            lines.append("|----------|-------|")
            for sev in ("critical", "high", "medium", "low", "info"):
                if sev in by_sev:
                    lines.append(f"| {sev.upper()} | {by_sev[sev]} |")

        by_cat = summary.get("by_category", {})
        if by_cat:
            lines.append("\n| Category | Count |")
            lines.append("|----------|-------|")
            for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
                lines.append(f"| {cat} | {count} |")

        # Project metrics
        metrics = report.get("project_metrics", {})
        lines.append("\n## Project Metrics")
        lines.append(f"- **Total Lines:** {metrics.get('total_lines', 0):,}")
        lines.append(f"- **Total Functions:** {metrics.get('total_functions', 0)}")
        lines.append(f"- **Total Classes:** {metrics.get('total_classes', 0)}")

        # Top issues
        top = summary.get("top_issues", [])
        if top:
            lines.append("\n## Critical & High Priority Issues")
            for i, issue in enumerate(top, 1):
                lines.append(
                    f"\n### {i}. [{issue.get('severity', '').upper()}] "
                    f"`{issue.get('file_path', '')}` (line {issue.get('line_range', '?')})"
                )
                lines.append(f"**Category:** {issue.get('category', 'N/A')}")
                lines.append(f"**Issue:** {issue.get('issue', 'N/A')}")
                lines.append(f"**Suggestion:** {issue.get('suggestion', 'N/A')}")
                if issue.get("code_snippet"):
                    lines.append(f"```python\n{issue['code_snippet']}\n```")

        # Per-file details
        lines.append("\n## File-by-File Review")
        for review in report.get("file_reviews", []):
            fpath = review.get("file_path", "unknown")
            score = review.get("overall_score", "?")
            lines.append(f"\n### `{fpath}` - Score: {score}/10")

            if review.get("summary"):
                lines.append(f"\n{review['summary']}")

            strengths = review.get("strengths", [])
            if strengths:
                lines.append("\n**Strengths:**")
                for s in strengths:
                    lines.append(f"- {s}")

            findings = review.get("findings", [])
            if findings:
                lines.append(f"\n**Findings ({len(findings)}):**\n")
                lines.append("| # | Severity | Category | Line | Issue |")
                lines.append("|---|----------|----------|------|-------|")
                for j, f in enumerate(findings, 1):
                    lines.append(
                        f"| {j} | {f.get('severity', '')} | {f.get('category', '')} "
                        f"| {f.get('line_range', '')} | {f.get('issue', '')} |"
                    )

        # Errors
        errs = report.get("errors", [])
        if errs:
            lines.append("\n## Errors During Review")
            for err in errs:
                lines.append(f"- `{err.get('file', '')}`: {err.get('error', '')}")

        lines.append("\n---\n*Generated by CodeReviewAgent*")
        return "\n".join(lines)

    def save_report(
        self,
        report: Dict[str, Any],
        output_dir: str = None,
        formats: List[str] = None,
    ) -> Dict[str, str]:
        """Save the review report to files.

        Args:
            report: The review report dictionary.
            output_dir: Directory to save to. Defaults to output/code_review/.
            formats: List of formats to save ("json", "md"). Defaults to both.

        Returns:
            Dictionary mapping format to saved file path.
        """
        if formats is None:
            formats = ["json", "md"]

        if output_dir is None:
            output_dir = str(self.project_root / "output" / "code_review")

        os.makedirs(output_dir, exist_ok=True)

        saved = {}
        timestamp = report.get("timestamp", generate_timestamp()).replace(":", "-")

        if "json" in formats:
            json_path = os.path.join(output_dir, f"review_{timestamp}.json")
            save_json(report, json_path)
            saved["json"] = json_path
            logger.info(f"JSON report saved: {json_path}")

        if "md" in formats:
            md_content = self.generate_markdown_report(report)
            md_path = os.path.join(output_dir, f"review_{timestamp}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)
            saved["md"] = md_path
            logger.info(f"Markdown report saved: {md_path}")

        return saved
