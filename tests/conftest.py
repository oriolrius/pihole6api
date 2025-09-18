"""
Test configuration and shared fixtures for pihole6api tests.
"""

import os
import pytest
from unittest.mock import Mock, patch
from pihole6api import PiHole6Client, PiHole6Connection


# Test configuration
TEST_BASE_URL = "http://test-pihole:42345"
TEST_PASSWORD = "test_password"
TEST_SESSION_ID = "test_session_123"


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"status": "success"}
    return response


@pytest.fixture
def mock_auth_response():
    """Create a mock authentication response."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "session": {"sid": TEST_SESSION_ID},
        "status": "success"
    }
    return response


@pytest.fixture
def mock_connection():
    """Create a mock connection for testing."""
    with patch('pihole6api.conn.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "session": {"sid": TEST_SESSION_ID}
        }
        
        connection = PiHole6Connection(TEST_BASE_URL, TEST_PASSWORD)
        yield connection


@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    with patch('pihole6api.conn.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "session": {"sid": TEST_SESSION_ID}
        }
        
        client = PiHole6Client(TEST_BASE_URL, TEST_PASSWORD)
        yield client


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