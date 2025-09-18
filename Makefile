# Makefile for pihole6api Docker-based testing and development
# 
# This Makefile provides convenient commands for managing the Docker-based
# testing infrastructure and development workflow.

.PHONY: help test test-verbose test-quick test-auth test-dns test-perf test-cleanup info install deps clean check-docker docker-logs docker-status

# Default target
help:
	@echo "🐳 pihole6api Docker Test Environment"
	@echo "====================================="
	@echo ""
	@echo "Test Commands:"
	@echo "  test              Run all Docker-based tests"
	@echo "  test-verbose      Run tests with verbose output"
	@echo "  test-quick        Run core tests only (skip performance tests)"
	@echo "  test-auth         Run authentication tests only"
	@echo "  test-dns          Run DNS management tests only"
	@echo "  test-perf         Run performance/bulk operation tests only"
	@echo "  test-cleanup      Cleanup test resources and exit"
	@echo ""
	@echo "Docker Management:"
	@echo "  check-docker      Verify Docker prerequisites"
	@echo "  docker-logs       Show Pi-hole container logs"
	@echo "  docker-status     Show Docker container status"
	@echo "  docker-clean      Remove all test containers and resources"
	@echo ""
	@echo "Development:"
	@echo "  install           Install package in development mode"
	@echo "  deps              Install all dependencies"
	@echo "  clean             Clean up Python cache files"
	@echo "  info              Show test information and examples"
	@echo ""
	@echo "Environment Variables:"
	@echo "  VERBOSE=1         Enable verbose output for any test command"
	@echo "  STOP_ON_FAIL=1    Stop on first test failure"
	@echo "  PARALLEL=1        Run tests in parallel (where supported)"

# Test commands
test:
	@echo "🧪 Running complete Docker-based test suite..."
	python run_tests_docker.py $(if $(VERBOSE),-v) $(if $(STOP_ON_FAIL),-x) $(if $(PARALLEL),-p)

test-verbose:
	@echo "🧪 Running tests with verbose output..."
	python run_tests_docker.py -v $(if $(STOP_ON_FAIL),-x)

test-quick:
	@echo "🧪 Running core tests (excluding performance tests)..."
	python run_tests_docker.py -k "not bulk and not perf" $(if $(VERBOSE),-v) $(if $(STOP_ON_FAIL),-x)

test-auth:
	@echo "🔐 Running authentication and connection tests..."
	python run_tests_docker.py -t test_01 $(if $(VERBOSE),-v)

test-dns:
	@echo "📋 Running DNS management tests..."
	python run_tests_docker.py -k "test_02 or test_03 or test_04 or test_05" $(if $(VERBOSE),-v)

test-perf:
	@echo "🚀 Running performance and bulk operation tests..."
	python run_tests_docker.py -k "bulk or perf or test_08" $(if $(VERBOSE),-v)

test-cleanup:
	@echo "🧹 Running cleanup only..."
	python run_tests_docker.py --cleanup-only

# Docker management commands  
check-docker:
	@echo "🐳 Checking Docker prerequisites..."
	@python run_tests_docker.py --info

docker-logs:
	@echo "📄 Showing Pi-hole container logs..."
	@docker logs pihole-test-container 2>/dev/null || echo "No Pi-hole test container running"

docker-status:
	@echo "📊 Docker container status:"
	@docker ps -a --filter name=pihole-test --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No test containers found"
	@echo ""
	@echo "📊 Docker network status:"
	@docker network ls --filter name=pihole-test --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>/dev/null || echo "No test networks found"

docker-clean:
	@echo "🧹 Cleaning up all Docker test resources..."
	@docker ps -a --filter name=pihole-test -q | xargs -r docker rm -f
	@docker network ls --filter name=pihole-test -q | xargs -r docker network rm
	@docker volume ls --filter name=pihole-test -q | xargs -r docker volume rm
	@echo "✅ Docker cleanup complete"

# Development commands
install:
	@echo "📦 Installing pihole6api in development mode..."
	pip install -e .

deps:
	@echo "📦 Installing all dependencies..."
	pip install -e .
	pip install pytest>=7.0.0 requests>=2.25.0
	@echo "✅ Dependencies installed"

clean:
	@echo "🧹 Cleaning Python cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ 2>/dev/null || true
	@echo "✅ Python cache cleanup complete"

info:
	@echo "📋 Test Information and Usage Examples"
	@echo "======================================"
	python run_tests_docker.py --info

# Advanced test patterns
test-integration:
	@echo "🔄 Running integration workflow tests..."
	python run_tests_docker.py -k "workflow or integration" $(if $(VERBOSE),-v)

test-error-handling:
	@echo "⚠️  Running error handling and validation tests..."
	python run_tests_docker.py -k "error or validation" $(if $(VERBOSE),-v)

test-export:
	@echo "💾 Running export functionality tests..."
	python run_tests_docker.py -k "export" $(if $(VERBOSE),-v)

# Continuous Integration helpers
ci-test:
	@echo "🤖 Running CI test suite..."
	python run_tests_docker.py -v --stop-on-failure

ci-quick:
	@echo "🤖 Running CI quick test suite..."
	python run_tests_docker.py -k "not bulk and not perf" -v --stop-on-failure

# Development helpers
dev-test:
	@echo "👨‍💻 Running development test cycle..."
	make clean
	make install
	make test-quick
	
dev-full:
	@echo "👨‍💻 Running full development test cycle..."
	make clean
	make deps
	make test

# Debug helpers
debug-docker:
	@echo "🔍 Docker debugging information:"
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker info:"
	@docker info | head -10
	@echo ""
	@echo "Running containers:"
	@docker ps
	@echo ""
	@echo "Test containers (all states):"
	@docker ps -a --filter name=pihole-test

debug-env:
	@echo "🔍 Environment debugging information:"
	@echo "Python version: $(shell python --version)"
	@echo "Pytest version: $(shell pytest --version 2>/dev/null || echo 'Not installed')"
	@echo "Working directory: $(shell pwd)"
	@echo "Python path: $(shell python -c 'import sys; print(sys.path[0])')"