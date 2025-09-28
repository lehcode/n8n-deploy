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
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=False
        )
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


def run_unit_tests(quiet=False, coverage=False):
    """Run unit tests"""
    print("🧪 Running unit tests...")

    cmd = "python -m pytest tests/unit/"
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


def run_integration_tests(quiet=False):
    """Run integration tests"""
    print("🔗 Running integration tests...")

    # Set environment variable for integration tests
    env = os.environ.copy()
    env["N8N_DEPLOY_TESTING"] = "1"

    cmd = "N8N_DEPLOY_TESTING=1 python -m pytest tests/integration/"
    if quiet:
        cmd += " -q"  # Quiet mode
    # Default output from pyproject.toml (-v)

    # Use real-time output unless quiet mode
    if quiet:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, check=False, env=env
            )
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


def run_all_tests(quiet=False, coverage=False):
    """Run all tests"""
    print("🚀 Running all tests...")

    # Run unit tests first
    print("\n📋 Running unit tests...")
    unit_success = run_unit_tests(quiet, coverage)

    # Run integration tests second
    print("\n📋 Running integration tests...")
    integration_success = run_integration_tests(quiet)

    # Overall result
    success = unit_success and integration_success

    if success:
        print("✅ All tests passed")
    else:
        print("❌ Some tests failed")
        if not unit_success:
            print("   - Unit tests had failures")
        if not integration_success:
            print("   - Integration tests had failures")

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


def generate_test_report():
    """Generate comprehensive test report"""
    print("📊 Generating comprehensive test report...")

    # Run tests with coverage and JUnit XML output
    cmd = "python -m pytest tests/ --cov=api --cov-report=html --cov-report=xml --cov-report=term --junit-xml=test-results.xml -v"

    code, stdout, stderr = run_command(cmd)

    if code == 0:
        print("✅ Test report generated successfully")
        print("📄 Coverage report: htmlcov/index.html")
        print("📄 JUnit XML: test-results.xml")
    else:
        print("❌ Failed to generate test report")

    return code == 0


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="n8n-deploy Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --integration            # Run integration tests only
  python run_tests.py --fast                   # Run fast tests only
  python run_tests.py --all                    # Run all tests (unit + integration)
  python run_tests.py --unit --coverage        # Run unit tests with coverage
  python run_tests.py --quality                # Run code quality checks
  python run_tests.py --specific tests/unit/test_models.py  # Run specific test
  python run_tests.py --report                 # Generate comprehensive report

Note: You must specify a test type (--unit, --integration, --fast, --all, --report, --quality, or --specific)
        """,
    )

    parser.add_argument("--unit", action="store_true", help="Run unit tests only")

    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )

    parser.add_argument(
        "--fast", action="store_true", help="Run fast tests only (excluding slow tests)"
    )

    parser.add_argument(
        "--all", action="store_true", help="Run all tests (unit + integration)"
    )

    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage reporting"
    )

    parser.add_argument(
        "--quality", action="store_true", help="Run code quality checks (black, mypy)"
    )

    parser.add_argument(
        "--specific", type=str, help="Run specific test file or function"
    )

    parser.add_argument(
        "--report", action="store_true", help="Generate comprehensive test report"
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet output (suppress default output)",
    )
    parser.add_argument(
        "--no-deps-check", action="store_true", help="Skip dependency check"
    )

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
        success &= run_unit_tests(args.quiet, args.coverage)

    elif args.integration:
        success &= run_integration_tests(args.quiet)

    elif args.fast:
        success &= run_fast_tests(args.quiet)

    elif args.all:
        success &= run_all_tests(args.quiet, args.coverage)

    elif args.report:
        success &= generate_test_report()

    elif not args.quality and not args.specific:
        # No test type specified - show help and exit
        print("❌ No test type specified!")
        print("📋 Available options:")
        print("  --unit         Run unit tests only")
        print("  --integration  Run integration tests only")
        print("  --fast         Run fast tests only")
        print("  --all          Run all tests (unit + integration)")
        print("  --report       Generate comprehensive test report")
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
