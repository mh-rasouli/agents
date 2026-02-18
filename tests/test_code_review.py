"""Tests for CodeReviewAgent."""

import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from agents.code_review_agent import CodeReviewAgent, FileMetrics, SKIP_DIRS


# ─── FileMetrics Tests ────────────────────────────────────────────


class TestFileMetrics:
    """Tests for the FileMetrics helper class."""

    def test_basic_metrics(self):
        source = '''"""Module docstring."""

import os
from pathlib import Path

class Foo:
    """A class."""
    def bar(self):
        pass

    def baz(self):
        return 42

def standalone():
    # a comment
    return True
'''
        m = FileMetrics(source)
        assert m.total_lines > 0
        assert m.function_count == 3  # bar, baz, standalone
        assert m.class_count == 1
        assert m.import_count == 2
        assert "%" in m.comment_ratio

    def test_empty_source(self):
        m = FileMetrics("")
        assert m.total_lines == 0
        assert m.function_count == 0
        assert m.class_count == 0
        assert m.comment_ratio == "0%"

    def test_syntax_error_source(self):
        m = FileMetrics("def broken(:\n    pass")
        assert m.total_lines == 2
        assert m.function_count == 0  # Can't parse
        assert m.class_count == 0

    def test_to_dict(self):
        m = FileMetrics("x = 1\n# comment\n")
        d = m.to_dict()
        assert "total_lines" in d
        assert "function_count" in d
        assert "class_count" in d
        assert "import_count" in d
        assert "comment_ratio" in d


# ─── CodeReviewAgent Tests ────────────────────────────────────────


class TestCodeReviewAgent:
    """Tests for the CodeReviewAgent."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure for testing."""
        # Main module
        (tmp_path / "main.py").write_text(
            '"""Main module."""\nimport os\n\ndef main():\n    print("hello")\n'
        )

        # Module with issues
        (tmp_path / "bad_code.py").write_text(
            '"""Bad code."""\n'
            'import os\n'
            'password = "hunter2"\n'  # Hardcoded secret
            'eval("1+1")\n'  # eval usage
            'try:\n'
            '    x = 1\n'
            'except:\n'  # Bare except
            '    pass\n'
            '# TODO: fix this\n'
        )

        # A subdirectory with a module
        sub = tmp_path / "submodule"
        sub.mkdir()
        (sub / "__init__.py").write_text("")
        (sub / "helper.py").write_text(
            '"""Helper functions."""\n\ndef add(a, b):\n    return a + b\n'
        )

        # Test file
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text(
            '"""Tests."""\ndef test_main():\n    assert True\n'
        )

        # Excluded dir
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "junk.py").write_text("x = 1")

        return tmp_path

    @pytest.fixture
    def agent(self, temp_project):
        return CodeReviewAgent(project_root=str(temp_project))

    def test_init(self, agent, temp_project):
        assert agent.agent_name == "CodeReviewAgent"
        assert agent.project_root == temp_project

    def test_discover_files_finds_py_files(self, agent, temp_project):
        files = agent.discover_files()
        names = {f.name for f in files}
        assert "main.py" in names
        assert "bad_code.py" in names
        assert "helper.py" in names

    def test_discover_files_skips_pycache(self, agent):
        files = agent.discover_files()
        for f in files:
            assert "__pycache__" not in f.parts

    def test_discover_files_skips_small_init(self, agent):
        files = agent.discover_files()
        names = {f.name for f in files}
        assert "__init__.py" not in names

    def test_discover_files_target_single_file(self, agent, temp_project):
        target = str(temp_project / "main.py")
        files = agent.discover_files(target=target)
        assert len(files) == 1
        assert files[0].name == "main.py"

    def test_discover_files_target_directory(self, agent, temp_project):
        target = str(temp_project / "submodule")
        files = agent.discover_files(target=target)
        names = {f.name for f in files}
        assert "helper.py" in names
        assert "main.py" not in names

    def test_discover_files_exclude_tests(self, agent):
        files_with = agent.discover_files(include_tests=True)
        files_without = agent.discover_files(include_tests=False)
        assert len(files_with) >= len(files_without)
        test_names = {f.name for f in files_without}
        assert all(not n.startswith("test_") for n in test_names)

    def test_static_review_detects_bare_except(self, agent, temp_project):
        files = [temp_project / "bad_code.py"]
        report = agent.review_files(files, parallel=False)

        all_findings = []
        for review in report.get("file_reviews", []):
            all_findings.extend(review.get("findings", []))

        bare_except = [
            f for f in all_findings
            if f["category"] == "error_handling" and "except" in f["issue"].lower()
        ]
        assert len(bare_except) > 0

    def test_static_review_detects_eval(self, agent, temp_project):
        files = [temp_project / "bad_code.py"]
        report = agent.review_files(files, parallel=False)

        all_findings = []
        for review in report.get("file_reviews", []):
            all_findings.extend(review.get("findings", []))

        eval_issues = [
            f for f in all_findings
            if f["category"] == "security" and "eval" in f["issue"].lower()
        ]
        assert len(eval_issues) > 0

    def test_static_review_detects_todo(self, agent, temp_project):
        files = [temp_project / "bad_code.py"]
        report = agent.review_files(files, parallel=False)

        all_findings = []
        for review in report.get("file_reviews", []):
            all_findings.extend(review.get("findings", []))

        todos = [f for f in all_findings if "TODO" in f.get("issue", "")]
        assert len(todos) > 0

    def test_review_report_structure(self, agent, temp_project):
        files = agent.discover_files()
        report = agent.review_files(files, parallel=False)

        # Top-level keys
        assert "timestamp" in report
        assert "project_root" in report
        assert "files_reviewed" in report
        assert "review_time_seconds" in report
        assert "overall_score" in report
        assert "summary" in report
        assert "project_metrics" in report
        assert "file_reviews" in report
        assert "errors" in report

        # Summary keys
        assert "total_findings" in report["summary"]
        assert "by_severity" in report["summary"]
        assert "by_category" in report["summary"]

    def test_review_clean_file(self, agent, temp_project):
        files = [temp_project / "submodule" / "helper.py"]
        report = agent.review_files(files, parallel=False)

        assert report["files_reviewed"] == 1
        review = report["file_reviews"][0]
        assert review["overall_score"] >= 8  # Clean file should score well

    def test_empty_file_skipped(self, agent, temp_project):
        empty = temp_project / "empty.py"
        empty.write_text("")

        files = [empty]
        report = agent.review_files(files, parallel=False)
        assert report["files_reviewed"] == 0

    def test_markdown_report_generation(self, agent, temp_project):
        files = agent.discover_files()
        report = agent.review_files(files, parallel=False)
        md = agent.generate_markdown_report(report)

        assert "# Code Review Report" in md
        assert "## Summary" in md
        assert "## Project Metrics" in md
        assert "## File-by-File Review" in md
        assert "Generated by CodeReviewAgent" in md

    def test_save_report_json(self, agent, temp_project):
        files = [temp_project / "main.py"]
        report = agent.review_files(files, parallel=False)

        out_dir = str(temp_project / "reports")
        saved = agent.save_report(report, output_dir=out_dir, formats=["json"])

        assert "json" in saved
        assert os.path.exists(saved["json"])

        with open(saved["json"], "r") as f:
            loaded = json.load(f)
        assert loaded["files_reviewed"] == 1

    def test_save_report_md(self, agent, temp_project):
        files = [temp_project / "main.py"]
        report = agent.review_files(files, parallel=False)

        out_dir = str(temp_project / "reports")
        saved = agent.save_report(report, output_dir=out_dir, formats=["md"])

        assert "md" in saved
        assert os.path.exists(saved["md"])

        with open(saved["md"], "r") as f:
            content = f.read()
        assert "# Code Review Report" in content


class TestCodeReviewAgentLLM:
    """Tests for LLM-powered review (mocked)."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        (tmp_path / "sample.py").write_text(
            '"""Sample."""\ndef foo():\n    return 1\n'
        )
        return tmp_path

    @pytest.fixture
    def agent(self, temp_project):
        return CodeReviewAgent(project_root=str(temp_project))

    def test_llm_review_called_when_available(self, agent, temp_project):
        mock_response = json.dumps({
            "file_path": "sample.py",
            "overall_score": 9,
            "summary": "Clean code.",
            "findings": [],
            "strengths": ["Good docstring"],
            "metrics": {},
        })

        with patch.object(agent.llm, "is_available", return_value=True), \
             patch.object(agent.llm, "generate", return_value=mock_response):
            files = [temp_project / "sample.py"]
            report = agent.review_files(files, parallel=False)

            assert report["files_reviewed"] == 1
            assert report["file_reviews"][0]["overall_score"] == 9

    def test_llm_failure_falls_back_to_static(self, agent, temp_project):
        with patch.object(agent.llm, "is_available", return_value=True), \
             patch.object(agent.llm, "generate", side_effect=Exception("API error")):
            files = [temp_project / "sample.py"]
            report = agent.review_files(files, parallel=False)

            # Should still produce a report via static fallback
            assert report["files_reviewed"] == 1

    def test_llm_unavailable_uses_static(self, agent, temp_project):
        with patch.object(agent.llm, "is_available", return_value=False):
            files = [temp_project / "sample.py"]
            report = agent.review_files(files, parallel=False)
            assert report["files_reviewed"] == 1


# ─── Mutable default argument detection ──────────────────────────


class TestStaticChecks:
    """Test specific static analysis checks."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path

    @pytest.fixture
    def agent(self, temp_project):
        return CodeReviewAgent(project_root=str(temp_project))

    def test_mutable_default_detected(self, agent, temp_project):
        code = 'def foo(items=[]):\n    items.append(1)\n    return items\n'
        (temp_project / "mutable.py").write_text(code)

        report = agent.review_files([temp_project / "mutable.py"], parallel=False)
        findings = report["file_reviews"][0]["findings"]
        mutable = [f for f in findings if "mutable" in f["issue"].lower()]
        assert len(mutable) > 0

    def test_long_function_detected(self, agent, temp_project):
        lines = ["def long_function():"]
        for i in range(55):
            lines.append(f"    x_{i} = {i}")
        lines.append("    return x_0")
        code = "\n".join(lines) + "\n"
        (temp_project / "long_func.py").write_text(code)

        report = agent.review_files([temp_project / "long_func.py"], parallel=False)
        findings = report["file_reviews"][0]["findings"]
        long_fn = [f for f in findings if "long" in f["issue"].lower() or "lines" in f["issue"].lower()]
        assert len(long_fn) > 0

    def test_hardcoded_secret_detected(self, agent, temp_project):
        code = 'API_KEY = "sk-abc123secret"\npassword = "admin123"\n'
        (temp_project / "secrets.py").write_text(code)

        report = agent.review_files([temp_project / "secrets.py"], parallel=False)
        findings = report["file_reviews"][0]["findings"]
        secrets = [f for f in findings if f["category"] == "security"]
        assert len(secrets) > 0
