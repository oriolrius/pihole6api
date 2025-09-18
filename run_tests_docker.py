#!/usr/bin/env python3
"""
Docker-based Test Runner for pihole6api.

This script provides a comprehensive testing framework for the pihole6api library
using real Pi-hole Docker containers. It handles the complete test lifecycle
including Docker container management, test execution, and cleanup.

Usage:
    python run_tests_docker.py                    # Run all tests
    python run_tests_docker.py -v                 # Verbose output
    python run_tests_docker.py -t test_01_auth    # Run specific test
    python run_tests_docker.py --cleanup-only     # Cleanup and exit
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_command(cmd, capture_output=True, check=True, timeout=None):
    """Run a command with error handling and optional timeout."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, 
                timeout=timeout, check=False
            )
            if check and result.returncode != 0:
                print(f"❌ Command failed: {cmd}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
                if result.stdout:
                    print(f"Output: {result.stdout.strip()}")
                return None
            return result
        else:
            result = subprocess.run(cmd, shell=True, timeout=timeout, check=False)
            return result
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out: {cmd}")
        return None
    except Exception as e:
        print(f"❌ Command error: {cmd} - {e}")
        return None

def check_prerequisites():
    """Check all prerequisites for running Docker-based tests."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check Docker installation
    result = run_command("docker --version", timeout=10)
    if result is None:
        print("❌ Docker is not installed or not accessible")
        print("   Please install Docker: https://docs.docker.com/get-docker/")
        return False
    print(f"✅ {result.stdout.strip()}")
    
    # Check Docker daemon
    result = run_command("docker info", check=False, timeout=10)
    if result is None or result.returncode != 0:
        print("❌ Docker daemon is not running")
        print("   Please start Docker daemon")
        return False
    print("✅ Docker daemon is running")
    
    # Check Docker Compose
    result = run_command("docker compose version", check=False, timeout=10)
    if result is None or result.returncode != 0:
        print("❌ Docker Compose is not available")
        print("   Please install Docker Compose v2")
        return False
    print(f"✅ {result.stdout.strip()}")
    
    # Check network connectivity (needed for Pi-hole Docker image)
    result = run_command("docker pull --help", timeout=5)
    if result is None:
        print("❌ Docker pull command is not working")
        return False
    print("✅ Docker pull capability confirmed")
    
    return True

def setup_test_environment():
    """Setup the test environment and dependencies."""
    print("\n🔧 Setting up test environment...")
    
    # Ensure we're in the correct directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"Working directory: {project_root}")
    
    # Add source directory to Python path instead of installing
    print("📦 Setting up Python path for pihole6api...")
    src_path = project_root / "src"
    if src_path.exists():
        # Add to PYTHONPATH environment variable for the tests
        current_pythonpath = os.environ.get('PYTHONPATH', '')
        if current_pythonpath:
            os.environ['PYTHONPATH'] = f"{src_path}:{current_pythonpath}"
        else:
            os.environ['PYTHONPATH'] = str(src_path)
        print(f"✅ Added {src_path} to PYTHONPATH")
    
    # Install test dependencies
    print("📦 Installing test dependencies...")
    test_deps = ["pytest>=7.0.0", "requests>=2.25.0"]
    
    for dep in test_deps:
        result = run_command(f"pip install --user '{dep}'", timeout=30)
        if result is None:
            print(f"❌ Failed to install {dep}")
            return False
    
    # Verify pytest installation
    result = run_command("pytest --version", timeout=10)
    if result is None:
        print("❌ pytest is not properly installed")
        return False
    print(f"✅ {result.stdout.strip()}")
    
    # Check if test files exist
    test_file = project_root / "tests" / "test_real_integration.py"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    print(f"✅ Test file found: {test_file.name}")
    
    print("✅ Test environment ready")
    return True

def run_docker_tests(test_pattern=None, verbose=False, stop_on_failure=False, parallel=False):
    """Execute the Docker-based test suite."""
    print("\n🚀 Starting Docker-based Pi-hole tests...")
    print("=" * 60)
    
    # Build pytest command
    pytest_args = ["pytest"]
    
    # Output configuration
    if verbose:
        pytest_args.extend(["-v", "-s"])
    else:
        pytest_args.extend(["-s", "--tb=short"])
    
    # Test execution options
    if stop_on_failure:
        pytest_args.append("-x")
    
    if parallel and test_pattern is None:
        pytest_args.extend(["-n", "auto"])  # Requires pytest-xdist
    
    # Specify test file/pattern
    if test_pattern:
        if "::" in test_pattern:
            # Full test specification (class::method)
            pytest_args.append(f"tests/test_real_integration.py::{test_pattern}")
        else:
            # Partial match
            pytest_args.extend(["-k", test_pattern, "tests/test_real_integration.py"])
    else:
        pytest_args.append("tests/test_real_integration.py")
    
    # Additional pytest options
    pytest_args.extend([
        "-ra",                    # Show extra summary for all except passed
        "--durations=10",         # Show 10 slowest tests
        "--strict-markers",       # Fail on unknown markers
    ])
    
    # Build and display command
    cmd = " ".join(pytest_args)
    print(f"Executing: {cmd}")
    print("=" * 60)
    
    # Execute tests
    start_time = time.time()
    result = run_command(cmd, capture_output=False, check=False)
    end_time = time.time()
    
    # Display results
    duration = end_time - start_time
    print("\n" + "=" * 60)
    print(f"Test execution completed in {duration:.1f} seconds")
    
    if result:
        return result.returncode
    else:
        print("❌ Failed to execute tests")
        return 1

def cleanup_test_resources():
    """Clean up any remaining test resources."""
    print("\n🧹 Cleaning up test resources...")
    
    cleanup_count = 0
    
    # Remove Pi-hole test containers
    print("Checking for test containers...")
    result = run_command(
        "docker ps -a --filter name=pihole-test --format '{{.Names}}'",
        timeout=10
    )
    if result and result.stdout.strip():
        containers = [c for c in result.stdout.strip().split('\n') if c]
        for container in containers:
            print(f"  Removing container: {container}")
            run_command(f"docker rm -f {container}", timeout=10)
            cleanup_count += 1
    
    # Remove test networks
    print("Checking for test networks...")
    result = run_command(
        "docker network ls --filter name=pihole-test --format '{{.Name}}'",
        timeout=10
    )
    if result and result.stdout.strip():
        networks = [n for n in result.stdout.strip().split('\n') if n and n != "bridge"]
        for network in networks:
            print(f"  Removing network: {network}")
            run_command(f"docker network rm {network}", timeout=10)
            cleanup_count += 1
    
    # Remove test volumes
    print("Checking for test volumes...")
    result = run_command(
        "docker volume ls --filter name=pihole-test --format '{{.Name}}'",
        timeout=10
    )
    if result and result.stdout.strip():
        volumes = [v for v in result.stdout.strip().split('\n') if v]
        for volume in volumes:
            print(f"  Removing volume: {volume}")
            run_command(f"docker volume rm {volume}", timeout=10)
            cleanup_count += 1
    
    # Clean up orphaned containers (containers that might be from previous test runs)
    print("Checking for orphaned test containers...")
    result = run_command(
        "docker ps -a --filter label=pihole.test=true --format '{{.Names}}'",
        timeout=10
    )
    if result and result.stdout.strip():
        containers = [c for c in result.stdout.strip().split('\n') if c]
        for container in containers:
            print(f"  Removing orphaned container: {container}")
            run_command(f"docker rm -f {container}", timeout=10)
            cleanup_count += 1
    
    if cleanup_count > 0:
        print(f"✅ Cleaned up {cleanup_count} Docker resources")
    else:
        print("✅ No cleanup needed - all resources already clean")

def print_test_info():
    """Print information about available tests."""
    print("\n📋 Available Test Categories:")
    print("  01 - Authentication and Connection")
    print("  02 - DNS Configuration Retrieval") 
    print("  03 - A Record Management")
    print("  04 - CNAME Record Management")
    print("  05 - DNS Statistics and Search")
    print("  06 - Export Functionality")
    print("  07 - Error Handling and Validation")
    print("  08 - Bulk Operations Performance")
    print("  09 - Session Management")
    print("  10 - Complete Workflow Validation")
    print("\nExample usage:")
    print("  python run_tests_docker.py -t test_01              # Run authentication tests")
    print("  python run_tests_docker.py -t TestPiHole::test_03  # Run A record tests")
    print("  python run_tests_docker.py -k 'auth or dns'        # Run tests matching keywords")

def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Docker-based test runner for pihole6api",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run all tests
  %(prog)s -v                       # Verbose output  
  %(prog)s -t test_01               # Run authentication tests
  %(prog)s -k "auth and not bulk"   # Run auth tests but not bulk tests
  %(prog)s --cleanup-only           # Just cleanup and exit
  %(prog)s --info                   # Show test information
        """
    )
    
    # Test execution options
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose test output")
    parser.add_argument("-x", "--stop-on-failure", action="store_true",
                       help="Stop on first test failure")
    parser.add_argument("-t", "--test", type=str,
                       help="Run specific test pattern (e.g., test_01, TestPiHole::test_auth)")
    parser.add_argument("-k", "--keyword", type=str,
                       help="Run tests matching keyword expression")
    parser.add_argument("-p", "--parallel", action="store_true",
                       help="Run tests in parallel (requires pytest-xdist)")
    
    # System options
    parser.add_argument("--skip-prereq", action="store_true",
                       help="Skip prerequisite checks")
    parser.add_argument("--cleanup-only", action="store_true",
                       help="Only run cleanup and exit")
    parser.add_argument("--info", action="store_true",
                       help="Show test information and exit")
    
    args = parser.parse_args()
    
    # Handle info mode
    if args.info:
        print_test_info()
        return 0
    
    # Handle cleanup-only mode
    if args.cleanup_only:
        cleanup_test_resources()
        return 0
    
    print("🐳 pihole6api Docker Test Runner")
    print("=" * 50)
    
    try:
        # Check prerequisites
        if not args.skip_prereq:
            if not check_prerequisites():
                print("\n❌ Prerequisites not met. Use --skip-prereq to bypass checks.")
                return 1
        
        # Setup test environment
        if not setup_test_environment():
            print("\n❌ Failed to setup test environment")
            return 1
        
        # Determine test pattern
        test_pattern = args.test or args.keyword
        
        # Run tests
        exit_code = run_docker_tests(
            test_pattern=test_pattern,
            verbose=args.verbose,
            stop_on_failure=args.stop_on_failure,
            parallel=args.parallel
        )
        
        # Display final results
        if exit_code == 0:
            print("\n🎉 All tests passed successfully!")
            print("   The pihole6api library is working correctly with Docker Pi-hole containers.")
        else:
            print(f"\n❌ Tests failed with exit code {exit_code}")
            print("   Check the output above for details on failed tests.")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user (Ctrl+C)")
        return 130
    
    except Exception as e:
        print(f"\n💥 Unexpected error during test execution: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Always attempt cleanup
        try:
            cleanup_test_resources()
        except Exception as e:
            print(f"⚠️  Warning: Cleanup failed: {e}")

if __name__ == "__main__":
    sys.exit(main())