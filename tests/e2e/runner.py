#!/usr/bin/env python3
"""
Master E2E Test Suite Runner for Web App Nhà hàng Mộc.
Supports running individual tiers (1, 2, 3, 4) or all tiers,
verbose output, and JSON test report generation.

Usage:
    python tests/e2e/runner.py
    python tests/e2e/runner.py --tier 1
    python tests/e2e/runner.py --tier 2
    python tests/e2e/runner.py --tier 3
    python tests/e2e/runner.py --tier 4
    python tests/e2e/runner.py --verbose --json-report e2e_report.json
"""

import argparse
import json
import os
import sys
import time
import unittest
from pathlib import Path


# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


TIER_MODULES = {
    1: [
        "tests.e2e.tier1.test_t1_backend",
        "tests.e2e.tier1.test_t1_vnpay",
        "tests.e2e.tier1.test_t1_concurrency",
        "tests.e2e.tier1.test_t1_realtime",
        "tests.e2e.tier1.test_t1_recommendation_gis",
        "tests.e2e.tier1.test_t1_frontend",
    ],
    2: [
        "tests.e2e.tier2.test_t2_vnpay",
        "tests.e2e.tier2.test_t2_refund",
        "tests.e2e.tier2.test_t2_concurrency",
        "tests.e2e.tier2.test_t2_fsm",
    ],
    3: [
        "tests.e2e.tier3.test_t3_combinations",
    ],
    4: [
        "tests.e2e.tier4.test_t4_scenarios",
    ],
}


class DetailedTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.test_records.append({
            "test": str(test),
            "status": "PASSED",
            "error": None,
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.test_records.append({
            "test": str(test),
            "status": "FAILED",
            "error": self._exc_info_to_string(err, test),
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.test_records.append({
            "test": str(test),
            "status": "ERROR",
            "error": self._exc_info_to_string(err, test),
        })

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.test_records.append({
            "test": str(test),
            "status": "SKIPPED",
            "error": reason,
        })


def run_e2e_tests(tier=None, verbosity=1, json_report_path=None):
    start_time = time.time()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    tiers_to_run = [tier] if tier in (1, 2, 3, 4) else [1, 2, 3, 4]

    print("=" * 70)
    print(" WEB APP NHÀ HÀNG MỘC — AUTOMATED E2E TEST RUNNER")
    print(f" Target Tiers: {tiers_to_run}")
    print("=" * 70)

    total_modules = 0
    for t in tiers_to_run:
        for mod_name in TIER_MODULES[t]:
            total_modules += 1
            try:
                mod_suite = loader.loadTestsFromName(mod_name)
                suite.addTest(mod_suite)
            except Exception as e:
                print(f"[-] Error loading module {mod_name}: {e}")

    runner = unittest.TextTestRunner(
        resultclass=DetailedTestResult,
        verbosity=verbosity,
    )
    result = runner.run(suite)
    duration = time.time() - start_time

    total_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = total_run - failures - errors - skipped

    print("\n" + "=" * 70)
    print(" TEST EXECUTION SUMMARY")
    print("=" * 70)
    print(f" Total Tests Run : {total_run}")
    print(f" Passed          : {passed}")
    print(f" Failed          : {failures}")
    print(f" Errors          : {errors}")
    print(f" Skipped         : {skipped}")
    print(f" Time Taken      : {duration:.2f} seconds")
    print(f" Pass Rate       : {(passed / total_run * 100.0 if total_run > 0 else 0):.1f}%")
    print("=" * 70)

    if json_report_path:
        report_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_seconds": round(duration, 3),
            "tiers_run": tiers_to_run,
            "total_tests": total_run,
            "passed": passed,
            "failed": failures,
            "errors": errors,
            "skipped": skipped,
            "pass_rate_percent": round(passed / total_run * 100.0, 1) if total_run > 0 else 0,
            "details": getattr(result, "test_records", []),
        }
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"[+] JSON report saved to: {json_report_path}")

    return 0 if (failures == 0 and errors == 0) else 1


def main():
    parser = argparse.ArgumentParser(description="Run Nhà hàng Mộc E2E Tests.")
    parser.add_argument(
        "--tier", "-t",
        type=int,
        choices=[1, 2, 3, 4],
        help="Run tests only for the specified Tier (1, 2, 3, or 4). Default: run all.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    parser.add_argument(
        "--json-report", "-j",
        type=str,
        default=None,
        help="Path to output JSON test execution report.",
    )

    args = parser.parse_args()
    verbosity = 2 if args.verbose else 1
    sys.exit(run_e2e_tests(tier=args.tier, verbosity=verbosity, json_report_path=args.json_report))


if __name__ == "__main__":
    main()
