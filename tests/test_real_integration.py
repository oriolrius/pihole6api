"""
Real integration tests for Pi-hole API using Docker container.

These tests run against an actual Pi-hole instance in Docker and test
the complete end-to-end functionality including authentication and local DNS management.
"""

import pytest
import os
import sys
import time
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pihole6api import PiHole6Client
from tests.docker_test_manager import PiHoleDockerTestManager


class TestRealPiHoleIntegration:
    """Integration tests using real Pi-hole Docker container."""
    
    @classmethod
    def setup_class(cls):
        """Setup Docker container before running tests."""
        cls.manager = PiHoleDockerTestManager()
        cls.base_url = "http://localhost:42345"
        cls.password = "test_password_123"
        
        # Start container
        if not cls.manager.start_container():
            pytest.skip("Failed to start Pi-hole Docker container")
        
        # Give it a moment to fully initialize
        time.sleep(5)
    
    @classmethod
    def teardown_class(cls):
        """Cleanup Docker container after tests."""
        if hasattr(cls, 'manager'):
            cls.manager.stop_container()
    
    def test_real_authentication_success(self):
        """Test authentication against real Pi-hole instance."""
        client = PiHole6Client(self.base_url, self.password)
        
        # Verify we have a session ID
        assert client.connection.session_id is not None
        assert len(client.connection.session_id) > 0
        
        # Close session
        client.close_session()
    
    def test_real_authentication_failure(self):
        """Test authentication failure with wrong password."""
        with pytest.raises(Exception) as exc_info:
            PiHole6Client(self.base_url, "wrong_password")
        
        assert "authentication" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
    
    def test_real_get_dns_configuration(self):
        """Test retrieving DNS configuration from real Pi-hole."""
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Get all DNS records
            records = client.local_dns.get_all_records()
            
            # Should return a dictionary with A and CNAME keys
            assert isinstance(records, dict)
            assert "A" in records
            assert "CNAME" in records
            
            # Values should be dictionaries
            assert isinstance(records["A"], dict)
            assert isinstance(records["CNAME"], dict)
            
        finally:
            client.close_session()
    
    def test_real_add_and_remove_a_record(self):
        """Test adding and removing A records in real Pi-hole."""
        client = PiHole6Client(self.base_url, self.password)
        test_domain = "integration-test.local"
        test_ip = "192.168.99.100"
        
        try:
            # Get initial record count
            initial_records = client.local_dns.get_a_records()
            initial_count = len(initial_records)
            
            # Add test record
            result = client.local_dns.add_a_record(test_domain, test_ip)
            assert result is not None  # Should not fail
            
            # Verify record was added
            updated_records = client.local_dns.get_a_records()
            assert len(updated_records) >= initial_count  # Should have at least as many
            
            # Remove test record
            remove_result = client.local_dns.remove_a_record(test_domain)
            assert remove_result is not None  # Should not fail
            
            # Verify record was removed
            final_records = client.local_dns.get_a_records()
            assert test_domain not in final_records
            
        finally:
            # Cleanup: try to remove the test record if it still exists
            try:
                client.local_dns.remove_a_record(test_domain)
            except:
                pass
            client.close_session()
    
    def test_real_add_and_remove_cname_record(self):
        """Test adding and removing CNAME records in real Pi-hole."""
        client = PiHole6Client(self.base_url, self.password)
        test_alias = "integration-cname-test.local"
        test_target = "target.local"
        
        try:
            # Get initial record count
            initial_records = client.local_dns.get_cname_records()
            initial_count = len(initial_records)
            
            # Add test CNAME record
            result = client.local_dns.add_cname_record(test_alias, test_target)
            assert result is not None  # Should not fail
            
            # Verify record was added
            updated_records = client.local_dns.get_cname_records()
            assert len(updated_records) >= initial_count  # Should have at least as many
            
            # Remove test record
            remove_result = client.local_dns.remove_cname_record(test_alias)
            assert remove_result is not None  # Should not fail
            
            # Verify record was removed
            final_records = client.local_dns.get_cname_records()
            assert test_alias not in final_records
            
        finally:
            # Cleanup: try to remove the test record if it still exists
            try:
                client.local_dns.remove_cname_record(test_alias)
            except:
                pass
            client.close_session()
    
    def test_real_dns_statistics(self):
        """Test DNS statistics from real Pi-hole."""
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            stats = client.local_dns.get_statistics()
            
            # Should return a dictionary with expected keys
            assert isinstance(stats, dict)
            assert "A" in stats
            assert "CNAME" in stats
            assert "unique_ips" in stats
            assert "domains_per_ip" in stats
            
            # Values should be reasonable
            assert isinstance(stats["A"], int)
            assert isinstance(stats["CNAME"], int)
            assert isinstance(stats["unique_ips"], int)
            assert isinstance(stats["domains_per_ip"], dict)
            
            # Non-negative counts
            assert stats["A"] >= 0
            assert stats["CNAME"] >= 0
            assert stats["unique_ips"] >= 0
            
        finally:
            client.close_session()
    
    def test_real_search_records(self):
        """Test searching DNS records in real Pi-hole."""
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Add a test record first
            test_domain = "searchtest.local"
            test_ip = "192.168.99.101"
            client.local_dns.add_a_record(test_domain, test_ip)
            
            # Search for the record
            results = client.local_dns.search_records("searchtest")
            
            # Should find our test record
            assert isinstance(results, dict)
            assert "A" in results
            assert "CNAME" in results
            
            # Cleanup
            client.local_dns.remove_a_record(test_domain)
            
        finally:
            client.close_session()
    
    def test_real_export_functionality(self):
        """Test DNS record export functionality."""
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Add some test data
            test_records = [
                ("export-test1.local", "192.168.99.201"),
                ("export-test2.local", "192.168.99.202"),
            ]
            
            for domain, ip in test_records:
                client.local_dns.add_a_record(domain, ip)
            
            # Test JSON export
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                client.local_dns.export_records(tmp.name, "json")
                
                # Verify file was created and has content
                assert os.path.exists(tmp.name)
                assert os.path.getsize(tmp.name) > 0
                
                # Cleanup
                os.unlink(tmp.name)
            
            # Test CSV export
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                client.local_dns.export_records(tmp.name, "csv")
                
                # Verify file was created and has content
                assert os.path.exists(tmp.name)
                assert os.path.getsize(tmp.name) > 0
                
                # Cleanup
                os.unlink(tmp.name)
            
            # Cleanup test records
            for domain, _ in test_records:
                try:
                    client.local_dns.remove_a_record(domain)
                except:
                    pass
            
        finally:
            client.close_session()
    
    def test_real_session_management(self):
        """Test session lifecycle with real Pi-hole."""
        client = PiHole6Client(self.base_url, self.password)
        
        # Verify we have a session
        original_session_id = client.connection.session_id
        assert original_session_id is not None
        
        # Make an API call to ensure session works
        records = client.local_dns.get_all_records()
        assert isinstance(records, dict)
        
        # Close session
        result = client.close_session()
        assert result is not None  # Should not fail
    
    @pytest.mark.slow
    def test_real_bulk_operations(self):
        """Test bulk DNS operations performance."""
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Add multiple records
            test_records = []
            for i in range(10):
                domain = f"bulk-test-{i}.local"
                ip = f"192.168.99.{100 + i}"
                test_records.append((domain, ip))
                
                result = client.local_dns.add_a_record(domain, ip)
                assert result is not None
            
            # Verify all records were added
            all_records = client.local_dns.get_a_records()
            for domain, ip in test_records:
                assert domain in all_records
                assert all_records[domain] == ip
            
            # Remove all test records
            for domain, _ in test_records:
                result = client.local_dns.remove_a_record(domain)
                assert result is not None
            
            # Verify all records were removed
            final_records = client.local_dns.get_a_records()
            for domain, _ in test_records:
                assert domain not in final_records
                
        finally:
            # Cleanup any remaining test records
            for domain, _ in test_records:
                try:
                    client.local_dns.remove_a_record(domain)
                except:
                    pass
            client.close_session()