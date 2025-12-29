#!/usr/bin/env python3
"""
Code Quality Analysis Script

Non-blocking code quality check for pre-push hooks.
Analyzes Python files for complexity metrics and reports warnings.

Usage:
    ./scripts/code-quality-check.py           # Analyze changed files only
    ./scripts/code-quality-check.py --all     # Analyze all Python files
    ./scripts/code-quality-check.py --staged  # Analyze staged files only
"""

import argparse
import ast
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    """Severity levels for code quality issues."""

    INFO = "info"
    WARNING = "warning"


@dataclass
class Issue:
    """Represents a code quality issue."""

    message: str
    severity: Severity
    metric: str
    value: float
    threshold: float


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""

    path: str
    loc: int = 0
    mi: float = 100.0
    avg_cc: float = 1.0
    high_cc_functions: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    is_test: bool = False


# Thresholds
THRESHOLDS = {
    "production": {
        "loc_warning": 500,
        "loc_info": 300,
        "cc_warning": 20,
        "cc_info": 15,
        "mi_warning": 30,
        "mi_info": 50,
    },
    "test": {
        "loc_warning": 800,
        "loc_info": 500,
        "cc_warning": 25,
        "cc_info": 20,
        "mi_warning": 20,
        "mi_info": 30,
    },
}

# ANSI colors
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "gray": "\033[90m",
}


def colored(text: str, color: str) -> str:
    """Apply ANSI color to text."""
    if not sys.stdout.isatty():
        return text
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def calculate_complexity(node: ast.AST) -> int:
    """Calculate McCabe cyclomatic complexity for a function."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.comprehension):
            complexity += 1
    return complexity


def count_loc(content: str) -> int:
    """Count lines of code (excluding blanks and comments)."""
    lines = content.split("\n")
    return len([line for line in lines if line.strip() and not line.strip().startswith("#")])


def calculate_maintainability_index(loc: int, avg_cc: float) -> float:
    """Calculate maintainability index (simplified)."""
    if loc == 0:
        return 100.0
    volume = loc * 5  # Rough approximation of Halstead volume
    mi = 171 - 5.2 * math.log(volume + 1) - 0.23 * avg_cc - 16.2 * math.log(loc + 1)
    return max(0, min(100, mi))


def analyze_file(filepath: str) -> Optional[FileAnalysis]:
    """Analyze a Python file for code quality metrics."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        rel_path = os.path.relpath(filepath)
        is_test = "test" in rel_path.lower() or rel_path.startswith("tests/")

        # Calculate LOC
        loc = count_loc(content)

        # Calculate complexity for each function
        complexities = []
        high_cc_functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = calculate_complexity(node)
                complexities.append(cc)

                thresholds = THRESHOLDS["test" if is_test else "production"]
                if cc >= thresholds["cc_info"]:
                    high_cc_functions.append((node.name, node.lineno, cc))

        avg_cc = sum(complexities) / len(complexities) if complexities else 1.0
        mi = calculate_maintainability_index(loc, avg_cc)

        return FileAnalysis(
            path=rel_path,
            loc=loc,
            mi=round(mi, 1),
            avg_cc=round(avg_cc, 1),
            high_cc_functions=high_cc_functions,
            is_test=is_test,
        )

    except (SyntaxError, UnicodeDecodeError):
        return None


def check_thresholds(analysis: FileAnalysis) -> list[Issue]:
    """Check file against thresholds and return issues."""
    issues = []
    thresholds = THRESHOLDS["test" if analysis.is_test else "production"]

    # LOC checks
    if analysis.loc > thresholds["loc_warning"]:
        issues.append(
            Issue(
                message=f"LOC: {analysis.loc} (threshold: {thresholds['loc_warning']}) - consider splitting",
                severity=Severity.WARNING,
                metric="loc",
                value=analysis.loc,
                threshold=thresholds["loc_warning"],
            )
        )
    elif analysis.loc > thresholds["loc_info"] and not analysis.is_test:
        issues.append(
            Issue(
                message=f"LOC: {analysis.loc} (threshold: {thresholds['loc_info']})",
                severity=Severity.INFO,
                metric="loc",
                value=analysis.loc,
                threshold=thresholds["loc_info"],
            )
        )

    # MI checks
    if analysis.mi < thresholds["mi_warning"]:
        issues.append(
            Issue(
                message=f"MI: {analysis.mi} (threshold: {thresholds['mi_warning']}) - hard to maintain",
                severity=Severity.WARNING,
                metric="mi",
                value=analysis.mi,
                threshold=thresholds["mi_warning"],
            )
        )
    elif analysis.mi < thresholds["mi_info"] and not analysis.is_test:
        issues.append(
            Issue(
                message=f"MI: {analysis.mi} (threshold: {thresholds['mi_info']})",
                severity=Severity.INFO,
                metric="mi",
                value=analysis.mi,
                threshold=thresholds["mi_info"],
            )
        )

    # CC checks for individual functions
    for func_name, line, cc in analysis.high_cc_functions:
        if cc >= thresholds["cc_warning"]:
            issues.append(
                Issue(
                    message=f"Function '{func_name}' (line {line}) CC: {cc} (threshold: {thresholds['cc_warning']})",
                    severity=Severity.WARNING,
                    metric="cc",
                    value=cc,
                    threshold=thresholds["cc_warning"],
                )
            )
        elif cc >= thresholds["cc_info"] and not analysis.is_test:
            issues.append(
                Issue(
                    message=f"Function '{func_name}' (line {line}) CC: {cc} (threshold: {thresholds['cc_info']})",
                    severity=Severity.INFO,
                    metric="cc",
                    value=cc,
                    threshold=thresholds["cc_info"],
                )
            )

    return issues


def get_changed_files() -> list[str]:
    """Get list of changed Python files from git."""
    try:
        # Get files changed compared to origin/develop or origin/master
        for branch in ["origin/develop", "origin/master", "HEAD~1"]:
            result = subprocess.run(
                ["git", "diff", "--name-only", branch],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                files = [f for f in result.stdout.strip().split("\n") if f.endswith(".py") and os.path.exists(f)]
                if files:
                    return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return []


def get_staged_files() -> list[str]:
    """Get list of staged Python files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f.endswith(".py") and os.path.exists(f)]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def get_all_python_files(directories: list[str]) -> list[str]:
    """Get all Python files in specified directories."""
    files = []
    for directory in directories:
        if os.path.isdir(directory):
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(".py"):
                        files.append(os.path.join(root, filename))
    return files


def calculate_quality_score(analyses: list[FileAnalysis]) -> int:
    """Calculate overall quality score (0-100)."""
    if not analyses:
        return 100

    total_score = 0
    for analysis in analyses:
        # Base score from MI (0-100)
        file_score = analysis.mi

        # Penalty for high LOC
        if analysis.loc > 500:
            file_score -= 20
        elif analysis.loc > 300:
            file_score -= 10

        # Penalty for high CC functions
        for _, _, cc in analysis.high_cc_functions:
            if cc >= 20:
                file_score -= 10
            elif cc >= 15:
                file_score -= 5

        total_score += max(0, file_score)

    return int(total_score / len(analyses))


def print_report(analyses: list[FileAnalysis]) -> tuple[int, int]:
    """Print analysis report and return (warning_count, info_count)."""
    warning_count = 0
    info_count = 0

    # Header
    print()
    print(colored("=" * 64, "cyan"))
    print(colored("  Code Quality Analysis (non-blocking)", "bold"))
    print(colored("=" * 64, "cyan"))
    print()

    files_with_issues = []

    for analysis in analyses:
        issues = check_thresholds(analysis)
        if issues:
            analysis.issues = issues
            files_with_issues.append(analysis)

    if not files_with_issues:
        print(colored("  All files pass quality checks!", "cyan"))
        print()
    else:
        for analysis in files_with_issues:
            warnings = [i for i in analysis.issues if i.severity == Severity.WARNING]
            infos = [i for i in analysis.issues if i.severity == Severity.INFO]

            if warnings:
                print(colored(f"  {analysis.path}", "yellow"))
                warning_count += len(warnings)
            else:
                print(colored(f"  {analysis.path}", "blue"))

            info_count += len(infos)

            for issue in analysis.issues:
                if issue.severity == Severity.WARNING:
                    print(colored(f"    - {issue.message}", "yellow"))
                else:
                    print(colored(f"    - {issue.message}", "gray"))

            print()

    # Summary
    quality_score = calculate_quality_score(analyses)

    print(colored("-" * 64, "cyan"))

    summary_parts = []
    if warning_count:
        summary_parts.append(colored(f"{warning_count} warnings", "yellow"))
    if info_count:
        summary_parts.append(colored(f"{info_count} info", "gray"))
    if not summary_parts:
        summary_parts.append(colored("no issues", "cyan"))

    score_color = "cyan" if quality_score >= 70 else "yellow" if quality_score >= 50 else "red"

    print(f"  Summary: {', '.join(summary_parts)} | Quality score: {colored(f'{quality_score}/100', score_color)}")
    print(colored("-" * 64, "cyan"))
    print()

    return warning_count, info_count


def main() -> int:
    """Main entry point. Always returns 0 (non-blocking)."""
    parser = argparse.ArgumentParser(description="Code quality analysis (non-blocking)")
    parser.add_argument("--all", action="store_true", help="Analyze all Python files")
    parser.add_argument("--staged", action="store_true", help="Analyze staged files only")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show warnings")
    args = parser.parse_args()

    # Determine which files to analyze
    if args.all:
        files = get_all_python_files(["api", "tests"])
    elif args.staged:
        files = get_staged_files()
    else:
        files = get_changed_files()

    if not files:
        if not args.quiet:
            print(colored("No Python files to analyze.", "gray"))
        return 0

    # Analyze files
    analyses = []
    for filepath in files:
        analysis = analyze_file(filepath)
        if analysis and analysis.loc > 50:  # Skip tiny files
            analyses.append(analysis)

    if not analyses:
        if not args.quiet:
            print(colored("No significant Python files to analyze.", "gray"))
        return 0

    # Print report
    warning_count, _ = print_report(analyses)

    # Always return 0 (non-blocking)
    return 0


if __name__ == "__main__":
    sys.exit(main())
