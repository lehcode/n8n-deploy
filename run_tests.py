#!/usr/bin/env python3
"""
Test runner script for n8n-deploy project
Provides convenient way to run different test suites with various options
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_verbosity_level(quiet):
    """Determine output level: quiet=False, normal=True"""
    if quiet:
        return False
    return True  # Default to normal output level


def check_dependencies():
    """Check if required test dependencies are installed"""
    print("🔍 Checking test dependencies...")

    required_packages = ["pytest", "pytest-cov", "pytest-mock"]

    missing_packages = []

    # Map package names to their import names
    package_import_map = {
        "pytest": "pytest",
        "pytest-cov": "pytest_cov",
        "pytest-mock": "pytest_mock",
    }

    for package in required_packages:
        import_name = package_import_map.get(package, package.replace("-", "_"))
        code, _, _ = run_command(f"python -c 'import {import_name}'")
        if code != 0:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("📦 Install with: pip install -e .[test]")
        return False

    print("✅ All test dependencies are installed")
    return True


def run_unit_tests(quiet=False, coverage=False, test_class=None):
    """Run unit tests"""
    if test_class:
        print(f"🧪 Running unit tests for class: {test_class}")
    else:
        print("🧪 Running unit tests...")

    cmd = "python -m pytest tests/unit/"

    # Add class filter if specified
    if test_class:
        # Use -k to filter by class name
        cmd += f" -k {test_class}"

    if quiet:
        cmd += " -q"  # Quiet mode
    # Default output from pyproject.toml (-v)

    if coverage:
        cmd += " --cov=api --cov-report=html --cov-report=term"

    # Use real-time output unless quiet mode
    if quiet:
        code, stdout, stderr = run_command(cmd)
    else:
        code = subprocess.run(cmd, shell=True).returncode
        stdout = stderr = ""

    if code == 0:
        print("✅ Unit tests passed")
        if coverage:
            print("📊 Coverage report generated:")
            print("   - HTML report: htmlcov/index.html")
            print("   - Terminal report displayed above")
    else:
        print("❌ Unit tests failed")
        if quiet and stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                    print(line)
        if quiet and stderr:
            print(f"Error: {stderr}")

    return code == 0


def run_integration_tests(quiet=False, test_class=None):
    """Run integration tests (excluding E2E manual tests)"""
    if test_class:
        print(f"🔗 Running integration tests for class: {test_class}")
    else:
        print("🔗 Running integration tests...")

    # Set environment variable for integration tests
    env = os.environ.copy()
    env["N8N_DEPLOY_TESTING"] = "1"

    # Exclude E2E manual tests from regular integration tests
    cmd = "N8N_DEPLOY_TESTING=1 python -m pytest tests/integration/ --ignore=tests/integration/test_e2e_manual_cli.py --ignore=tests/integration/test_e2e_manual_database.py --ignore=tests/integration/test_e2e_manual_apikeys.py --ignore=tests/integration/test_e2e_manual_workflows.py --ignore=tests/integration/test_e2e_manual_server.py"

    # Add class filter if specified
    if test_class:
        # Use -k to filter by class name
        cmd += f" -k {test_class}"

    if quiet:
        cmd += " -q"  # Quiet mode
    # Default output from pyproject.toml (-v)

    # Use real-time output unless quiet mode
    if quiet:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, env=env)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except Exception as e:
            code, stdout, stderr = 1, "", str(e)
    else:
        code = subprocess.run(cmd, shell=True, env=env).returncode
        stdout = stderr = ""

    if code == 0:
        print("✅ Integration tests passed")
    else:
        print("❌ Integration tests failed")
        if quiet and stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                    print(line)
        if quiet and stderr:
            print(f"Error: {stderr}")

    return code == 0


def run_e2e_tests(quiet=False, test_class=None):
    """Run End-to-End manual tests"""
    if test_class:
        print(f"🎭 Running E2E manual tests for class: {test_class}")
    else:
        print("🎭 Running E2E manual tests...")

    # Set environment variable for E2E tests
    env = os.environ.copy()
    env["N8N_DEPLOY_TESTING"] = "1"

    # Run only E2E manual tests
    cmd = "N8N_DEPLOY_TESTING=1 python -m pytest tests/integration/test_e2e_manual_*.py"

    # Add class filter if specified
    if test_class:
        # Use -k to filter by class name
        cmd += f" -k {test_class}"

    if quiet:
        cmd += " -q"  # Quiet mode
    # Default output from pyproject.toml (-v)

    # Use real-time output unless quiet mode
    if quiet:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, env=env)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except Exception as e:
            code, stdout, stderr = 1, "", str(e)
    else:
        code = subprocess.run(cmd, shell=True, env=env).returncode
        stdout = stderr = ""

    if code == 0:
        print("✅ E2E manual tests passed")
    else:
        print("❌ E2E manual tests failed")
        if quiet and stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                    print(line)
        if quiet and stderr:
            print(f"Error: {stderr}")

    return code == 0


def run_specific_test(test_path, quiet=False):
    """Run a specific test file or test function"""
    print(f"🎯 Running specific test: {test_path}")

    cmd = f"python -m pytest {test_path}"
    if quiet:
        cmd += " -q"

    # Use real-time output unless quiet mode
    if quiet:
        code, stdout, stderr = run_command(cmd)
    else:
        code = subprocess.run(cmd, shell=True).returncode
        stdout = stderr = ""

    if code == 0:
        print("✅ Specific test passed")
    else:
        print("❌ Specific test failed")
        if stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                    print(line)
        if stderr:
            print(f"Error: {stderr}")

    return code == 0


def run_hypothesis_tests(quiet=False, show_statistics=False):
    """Run property-based tests with Hypothesis"""
    print("🔬 Running property-based tests (Hypothesis)...")

    # Set environment variable for tests
    env = os.environ.copy()
    env["N8N_DEPLOY_TESTING"] = "1"

    cmd = "python -m pytest tests/generators/hypothesis_generator.py -v --tb=short"
    if show_statistics:
        cmd += " --hypothesis-show-statistics"
    if quiet:
        cmd += " -q"

    # Use real-time output unless quiet mode
    if quiet:
        code, stdout, stderr = run_command(cmd)
    else:
        # Run with environment and real-time output
        code = subprocess.run(cmd, shell=True, env=env).returncode
        stdout = stderr = ""

    if code == 0:
        print("✅ Property-based tests passed (755 generated examples)")
    else:
        print("❌ Property-based tests failed")
        if quiet and stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line or "Falsifying example" in line:
                    print(line)
        if stderr:
            print(f"Error: {stderr}")

    return code == 0


def run_generated_tests(quiet=False):
    """Run auto-generated CLI tests"""
    print("🤖 Running auto-generated CLI tests...")

    # Set environment variable for tests
    env = os.environ.copy()
    env["N8N_DEPLOY_TESTING"] = "1"

    cmd = "python -m pytest tests/generated/test_cli_generated.py -v --tb=short"
    if quiet:
        cmd += " -q"

    # Run command with environment
    code = subprocess.run(cmd, shell=True, env=env, capture_output=quiet, text=True).returncode
    stdout = stderr = ""

    if code == 0:
        print("✅ Auto-generated CLI tests passed (88 test scenarios)")
    else:
        print("❌ Auto-generated CLI tests failed")
        if quiet and stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line:
                    print(line)
        if stderr:
            print(f"Error: {stderr}")

    return code == 0


def run_all_tests(quiet=False, coverage=False, include_e2e=False):
    """Run all tests"""
    if include_e2e:
        print("🚀 Running all tests (including E2E)...")
    else:
        print("🚀 Running all tests (unit + integration)...")

    # Run unit tests first
    print("\n📋 Running unit tests...")
    unit_success = run_unit_tests(quiet, coverage)

    # Run integration tests second
    print("\n📋 Running integration tests...")
    integration_success = run_integration_tests(quiet)

    # Run E2E tests if requested
    e2e_success = True
    if include_e2e:
        print("\n📋 Running E2E manual tests...")
        e2e_success = run_e2e_tests(quiet)

    # Overall result
    success = unit_success and integration_success and e2e_success

    if success:
        if include_e2e:
            print("✅ All tests (unit + integration + E2E) passed")
        else:
            print("✅ All tests passed")
    else:
        print("❌ Some tests failed")
        if not unit_success:
            print("   - Unit tests had failures")
        if not integration_success:
            print("   - Integration tests had failures")
        if include_e2e and not e2e_success:
            print("   - E2E manual tests had failures")

    return success


def run_fast_tests(quiet=False):
    """Run fast tests only (excluding slow integration tests)"""
    print("⚡ Running fast tests only...")

    cmd = "python -m pytest tests/ -m 'not slow'"
    # Verbose is default mode

    # Use real-time output unless quiet mode
    if quiet:
        code, stdout, stderr = run_command(cmd)
    else:
        code = subprocess.run(cmd, shell=True).returncode
        stdout = stderr = ""

    if code == 0:
        print("✅ Fast tests passed")
    else:
        print("❌ Fast tests failed")
        if quiet and stdout:
            # Show failure summary in quiet mode
            lines = stdout.split("\n")
            for line in lines:
                if "FAILED" in line or "ERROR" in line or "short test summary" in line:
                    print(line)
        if quiet and stderr:
            print(f"Error: {stderr}")

    return code == 0


def check_code_quality():
    """Run code quality checks"""
    print("🧹 Running code quality checks...")

    success = True

    # Check if tools are available
    print("  Checking Black formatting...")
    code, _, _ = run_command("python -m black --check api/")
    if code != 0:
        print("  ❌ Code formatting issues found. Run: black api/")
        success = False
    else:
        print("  ✅ Code formatting is correct")

    print("  Checking MyPy type hints...")
    code, _, stderr = run_command("python -m mypy api/")
    if code != 0:
        print("  ❌ Type checking issues found")
        if stderr:
            print(f"  Error: {stderr}")
        success = False
    else:
        print("  ✅ Type checking passed")

    return success


def generate_test_report(include_e2e=False):
    """Generate comprehensive test report"""
    if include_e2e:
        print("📊 Generating comprehensive test report (including E2E)...")
        # Run all tests including E2E with coverage and JUnit XML output
        cmd = "N8N_DEPLOY_TESTING=1 python -m pytest tests/ --cov=api --cov-report=html --cov-report=xml --cov-report=term --junit-xml=test-results.xml -v"
    else:
        print("📊 Generating comprehensive test report...")
        # Run tests excluding E2E manual tests
        cmd = "N8N_DEPLOY_TESTING=1 python -m pytest tests/ --ignore=tests/integration/test_e2e_manual_cli.py --ignore=tests/integration/test_e2e_manual_database.py --ignore=tests/integration/test_e2e_manual_apikeys.py --ignore=tests/integration/test_e2e_manual_workflows.py --ignore=tests/integration/test_e2e_manual_server.py --cov=api --cov-report=html --cov-report=xml --cov-report=term --junit-xml=test-results.xml -v"

    # Set environment variable
    env = os.environ.copy()
    env["N8N_DEPLOY_TESTING"] = "1"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, env=env)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except Exception as e:
        code, stdout, stderr = 1, "", str(e)

    if code == 0:
        print("✅ Test report generated successfully")
        print("📄 Coverage report: htmlcov/index.html")
        print("📄 JUnit XML: test-results.xml")
    else:
        print("❌ Failed to generate test report")
        if stdout:
            print(f"Output:\n{stdout}")
        if stderr:
            print(f"Error:\n{stderr}")

    return code == 0


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="n8n-deploy Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --integration            # Run integration tests only (excluding E2E)
  python run_tests.py --e2e                    # Run E2E manual tests only
  python run_tests.py --integration --class TestE2EDatabase  # Run specific test class
  python run_tests.py --integration --class TestE2EEnv       # Run env tests only
  python run_tests.py --integration --class TestE2EWorkflows # Run wf tests only
  python run_tests.py --integration --class TestE2EAPIKeys   # Run API key tests only
  python run_tests.py --integration --class TestE2EServer    # Run server tests only
  python run_tests.py --hypothesis             # Run property-based tests with Hypothesis
  python run_tests.py --fast                   # Run fast tests only
  python run_tests.py --all                    # Run all tests (unit + integration, excluding E2E)
  python run_tests.py --all-e2e                # Run all tests including E2E manual tests
  python run_tests.py --unit --coverage        # Run unit tests with coverage
  python run_tests.py --quality                # Run code quality checks
  python run_tests.py --specific tests/unit/test_models.py  # Run specific test
  python run_tests.py --report                 # Generate comprehensive report (excluding E2E)
  python run_tests.py --report-e2e             # Generate comprehensive report including E2E

Note: You must specify a test type (--unit, --integration, --e2e, --hypothesis, --fast, --all, --all-e2e, --report, --report-e2e, --quality, or --specific)
        """,
    )

    parser.add_argument("--unit", action="store_true", help="Run unit tests only")

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only (excluding E2E)",
    )

    parser.add_argument("--e2e", action="store_true", help="Run E2E manual tests only")

    parser.add_argument(
        "--hypothesis", action="store_true", help="Run property-based tests with Hypothesis (755 generated examples)"
    )

    parser.add_argument("--generated", action="store_true", help="Run auto-generated CLI tests (all commands and options)")

    parser.add_argument("--fast", action="store_true", help="Run fast tests only (excluding slow tests)")

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (unit + integration, excluding E2E)",
    )

    parser.add_argument(
        "--all-e2e",
        action="store_true",
        help="Run all tests including E2E manual tests",
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run all tests with coverage reporting (or combine with --unit)"
    )

    parser.add_argument("--quality", action="store_true", help="Run code quality checks (black, mypy)")

    parser.add_argument("--specific", type=str, help="Run specific test file or function")

    parser.add_argument(
        "--class",
        type=str,
        dest="test_class",
        help="Run tests for a specific test class (e.g., TestE2EDatabase, TestE2EEnv)",
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report (excluding E2E)",
    )

    parser.add_argument(
        "--report-e2e",
        action="store_true",
        help="Generate comprehensive test report including E2E",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet output (suppress default output)",
    )
    parser.add_argument("--no-deps-check", action="store_true", help="Skip dependency check")

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print("🎭 n8n-deploy Test Runner")
    print("=" * 50)

    # Check dependencies unless skipped
    if not args.no_deps_check and not check_dependencies():
        return 1

    success = True

    # Run code quality checks if requested
    if args.quality:
        success &= check_code_quality()

    # Run specific test if requested
    if args.specific:
        success &= run_specific_test(args.specific, args.quiet)

    # Run test suites - require explicit test type selection
    if args.unit:
        success &= run_unit_tests(args.quiet, args.coverage, args.test_class)

    elif args.integration:
        success &= run_integration_tests(args.quiet, args.test_class)

    elif args.e2e:
        success &= run_e2e_tests(args.quiet, args.test_class)

    elif args.hypothesis:
        success &= run_hypothesis_tests(args.quiet, show_statistics=not args.quiet)

    elif args.generated:
        success &= run_generated_tests(args.quiet)

    elif args.fast:
        success &= run_fast_tests(args.quiet)

    elif args.all:
        success &= run_all_tests(args.quiet, args.coverage, include_e2e=False)

    elif args.all_e2e:
        success &= run_all_tests(args.quiet, args.coverage, include_e2e=True)

    elif args.report:
        success &= generate_test_report(include_e2e=False)

    elif args.report_e2e:
        success &= generate_test_report(include_e2e=True)

    elif args.coverage:
        # If --coverage is specified alone, run all tests with coverage
        success &= run_all_tests(args.quiet, coverage=True, include_e2e=False)

    elif not args.quality and not args.specific:
        # No test type specified - show help and exit
        print("❌ No test type specified!")
        print("📋 Available options:")
        print("  --unit         Run unit tests only")
        print("  --integration  Run integration tests only (excluding E2E)")
        print("  --e2e          Run E2E manual tests only")
        print("  --fast         Run fast tests only")
        print("  --all          Run all tests (unit + integration, excluding E2E)")
        print("  --all-e2e      Run all tests including E2E manual tests")
        print("  --coverage     Run all tests with coverage reporting")
        print("  --report       Generate comprehensive test report (excluding E2E)")
        print("  --report-e2e   Generate comprehensive test report including E2E")
        print("  --quality      Run code quality checks")
        print("  --specific     Run specific test file/function")
        print("\n💡 Example: python run_tests.py --unit")
        return 1

    print("=" * 50)

    if success:
        print("🎉 All operations completed successfully!")
        return 0
    else:
        print("💥 Some operations failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
