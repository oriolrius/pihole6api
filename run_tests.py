#!/usr/bin/env python3
"""
Test runner script for pihole6api library.

This script provides an easy way to run tests with different configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run pihole6api tests")
    parser.add_argument(
        '--coverage', 
        action='store_true', 
        help='Run tests with coverage report'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests in verbose mode'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run only fast tests (exclude slow markers)'
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run only integration tests'
    )
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run only unit tests'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Run tests from specific file'
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    import os
    os.chdir(project_root)
    
    # Build base command
    cmd = ['python', '-m', 'pytest']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    
    # Add coverage
    if args.coverage:
        cmd.extend(['--cov=src/pihole6api', '--cov-report=html', '--cov-report=term'])
    
    # Add marker filters
    if args.fast:
        cmd.extend(['-m', 'not slow'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.unit:
        cmd.extend(['-m', 'unit'])
    
    # Add specific file
    if args.file:
        cmd.append(f'tests/{args.file}')
    else:
        cmd.append('tests/')
    
    # Run tests
    exit_code = run_command(cmd, "Running tests")
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())