#!/usr/bin/env python3
"""
Comprehensive test runner for pihole6api library.

This script runs both unit tests (mocked) and integration tests (Docker-based).
It automatically manages Docker container lifecycle for integration tests.
"""

import sys
import subprocess
import argparse
import os
import time
from pathlib import Path

# Add the tests directory to Python path
tests_dir = Path(__file__).parent / "tests"
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(tests_dir))

from tests.docker_test_manager import PiHoleDockerTestManager


def run_command(cmd, description, cwd=None):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests (mocked tests)."""
    cmd = ['python', '-m', 'pytest']
    
    # Test files for unit tests (exclude integration tests)
    cmd.extend([
        'tests/test_authentication.py',
        'tests/test_local_dns.py',
        'tests/test_integration.py',  # This has mocked integration tests
    ])
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=src/pihole6api', '--cov-report=term-missing'])
    
    # Set PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root / "src")
    
    print(f"\n{'='*60}")
    print("Running Unit Tests (Mocked)")
    print('='*60)
    
    result = subprocess.run(cmd, cwd=project_root, env=env)
    return result.returncode


def run_integration_tests(verbose=False):
    """Run integration tests with Docker container."""
    docker_manager = PiHoleDockerTestManager()
    
    try:
        # Start Docker container
        print(f"\n{'='*60}")
        print("Setting up Docker Pi-hole for Integration Tests")
        print('='*60)
        
        if not docker_manager.start_container():
            print("❌ Failed to start Docker container")
            return 1
        
        # Wait a bit for Pi-hole to fully initialize
        print("Waiting for Pi-hole to fully initialize...")
        time.sleep(10)
        
        # Run integration tests
        cmd = ['python', '-m', 'pytest', 'tests/test_real_integration.py']
        
        if verbose:
            cmd.append('-v')
        
        # Set PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root / "src")
        
        print(f"\n{'='*60}")
        print("Running Integration Tests (Real Pi-hole)")
        print('='*60)
        
        result = subprocess.run(cmd, cwd=project_root, env=env)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted")
        return 1
        
    finally:
        # Always cleanup Docker container
        print(f"\n{'='*60}")
        print("Cleaning up Docker container")
        print('='*60)
        docker_manager.stop_container()


def run_all_tests(verbose=False, coverage=False):
    """Run both unit and integration tests."""
    print("🧪 Running Complete Test Suite")
    print("=" * 80)
    
    # Run unit tests first
    unit_result = run_unit_tests(verbose=verbose, coverage=coverage)
    
    if unit_result != 0:
        print("\n❌ Unit tests failed. Skipping integration tests.")
        return unit_result
    
    print("\n✅ Unit tests passed! Running integration tests...")
    
    # Run integration tests
    integration_result = run_integration_tests(verbose=verbose)
    
    if integration_result == 0:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Integration tests failed.")
    
    return integration_result


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
        else:
            print("❌ Docker not available")
            return False
    except FileNotFoundError:
        print("❌ Docker not found")
        return False
    
    # Check Docker Compose
    try:
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose: {result.stdout.strip()}")
        else:
            print("❌ Docker Compose not available")
            return False
    except FileNotFoundError:
        print("❌ Docker Compose not found")
        return False
    
    # Check pytest
    try:
        result = subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Pytest: {result.stdout.strip()}")
        else:
            print("❌ Pytest not available")
            return False
    except FileNotFoundError:
        print("❌ Pytest not found")
        return False
    
    print("✅ All dependencies available")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run pihole6api tests with Docker-based integration testing"
    )
    
    parser.add_argument(
        'test_type',
        choices=['unit', 'integration', 'all'],
        nargs='?',
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests in verbose mode'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run unit tests with coverage report'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies and exit'
    )
    
    parser.add_argument(
        '--docker-only',
        action='store_true',
        help='Only manage Docker container (start/stop)'
    )
    
    parser.add_argument(
        '--docker-action',
        choices=['start', 'stop', 'restart', 'logs'],
        help='Docker container action'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if args.check_deps:
        return 0 if check_dependencies() else 1
    
    # Docker-only actions
    if args.docker_only and args.docker_action:
        docker_manager = PiHoleDockerTestManager()
        
        if args.docker_action == 'start':
            return 0 if docker_manager.start_container() else 1
        elif args.docker_action == 'stop':
            return 0 if docker_manager.stop_container() else 1
        elif args.docker_action == 'restart':
            docker_manager.stop_container()
            return 0 if docker_manager.start_container() else 1
        elif args.docker_action == 'logs':
            print(docker_manager.get_container_logs())
            return 0
    
    # Check dependencies before running tests
    if not check_dependencies():
        print("\n❌ Missing required dependencies")
        return 1
    
    # Run tests
    if args.test_type == 'unit':
        return run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.test_type == 'integration':
        return run_integration_tests(verbose=args.verbose)
    elif args.test_type == 'all':
        return run_all_tests(verbose=args.verbose, coverage=args.coverage)


if __name__ == "__main__":
    sys.exit(main())