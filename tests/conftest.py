"""
Test configuration and shared fixtures for pihole6api tests.
Includes both unit test mocks and Docker-based integration test fixtures.
"""

import os
import sys
import time
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load test environment configuration for Docker tests
load_dotenv(Path(__file__).parent / ".env.test")

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pihole6api import PiHole6Client, PiHole6Connection


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"status": "success"}
    return response


@pytest.fixture
def sample_dns_config():
    """Sample DNS configuration data for testing."""
    return {
        "config": {
            "dns": {
                "hosts": [
                    "192.168.1.100 server1.local",
                    "192.168.1.101 server2.local server2-alt.local",
                    "10.0.0.5 nas.home.local"
                ],
                "cnameRecords": [
                    "www.local,server1.local",
                    "api.local,server2.local,3600",
                    "storage.local,nas.home.local"
                ]
            }
        }
    }


@pytest.fixture
def expected_dns_records():
    """Expected parsed DNS records for testing."""
    return {
        "A": {
            "server1.local": "192.168.1.100",
            "server2.local": "192.168.1.101",
            "server2-alt.local": "192.168.1.101",
            "nas.home.local": "10.0.0.5"
        },
        "CNAME": {
            "www.local": "server1.local",
            "api.local": "server2.local",
            "storage.local": "nas.home.local"
        }
    }


# Docker-based integration test fixtures
from tests.docker_test_manager import PiHoleDockerTestManager


@pytest.fixture(scope="session")
def docker_manager():
    """Fixture to manage Docker container lifecycle for the entire test session."""
    manager = PiHoleDockerTestManager()
    
    print("\n🐳 Starting Pi-hole Docker container...")
    if not manager.start_container():
        pytest.fail("Failed to start Pi-hole Docker container")
    
    print("⏳ Waiting for Pi-hole to be fully ready...")
    time.sleep(5)  # Give it extra time to initialize
    
    # Verify we can connect
    base_url = os.getenv("PIHOLE_TEST_URL", "http://localhost:42345")
    password = os.getenv("PIHOLE_TEST_PASSWORD", "test_password_123")
    
    try:
        test_client = PiHole6Client(base_url, password)
        test_client.close_session()
        print("✅ Pi-hole is ready for testing!")
        yield manager
    except Exception as e:
        manager.stop_container()
        pytest.fail(f"Pi-hole is not responding properly: {e}")
    finally:
        print("\n🧹 Cleaning up Docker container...")
        manager.stop_container()


@pytest.fixture(scope="session")
def test_config():
    """Fixture providing test configuration from environment variables."""
    return {
        'base_url': os.getenv("PIHOLE_TEST_URL", "http://localhost:42345"),
        'password': os.getenv("PIHOLE_TEST_PASSWORD", "test_password_123"),
        'domain_base': os.getenv("TEST_DOMAIN_BASE", "test.local"),
        'ip_base': os.getenv("TEST_IP_BASE", "192.168.99"),
    }


@pytest.fixture(scope="session")
def pihole_client(docker_manager, test_config):
    """Fixture providing a configured PiHole6Client for testing."""
    # Verify we can connect
    client = PiHole6Client(test_config['base_url'], test_config['password'])
    
    try:
        # Test basic connectivity
        client.local_dns.get_all_records()
        print("✅ Pi-hole is ready for testing!")
        yield client
    except Exception as e:
        pytest.fail(f"Failed to connect to Pi-hole: {e}")
    finally:
        try:
            client.close_session()
        except:
            pass


@pytest.fixture
def fresh_client(test_config):
    """Fixture providing a fresh PiHole6Client instance for each test."""
    client = PiHole6Client(test_config['base_url'], test_config['password'])
    yield client
    try:
        client.close_session()
    except:
        pass


@pytest.fixture
def test_data(test_config):
    """Fixture providing common test data patterns."""
    return {
        'domain_base': test_config['domain_base'],
        'ip_base': test_config['ip_base'],
        'test_domain': f"test.{test_config['domain_base']}",
        'test_ip': f"{test_config['ip_base']}.100",
        'test_cname': f"alias.{test_config['domain_base']}",
        'test_target': f"target.{test_config['domain_base']}",
    }