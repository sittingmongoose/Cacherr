#!/usr/bin/env python3
"""
Coverage validation and reporting script for Cacherr testing suite.

This script validates test coverage against requirements, generates comprehensive
reports, and ensures the testing suite meets quality standards.

Usage:
    python tests/validate_coverage.py [options]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import xml.etree.ElementTree as ET


class CoverageValidator:
    """Validates and reports on test coverage for the Cacherr project."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_dir = project_root / "htmlcov"
        self.coverage_xml = project_root / "coverage.xml"
        self.tests_dir = project_root / "tests"

    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run coverage analysis and return results."""
        print("🔍 Running coverage analysis...")

        # Run pytest with coverage
        cmd = [
            "python", "-m", "pytest",
            "--cov=src",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "-v"
        ]

        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    def parse_coverage_xml(self) -> Dict[str, Any]:
        """Parse coverage XML report and extract metrics."""
        if not self.coverage_xml.exists():
            return {"error": "Coverage XML file not found"}

        try:
            tree = ET.parse(self.coverage_xml)
            root = tree.getroot()

            coverage_data = {
                "overall_coverage": float(root.get("line-rate", 0)) * 100,
                "overall_branch_coverage": float(root.get("branch-rate", 0)) * 100,
                "lines_covered": int(root.get("lines-covered", 0)),
                "lines_total": int(root.get("lines-valid", 0)),
                "files": []
            }

            # Parse individual file coverage
            for package in root.findall(".//package"):
                for file_elem in package.findall(".//class"):
                    file_data = {
                        "filename": file_elem.get("filename", ""),
                        "name": file_elem.get("name", ""),
                        "line_rate": float(file_elem.get("line-rate", 0)) * 100,
                        "branch_rate": float(file_elem.get("branch-rate", 0)) * 100,
                        "lines_covered": int(file_elem.get("lines-covered", 0)),
                        "lines_total": int(file_elem.get("lines-valid", 0))
                    }
                    coverage_data["files"].append(file_data)

            return coverage_data

        except Exception as e:
            return {"error": f"Failed to parse coverage XML: {e}"}

    def analyze_test_structure(self) -> Dict[str, Any]:
        """Analyze the test file structure and organization."""
        analysis = {
            "total_test_files": 0,
            "test_files_by_type": {},
            "missing_tests": [],
            "test_coverage": {}
        }

        # Count test files by type
        test_files = list(self.tests_dir.rglob("test_*.py"))
        test_files.extend(self.tests_dir.rglob("*_test.py"))

        analysis["total_test_files"] = len(test_files)

        for test_file in test_files:
            relative_path = test_file.relative_to(self.tests_dir)
            if relative_path.parts:
                test_type = relative_path.parts[0]
                analysis["test_files_by_type"][test_type] = \
                    analysis["test_files_by_type"].get(test_type, 0) + 1

        # Check for source files without corresponding tests
        src_files = list((self.project_root / "src").rglob("*.py"))
        for src_file in src_files:
            if src_file.name == "__init__.py":
                continue

            relative_path = src_file.relative_to(self.project_root / "src")
            test_file_candidates = [
                self.tests_dir / f"test_{src_file.stem}.py",
                self.tests_dir / relative_path.parent / f"test_{src_file.stem}.py",
                self.tests_dir / relative_path.parent / f"{src_file.stem}_test.py"
            ]

            has_test = any(candidate.exists() for candidate in test_file_candidates)
            if not has_test:
                analysis["missing_tests"].append(str(relative_path))

        return analysis

    def validate_coverage_requirements(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate coverage against requirements."""
        validation = {
            "passed": True,
            "issues": [],
            "recommendations": []
        }

        overall_coverage = coverage_data.get("overall_coverage", 0)

        # Check overall coverage requirement (>=90%)
        if overall_coverage < 90:
            validation["passed"] = False
            validation["issues"].append(
                f"Overall coverage {overall_coverage:.1f}% is below 90% requirement"
            )

        # Check branch coverage (>=80%)
        branch_coverage = coverage_data.get("overall_branch_coverage", 0)
        if branch_coverage < 80:
            validation["issues"].append(
                f"Branch coverage {branch_coverage:.1f}% is below 80% recommendation"
            )

        # Check for files with low coverage
        low_coverage_files = []
        for file_data in coverage_data.get("files", []):
            if file_data["line_rate"] < 80:
                low_coverage_files.append(
                    f"{file_data['filename']}: {file_data['line_rate']:.1f}%"
                )

        if low_coverage_files:
            validation["issues"].extend([
                "Files with low coverage (<80%):",
                *low_coverage_files[:10]  # Show first 10
            ])
            if len(low_coverage_files) > 10:
                validation["issues"].append(
                    f"... and {len(low_coverage_files) - 10} more"
                )

        # Generate recommendations
        if overall_coverage < 95:
            validation["recommendations"].append(
                "Consider adding more integration tests to reach 95%+ coverage"
            )

        if not low_coverage_files:
            validation["recommendations"].append(
                "Excellent! All files meet minimum coverage requirements"
            )

        return validation

    def generate_report(self, coverage_data: Dict[str, Any],
                       test_analysis: Dict[str, Any],
                       validation: Dict[str, Any]) -> str:
        """Generate a comprehensive coverage report."""
        report_lines = [
            "=" * 60,
            "🧪 CACHERR TEST COVERAGE REPORT",
            "=" * 60,
            "",
            f"📊 OVERALL COVERAGE: {coverage_data.get('overall_coverage', 0):.1f}%",
            f"🌿 BRANCH COVERAGE: {coverage_data.get('overall_branch_coverage', 0):.1f}%",
            f"📁 FILES COVERED: {len(coverage_data.get('files', []))}",
            f"📝 LINES COVERED: {coverage_data.get('lines_covered', 0)}/{coverage_data.get('lines_total', 0)}",
            "",
            "📂 TEST FILE ANALYSIS:",
            f"   Total test files: {test_analysis.get('total_test_files', 0)}",
        ]

        # Add test file breakdown
        for test_type, count in test_analysis.get("test_files_by_type", {}).items():
            report_lines.append(f"   {test_type}: {count} files")

        report_lines.extend([
            "",
            "✅ VALIDATION RESULTS:"
        ])

        if validation["passed"]:
            report_lines.append("   ✅ All coverage requirements met!")
        else:
            report_lines.append("   ❌ Some requirements not met")

        # Add issues
        if validation["issues"]:
            report_lines.extend([
                "",
                "⚠️  ISSUES FOUND:",
                *[f"   - {issue}" for issue in validation["issues"]]
            ])

        # Add recommendations
        if validation["recommendations"]:
            report_lines.extend([
                "",
                "💡 RECOMMENDATIONS:",
                *[f"   - {rec}" for rec in validation["recommendations"]]
            ])

        # Add missing tests
        missing_tests = test_analysis.get("missing_tests", [])
        if missing_tests:
            report_lines.extend([
                "",
                "🔍 MISSING TESTS:",
                *[f"   - {test}" for test in missing_tests[:10]]
            ])
            if len(missing_tests) > 10:
                report_lines.append(f"   ... and {len(missing_tests) - 10} more")

        report_lines.extend([
            "",
            "📈 TOP FILES BY COVERAGE:",
        ])

        # Sort files by coverage and show top 10
        files = coverage_data.get("files", [])
        sorted_files = sorted(
            files,
            key=lambda x: x["line_rate"],
            reverse=True
        )

        for i, file_data in enumerate(sorted_files[:10]):
            report_lines.append(
                f"   {i+1:2d}. {file_data['name']:<30} "
                f"{file_data['line_rate']:5.1f}% ({file_data['lines_covered']}/{file_data['lines_total']})"
            )

        report_lines.extend([
            "",
            "=" * 60,
            f"Report generated for: {self.project_root.name}",
            "=" * 60
        ])

        return "\n".join(report_lines)

    def save_report(self, report: str, output_file: Path) -> None:
        """Save the report to a file."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Report saved to: {output_file}")

    def run_full_validation(self, save_report: bool = True) -> Dict[str, Any]:
        """Run complete coverage validation and generate report."""
        print("🚀 Starting comprehensive coverage validation...")

        # Run coverage analysis
        coverage_result = self.run_coverage_analysis()
        if coverage_result["returncode"] != 0:
            print("❌ Coverage analysis failed!")
            print(coverage_result["stderr"])
            return {"error": "Coverage analysis failed"}

        # Parse coverage data
        coverage_data = self.parse_coverage_xml()
        if "error" in coverage_data:
            print(f"❌ Failed to parse coverage data: {coverage_data['error']}")
            return coverage_data

        # Analyze test structure
        test_analysis = self.analyze_test_structure()

        # Validate requirements
        validation = self.validate_coverage_requirements(coverage_data)

        # Generate report
        report = self.generate_report(coverage_data, test_analysis, validation)

        # Print report
        print(report)

        # Save report if requested
        if save_report:
            report_file = self.project_root / "tests" / "coverage_report.txt"
            self.save_report(report, report_file)

        # Return comprehensive results
        return {
            "coverage_data": coverage_data,
            "test_analysis": test_analysis,
            "validation": validation,
            "report": report,
            "success": validation["passed"]
        }


def main():
    """Main entry point for coverage validation."""
    parser = argparse.ArgumentParser(
        description="Cacherr Coverage Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/validate_coverage.py              # Run full validation
  python tests/validate_coverage.py --no-report  # Skip report saving
  python tests/validate_coverage.py --quiet      # Minimal output
        """
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Don't save report to file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: auto-detect)"
    )

    args = parser.parse_args()

    # Determine project root
    if args.project_root:
        project_root = args.project_root
    else:
        # Auto-detect: script is in tests/ subdirectory
        project_root = Path(__file__).parent.parent

    if not args.quiet:
        print(f"📍 Project root: {project_root}")

    # Initialize validator
    validator = CoverageValidator(project_root)

    # Run validation
    results = validator.run_full_validation(save_report=not args.no_report)

    # Exit with appropriate code
    if "error" in results:
        if not args.quiet:
            print(f"❌ Validation failed: {results['error']}")
        sys.exit(1)
    elif not results.get("success", False):
        if not args.quiet:
            print("❌ Coverage requirements not met")
        sys.exit(1)
    else:
        if not args.quiet:
            print("✅ Coverage validation passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
