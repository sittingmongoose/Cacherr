#!/usr/bin/env python3
"""
Comprehensive test runner for Cacherr backend testing suite.

This script provides multiple testing modes and configurations for running
the complete test suite with different levels of coverage and reporting.

Usage:
    python tests/run_tests.py [options]

Examples:
    python tests/run_tests.py --unit           # Run only unit tests
    python tests/run_tests.py --integration   # Run integration tests
    python tests/run_tests.py --coverage      # Run with coverage
    python tests/run_tests.py --performance   # Run performance tests
    python tests/run_tests.py --all           # Run all tests
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for Cacherr backend tests."""

    def __init__(self, base_dir: Path):
        """Initialize test runner with base directory."""
        self.base_dir = base_dir
        self.tests_dir = base_dir / "tests"
        self.src_dir = base_dir / "src"

    def run_command(self, command: List[str], cwd: Optional[Path] = None) -> int:
        """Run a command and return the exit code."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.tests_dir,
                capture_output=False,
                text=True,
                check=False
            )
            return result.returncode
        except KeyboardInterrupt:
            print("\nTest run interrupted by user")
            return 130
        except Exception as e:
            print(f"Error running command: {e}")
            return 1

    def run_unit_tests(self, verbose: bool = True, parallel: bool = False) -> int:
        """Run unit tests only."""
        print("🚀 Running unit tests...")
        cmd = ["pytest", "-m", "unit"]

        if verbose:
            cmd.append("-v")
        if parallel:
            cmd.extend(["-n", "auto"])

        return self.run_command(cmd)

    def run_integration_tests(self, verbose: bool = True) -> int:
        """Run integration tests only."""
        print("🔗 Running integration tests...")
        cmd = ["pytest", "-m", "integration"]

        if verbose:
            cmd.append("-v")

        return self.run_command(cmd)

    def run_api_tests(self, verbose: bool = True) -> int:
        """Run API tests only."""
        print("🌐 Running API tests...")
        cmd = ["pytest", "-m", "api"]

        if verbose:
            cmd.append("-v")

        return self.run_command(cmd)

    def run_websocket_tests(self, verbose: bool = True) -> int:
        """Run WebSocket tests only."""
        print("🔌 Running WebSocket tests...")
        cmd = ["pytest", "-m", "websocket"]

        if verbose:
            cmd.append("-v")

        return self.run_command(cmd)

    def run_repository_tests(self, verbose: bool = True) -> int:
        """Run repository layer tests only."""
        print("💾 Running repository tests...")
        cmd = ["pytest", "-m", "repository"]

        if verbose:
            cmd.append("-v")

        return self.run_command(cmd)

    def run_service_tests(self, verbose: bool = True, parallel: bool = False) -> int:
        """Run service layer tests only."""
        print("⚙️ Running service tests...")
        cmd = ["pytest", "-m", "service"]

        if verbose:
            cmd.append("-v")
        if parallel:
            cmd.extend(["-n", "auto"])

        return self.run_command(cmd)

    def run_performance_tests(self, verbose: bool = True) -> int:
        """Run performance tests only."""
        print("⚡ Running performance tests...")
        cmd = ["pytest", "-m", "performance"]

        if verbose:
            cmd.append("-v")

        return self.run_command(cmd)

    def run_security_tests(self, verbose: bool = True) -> int:
        """Run security tests only."""
        print("🔒 Running security tests...")
        cmd = ["pytest", "-m", "security"]

        if verbose:
            cmd.append("-v")

        return self.run_command(cmd)

    def run_with_coverage(self, markers: Optional[str] = None, html: bool = True) -> int:
        """Run tests with coverage reporting."""
        print("📊 Running tests with coverage...")

        cmd = [
            "pytest",
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml"
        ]

        if html:
            cmd.append("--cov-report=html:htmlcov")
        if markers:
            cmd.extend(["-m", markers])

        return self.run_command(cmd)

    def run_all_tests(self, parallel: bool = False, coverage: bool = True) -> int:
        """Run all tests with comprehensive reporting."""
        print("🎯 Running complete test suite...")

        cmd = ["pytest"]

        if parallel:
            cmd.extend(["-n", "auto"])
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml:coverage.xml"
            ])

        # Add test duration reporting
        cmd.extend(["--durations=10", "--durations-min=0.5"])

        return self.run_command(cmd)

    def run_slow_tests_only(self) -> int:
        """Run only slow tests (marked with @pytest.mark.slow)."""
        print("🐌 Running slow tests only...")
        cmd = ["pytest", "-m", "slow", "-v", "--durations=0"]
        return self.run_command(cmd)

    def run_fast_tests_only(self, parallel: bool = True) -> int:
        """Run only fast tests (unit tests, excluding slow/integration)."""
        print("💨 Running fast tests only...")
        cmd = ["pytest", "-m", "unit and not slow", "-v"]

        if parallel:
            cmd.extend(["-n", "auto"])

        return self.run_command(cmd)

    def check_test_structure(self) -> int:
        """Check test file structure and naming conventions."""
        print("🔍 Checking test structure...")

        test_files = list(self.tests_dir.rglob("test_*.py"))
        test_files.extend(self.tests_dir.rglob("*_test.py"))

        issues = []

        for test_file in test_files:
            # Check if file has corresponding source file
            relative_path = test_file.relative_to(self.tests_dir)
            source_file = self.src_dir / relative_path

            # Remove test_ prefix and _test suffix to find source
            if relative_path.name.startswith("test_"):
                source_name = relative_path.name[5:]  # Remove "test_"
            elif relative_path.name.endswith("_test.py"):
                source_name = relative_path.name[:-8] + ".py"  # Remove "_test.py"
            else:
                continue

            source_path = self.src_dir / relative_path.parent / source_name

            if not source_path.exists():
                issues.append(f"No corresponding source file for {test_file}")

        if issues:
            print("❌ Test structure issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        else:
            print("✅ Test structure looks good!")
            return 0

    def generate_test_report(self) -> int:
        """Generate comprehensive test report."""
        print("📋 Generating test report...")

        cmd = [
            "pytest",
            "--html=reports/test_report.html",
            "--json-report",
            "--json-report-file=reports/test_report.json",
            "--junitxml=reports/test_report.xml"
        ]

        return self.run_command(cmd)


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Cacherr Backend Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_tests.py --unit              # Run unit tests
  python tests/run_tests.py --integration      # Run integration tests
  python tests/run_tests.py --coverage         # Run with coverage
  python tests/run_tests.py --all              # Run all tests
  python tests/run_tests.py --performance      # Run performance tests
  python tests/run_tests.py --fast             # Run fast tests only
  python tests/run_tests.py --check-structure  # Check test structure
        """
    )

    # Test type options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--websocket", action="store_true", help="Run WebSocket tests only")
    parser.add_argument("--repository", action="store_true", help="Run repository tests only")
    parser.add_argument("--service", action="store_true", help="Run service tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")

    # Test suite options
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--fast", action="store_true", help="Run only fast tests")
    parser.add_argument("--slow", action="store_true", help="Run only slow tests")

    # Configuration options
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel execution")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    # Utility options
    parser.add_argument("--check-structure", action="store_true", help="Check test file structure")
    parser.add_argument("--generate-report", action="store_true", help="Generate test report")

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(__file__).parent.parent

    # Initialize test runner
    runner = TestRunner(base_dir)

    # Handle utility commands
    if args.check_structure:
        return runner.check_test_structure()

    if args.generate_report:
        return runner.generate_test_report()

    # Determine test configuration
    coverage = args.coverage and not args.no_coverage
    parallel = args.parallel and not args.no_parallel
    verbose = not args.quiet

    # Run specific test types
    if args.unit:
        return runner.run_unit_tests(verbose, parallel)
    elif args.integration:
        return runner.run_integration_tests(verbose)
    elif args.api:
        return runner.run_api_tests(verbose)
    elif args.websocket:
        return runner.run_websocket_tests(verbose)
    elif args.repository:
        return runner.run_repository_tests(verbose)
    elif args.service:
        return runner.run_service_tests(verbose, parallel)
    elif args.performance:
        return runner.run_performance_tests(verbose)
    elif args.security:
        return runner.run_security_tests(verbose)
    elif args.slow:
        return runner.run_slow_tests_only()
    elif args.fast:
        return runner.run_fast_tests_only(parallel)
    elif args.all:
        return runner.run_all_tests(parallel, coverage)
    elif coverage:
        return runner.run_with_coverage()
    else:
        # Default: run all tests
        return runner.run_all_tests(parallel, coverage)


if __name__ == "__main__":
    sys.exit(main())
