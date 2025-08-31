"""
Integration Test Runner for Cacherr API Endpoints

This script provides comprehensive testing capabilities for all API integration tests,
including selective test execution, coverage reporting, and performance monitoring.

Usage:
    python tests/integration/run_integration_tests.py [options]

Options:
    --all                 Run all integration tests
    --health             Run only health API tests
    --config             Run only configuration API tests
    --scheduler          Run only scheduler API tests
    --watcher            Run only watcher API tests
    --results            Run only results API tests
    --cached             Run only cached files API tests
    --logs               Run only logs API tests
    --trakt              Run only Trakt API tests
    --coverage           Generate coverage report
    --verbose            Enable verbose output
    --fail-fast          Stop on first failure
    --performance        Run performance tests
    --slow               Include slow tests
"""

import subprocess
import sys
import argparse
import time
from pathlib import Path
from typing import List, Optional


class IntegrationTestRunner:
    """Runner for Cacherr API integration tests."""

    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent.parent

        # Test categories and their corresponding test files
        self.test_categories = {
            "health": ["test_health_api.py"],
            "config": ["test_config_api.py"],
            "scheduler": ["test_scheduler_api.py"],
            "watcher": ["test_watcher_api.py"],
            "results": ["test_results_api.py"],
            "cached": ["test_cached_api.py"],
            "logs": ["test_logs_api.py"],
            "trakt": ["test_trakt_api.py"]
        }

    def run_tests(self, categories: List[str] = None, coverage: bool = False,
                  verbose: bool = False, fail_fast: bool = False,
                  performance: bool = False, include_slow: bool = False) -> int:
        """
        Run integration tests for specified categories.

        Args:
            categories: List of test categories to run
            coverage: Generate coverage report
            verbose: Enable verbose output
            fail_fast: Stop on first failure
            performance: Run performance tests
            include_slow: Include slow tests

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if categories is None:
            categories = list(self.test_categories.keys())

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]

        # Add test files
        test_files = []
        for category in categories:
            if category in self.test_categories:
                test_files.extend(self.test_categories[category])

        if not test_files:
            print(f"❌ No test files found for categories: {categories}")
            return 1

        # Add test file paths
        for test_file in test_files:
            cmd.append(str(self.test_dir / test_file))

        # Add pytest options
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:tests/reports/coverage",
                "--cov-report=term-missing",
                "--cov-fail-under=80"
            ])

        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        if fail_fast:
            cmd.append("--tb=short")

        # Add markers
        markers = []
        if performance:
            markers.append("performance")
        if include_slow:
            markers.append("slow")
        else:
            markers.append("not slow")

        if markers:
            cmd.extend(["-m", " and ".join(markers)])

        # Add integration marker
        cmd.extend(["-m", "api"])

        print(f"🚀 Running integration tests for categories: {categories}")
        print(f"📁 Test files: {test_files}")
        print(f"🔧 Command: {' '.join(cmd)}")
        print("-" * 60)

        # Run tests
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root)
        end_time = time.time()

        # Report results
        duration = end_time - start_time
        if result.returncode == 0:
            print(".2f"        else:
            print(".2f"
        return result.returncode

    def list_available_tests(self):
        """List all available integration tests."""
        print("📋 Available Integration Test Categories:")
        print("-" * 40)

        for category, files in self.test_categories.items():
            print("15"            for test_file in files:
                print(f"    📄 {test_file}")

        print("\n📊 Test Statistics:")
        total_files = sum(len(files) for files in self.test_categories.values())
        print(f"   Total test files: {total_files}")
        print(f"   Total categories: {len(self.test_categories)}")

    def validate_test_environment(self) -> bool:
        """Validate that the test environment is properly set up."""
        print("🔍 Validating test environment...")

        # Check if test files exist
        missing_files = []
        for category, files in self.test_categories.items():
            for test_file in files:
                test_path = self.test_dir / test_file
                if not test_path.exists():
                    missing_files.append(str(test_path))

        if missing_files:
            print("❌ Missing test files:"            for missing_file in missing_files:
                print(f"   ❌ {missing_file}")
            return False

        # Check if required dependencies are available
        try:
            import pytest
            import fastapi
            import requests
            print("✅ Required dependencies are available")
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            return False

        # Check if conftest.py exists
        conftest_path = self.test_dir / "conftest.py"
        if not conftest_path.exists():
            print("❌ conftest.py not found in integration directory")
            return False

        print("✅ Test environment validation passed")
        return True


def main():
    """Main entry point for the integration test runner."""
    parser = argparse.ArgumentParser(
        description="Cacherr API Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Test category arguments
    parser.add_argument("--all", action="store_true",
                       help="Run all integration tests")
    parser.add_argument("--health", action="store_true",
                       help="Run health API tests")
    parser.add_argument("--config", action="store_true",
                       help="Run configuration API tests")
    parser.add_argument("--scheduler", action="store_true",
                       help="Run scheduler API tests")
    parser.add_argument("--watcher", action="store_true",
                       help="Run watcher API tests")
    parser.add_argument("--results", action="store_true",
                       help="Run results API tests")
    parser.add_argument("--cached", action="store_true",
                       help="Run cached files API tests")
    parser.add_argument("--logs", action="store_true",
                       help="Run logs API tests")
    parser.add_argument("--trakt", action="store_true",
                       help="Run Trakt API tests")

    # Test options
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--fail-fast", action="store_true",
                       help="Stop on first failure")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests")
    parser.add_argument("--slow", action="store_true",
                       help="Include slow tests")

    # Utility options
    parser.add_argument("--list", action="store_true",
                       help="List available tests")
    parser.add_argument("--validate", action="store_true",
                       help="Validate test environment")

    args = parser.parse_args()

    runner = IntegrationTestRunner()

    # Handle utility commands
    if args.list:
        runner.list_available_tests()
        return 0

    if args.validate:
        success = runner.validate_test_environment()
        return 0 if success else 1

    # Determine which categories to run
    if args.all:
        categories = None  # Run all
    else:
        categories = []
        for category in runner.test_categories.keys():
            if getattr(args, category):
                categories.append(category)

        if not categories:
            print("❌ No test categories specified. Use --all or specific category flags.")
            print("💡 Available categories:", list(runner.test_categories.keys()))
            return 1

    # Validate environment before running tests
    if not runner.validate_test_environment():
        return 1

    # Run tests
    return runner.run_tests(
        categories=categories,
        coverage=args.coverage,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        performance=args.performance,
        include_slow=args.slow
    )


if __name__ == "__main__":
    sys.exit(main())
