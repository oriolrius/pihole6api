"""
Authentication and connection tests for pihole6api Docker integration.

Tests authentication, basic connectivity, and session management functionality.
"""

import pytest
import os
from pihole6api import PiHole6Client


class TestAuthConnection:
    """Test authentication, connection, and session management."""

    def test_01_authentication_and_connection(self, docker_manager, test_config):
        """Test basic authentication and connection functionality."""
        print("\n🔐 Testing authentication...")
        
        # Test successful authentication
        client = PiHole6Client(test_config['base_url'], test_config['password'])
        
        try:
            # Test authentication
            assert client.connection.session_id is not None
            print(f"✅ Authentication successful, session ID: {client.connection.session_id[:8]}...")
            
            # Test session closure
            client.close_session()
            print("✅ Session closed successfully")
            
        finally:
            try:
                client.close_session()
            except:
                pass
        
        # Test authentication with wrong password
        print("🔒 Testing authentication with wrong password...")
        try:
            wrong_client = PiHole6Client(test_config['base_url'], "wrong_password")
            wrong_client.local_dns.get_all_records()  # This should fail
            pytest.fail("Authentication should have failed with wrong password")
        except Exception as e:
            print("✅ Authentication correctly rejects wrong password")
            assert "authentication" in str(e).lower() or "unauthorized" in str(e).lower()

    def test_02_get_initial_dns_configuration(self, fresh_client):
        """Test retrieving initial DNS configuration."""
        print("\n📋 Testing DNS configuration retrieval...")
        
        try:
            # Get all records
            all_records = fresh_client.local_dns.get_all_records()
            
            assert isinstance(all_records, dict)
            assert "A" in all_records
            assert "CNAME" in all_records
            assert isinstance(all_records["A"], dict)
            assert isinstance(all_records["CNAME"], dict)
            
            a_count = len(all_records["A"])
            cname_count = len(all_records["CNAME"])
            
            print(f"✅ Retrieved DNS config - A records: {a_count}, CNAME records: {cname_count}")
            
            # Test individual record type retrieval
            a_records = fresh_client.local_dns.get_a_records()
            cname_records = fresh_client.local_dns.get_cname_records()
            
            assert isinstance(a_records, dict)
            assert isinstance(cname_records, dict)
            assert len(a_records) == a_count
            assert len(cname_records) == cname_count
            
            print("✅ Individual record type retrieval works correctly")
            
        finally:
            fresh_client.close_session()

    def test_09_session_persistence_and_reuse(self, docker_manager, test_config):
        """Test session management and persistence."""
        print("\n🔄 Testing session management...")
        
        # Test that sessions work across multiple operations
        client = PiHole6Client(test_config['base_url'], test_config['password'])
        original_session_id = client.connection.session_id
        
        try:
            # Perform multiple operations with the same session
            for i in range(3):
                records = client.local_dns.get_all_records()
                assert isinstance(records, dict)
                # Session ID should remain the same
                assert client.connection.session_id == original_session_id
            
            print("✅ Session persists across multiple operations")
            
            # Test explicit session closure
            result = client.close_session()
            print(f"Session close result: {result}")
            
            print("✅ Session management works correctly")
            
        finally:
            try:
                client.close_session()
            except:
                pass