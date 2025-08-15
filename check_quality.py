#!/usr/bin/env python3
"""
Code quality checker script.

Runs all quality checks and provides a comprehensive report.
Used in CI/CD pipelines and pre-commit hooks.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, NamedTuple


class CheckResult(NamedTuple):
    name: str
    command: str
    success: bool
    output: str


def run_command(name: str, command: str) -> CheckResult:
    """Run a command and capture its result."""
    print(f"🔍 Running {name}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        if success:
            print(f"✅ {name} passed")
        else:
            print(f"❌ {name} failed")
            
        return CheckResult(name, command, success, output)
        
    except Exception as e:
        print(f"💥 {name} crashed: {e}")
        return CheckResult(name, command, False, str(e))


def main():
    """Run all quality checks."""
    print("🚀 Spark Simplicity - Quality Checker")
    print("=" * 50)
    
    checks = [
        ("Code Formatting (Black)", "black --check spark_simplicity/ tests/"),
        ("Import Sorting (isort)", "isort --check-only spark_simplicity/ tests/"),
        ("Linting (Flake8)", "flake8 spark_simplicity/ tests/"),
        ("Type Checking (MyPy)", "mypy spark_simplicity/"),
        ("Security Check (Bandit)", "bandit -r spark_simplicity/ -f json -o bandit_report.json || true"),
        ("Unit Tests", "pytest tests/ -m 'not integration and not performance' --tb=short"),
        ("Test Coverage", "pytest tests/ --cov=spark_simplicity --cov-fail-under=90 --tb=short"),
    ]
    
    results: List[CheckResult] = []
    
    for name, command in checks:
        result = run_command(name, command)
        results.append(result)
        print()
    
    # Summary
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results if r.success)
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} {result.name}")
        
        if not result.success and result.output.strip():
            # Show first few lines of error output
            lines = result.output.strip().split('\n')[:5]
            for line in lines:
                print(f"    {line}")
            if len(result.output.split('\n')) > 5:
                print("    ...")
    
    print()
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All quality checks passed!")
        sys.exit(0)
    else:
        print(f"💔 {total - passed} check(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()