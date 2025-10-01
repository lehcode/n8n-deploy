#!/usr/bin/env python3
"""
Python test runner for n8n-deploy manual test suite

Executes bash test scripts and provides:
- Parallel execution support
- Rich console output
- Test result aggregation
- CI-friendly reporting
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple
import argparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# ANSI color codes
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


class TestRunner:
    """Runs bash test scripts and aggregates results"""

    def __init__(self, verbose: bool = False, parallel: bool = False, stream: bool = False):
        self.verbose = verbose
        self.parallel = parallel
        self.stream = stream
        self.manual_dir = Path(__file__).parent
        self.test_files = sorted(self.manual_dir.glob("test_*.sh"))

    def run_test_file(self, test_file: Path) -> Tuple[str, int, str, str]:
        """Run a single test file and return results"""
        if self.stream:
            # Stream output in real-time
            print(f"{CYAN}Running {test_file.name}...{NC}\n")
            try:
                result = subprocess.run(
                    [str(test_file)], cwd=str(self.manual_dir), timeout=300  # 5 minute timeout per test file
                )
                return (test_file.name, result.returncode, "", "")
            except subprocess.TimeoutExpired:
                print(f"{RED}Test timed out after 5 minutes{NC}")
                return (test_file.name, -1, "", "Test timed out after 5 minutes")
            except Exception as e:
                print(f"{RED}Error: {e}{NC}")
                return (test_file.name, -1, "", str(e))
        else:
            # Capture output for later display
            print(f"{CYAN}Running {test_file.name}...{NC}")
            try:
                result = subprocess.run(
                    [str(test_file)],
                    cwd=str(self.manual_dir),
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout per test file
                )
                return (test_file.name, result.returncode, result.stdout, result.stderr)
            except subprocess.TimeoutExpired:
                return (test_file.name, -1, "", "Test timed out after 5 minutes")
            except Exception as e:
                return (test_file.name, -1, "", str(e))

    def parse_test_results(self, stdout: str) -> Tuple[int, int, int, int]:
        """Parse test results from output"""
        # Strip ANSI color codes first
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        clean_output = ansi_escape.sub("", stdout)

        # Extract summary: Total Tests: 8, Passed: 8, Failed: 0, Skipped: 0
        total_match = re.search(r"Total Tests:\s+(\d+)", clean_output)
        passed_match = re.search(r"Passed:\s+(\d+)", clean_output)
        failed_match = re.search(r"Failed:\s+(\d+)", clean_output)
        skipped_match = re.search(r"Skipped:\s+(\d+)", clean_output)

        total = int(total_match.group(1)) if total_match else 0
        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0

        return (total, passed, failed, skipped)

    def run_all_tests(self, test_filter: str = None) -> int:
        """Run all test files and aggregate results"""
        test_files = self.test_files

        # Filter tests if specified
        if test_filter:
            test_files = [f for f in test_files if test_filter in f.name]
            if not test_files:
                print(f"{RED}No tests found matching filter: {test_filter}{NC}")
                return 1

        print(f"{CYAN}{'='*60}{NC}")
        print(f"{CYAN}n8n-deploy Manual Test Suite{NC}")
        print(f"{CYAN}Found {len(test_files)} test files{NC}")
        print(f"{CYAN}{'='*60}{NC}\n")

        results = []

        if self.parallel and not self.stream:
            # Run tests in parallel (not compatible with streaming)
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {executor.submit(self.run_test_file, tf): tf for tf in test_files}
                for future in as_completed(futures):
                    results.append(future.result())
        else:
            # Run tests sequentially
            for test_file in test_files:
                result = self.run_test_file(test_file)
                results.append(result)

                # In streaming mode, check for failures immediately
                if self.stream:
                    if result[1] == 0:
                        print(f"{GREEN}✓{NC} {result[0]} completed\n")
                    else:
                        print(f"{RED}✗{NC} {result[0]} FAILED with exit code {result[1]}\n")
                        # Fail fast in streaming mode
                        return 1

        # Aggregate results
        total_all = passed_all = failed_all = skipped_all = 0
        failed_files = []

        for name, returncode, stdout, stderr in results:
            # Skip detailed output in stream mode (already shown)
            if self.stream:
                if returncode != 0:
                    failed_files.append(name)
                    print(f"{RED}✗{NC} {name}: FAILED (exit code {returncode})")
                continue

            if self.verbose:
                print(f"\n{CYAN}=== Output from {name} ==={NC}")
                print(stdout)
                if stderr:
                    print(f"{YELLOW}Stderr:{NC}\n{stderr}")

            if returncode == 0:
                total, passed, failed, skipped = self.parse_test_results(stdout)
                total_all += total
                passed_all += passed
                failed_all += failed
                skipped_all += skipped

                print(f"{GREEN}✓{NC} {name}: {passed}/{total} passed")
            else:
                failed_files.append(name)
                print(f"{RED}✗{NC} {name}: FAILED (exit code {returncode})")
                if not self.verbose and stderr:
                    print(f"  {stderr[:200]}")

        # Print summary (only in non-stream mode, stream mode shows live results)
        if not self.stream:
            print(f"\n{CYAN}{'='*60}{NC}")
            print(f"{CYAN}TEST SUMMARY{NC}")
            print(f"{CYAN}{'='*60}{NC}")
            print(f"Total Tests:   {total_all}")
            print(f"{GREEN}Passed:        {passed_all}{NC}")
            print(f"{RED}Failed:        {failed_all}{NC}")
            print(f"{YELLOW}Skipped:       {skipped_all}{NC}")

            if failed_files:
                print(f"\n{RED}Failed test files:{NC}")
                for name in failed_files:
                    print(f"  - {name}")

            success_rate = (passed_all / total_all * 100) if total_all > 0 else 0
            print(f"\nSuccess Rate:  {success_rate:.1f}%")
            print(f"{CYAN}{'='*60}{NC}\n")

        return 0 if not failed_files else 1


def main():
    parser = argparse.ArgumentParser(description="Run n8n-deploy manual test suite")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-p", "--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("-s", "--stream", action="store_true", help="Stream output in real-time")
    parser.add_argument("-f", "--filter", type=str, help="Filter tests by name")
    parser.add_argument("--list", action="store_true", help="List available test files")

    args = parser.parse_args()

    runner = TestRunner(verbose=args.verbose, parallel=args.parallel, stream=args.stream)

    if args.list:
        print("Available test files:")
        for test_file in runner.test_files:
            print(f"  - {test_file.name}")
        return 0

    return runner.run_all_tests(test_filter=args.filter)


if __name__ == "__main__":
    sys.exit(main())
