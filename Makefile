.PHONY: help test test-cov test-fast test-integration test-unit test-docker test-docker-only install install-dev clean lint format docker-start docker-stop

help:
	@echo "Available commands:"
	@echo "  test           - Run all tests (unit + mocked integration)"
	@echo "  test-cov       - Run tests with coverage report"
	@echo "  test-fast      - Run fast tests only (exclude slow)"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-docker    - Run full test suite with Docker integration"
	@echo "  test-docker-only - Run only Docker-based integration tests"
	@echo "  docker-start   - Start Pi-hole Docker container for testing"
	@echo "  docker-stop    - Stop Pi-hole Docker container"
	@echo "  install        - Install package and dependencies"
	@echo "  install-dev    - Install package with dev dependencies"
	@echo "  clean          - Clean build artifacts and cache"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black and isort"

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=src/pihole6api --cov-report=html --cov-report=term

test-fast:
	python -m pytest tests/ -v -m "not slow"

test-integration:
	python -m pytest tests/ -v -m "integration"

test-unit:
	python -m pytest tests/ -v -m "unit"

# Docker-based testing
test-docker:
	python run_tests_docker.py all --verbose

test-docker-only:
	python run_tests_docker.py integration --verbose

docker-start:
	python run_tests_docker.py --docker-only --docker-action start

docker-stop:
	python run_tests_docker.py --docker-only --docker-action stop

docker-logs:
	python run_tests_docker.py --docker-only --docker-action logs

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

# Test specific modules
test-auth:
	python -m pytest tests/test_authentication.py -v

test-localdns:
	python -m pytest tests/test_local_dns.py -v

test-integration-only:
	python -m pytest tests/test_integration.py -v