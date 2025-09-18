"""
Integration tests for PiHole6Client with local DNS functionality.

These tests verify the end-to-end functionality of the client
with the local DNS management features.
"""

import pytest
from unittest.mock import Mock, patch
from pihole6api import PiHole6Client


class TestPiHole6ClientIntegration:
    """Integration tests for PiHole6Client with local DNS."""

    @pytest.fixture
    def mock_auth_and_responses(self):
        """Setup mock authentication and API responses."""
        with patch('pihole6api.conn.requests.post') as mock_post, \
             patch('pihole6api.conn.requests.get') as mock_get:
            
            # Mock authentication
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {"session": {"sid": "test_session"}}
            mock_post.return_value = auth_response
            
            # Mock config response
            config_response = Mock()
            config_response.status_code = 200
            config_response.json.return_value = {
                "config": {
                    "dns": {
                        "hosts": [
                            "192.168.1.100 server1.local",
                            "192.168.1.101 server2.local"
                        ],
                        "cnameRecords": [
                            "www.local,server1.local"
                        ]
                    }
                }
            }
            mock_get.return_value = config_response
            
            yield mock_post, mock_get

    def test_client_local_dns_integration(self, mock_auth_and_responses):
        """Test full client integration with local DNS functionality."""
        mock_post, mock_get = mock_auth_and_responses
        
        # Create client
        client = PiHole6Client("http://test-pihole:42345", "test_password")
        
        # Test local DNS functionality
        all_records = client.local_dns.get_all_records()
        
        # Verify authentication occurred
        mock_post.assert_called_with(
            "http://test-pihole:42345/api/auth",
            json={"password": "test_password"}
        )
        
        # Verify config was fetched
        mock_get.assert_called_with(
            "http://test-pihole:42345/api/config",
            headers={"sid": "test_session"},
            params=None
        )
        
        # Verify parsed data
        expected = {
            "A": {
                "server1.local": "192.168.1.100",
                "server2.local": "192.168.1.101"
            },
            "CNAME": {
                "www.local": "server1.local"
            }
        }
        
        assert all_records == expected

    def test_client_local_dns_statistics(self, mock_auth_and_responses):
        """Test statistics functionality through client."""
        mock_post, mock_get = mock_auth_and_responses
        
        client = PiHole6Client("http://test-pihole:42345", "test_password")
        stats = client.local_dns.get_statistics()
        
        expected_stats = {
            "A": 2,
            "CNAME": 1,
            "unique_ips": 2,
            "domains_per_ip": {
                "192.168.1.100": 1,
                "192.168.1.101": 1
            }
        }
        
        assert stats == expected_stats

    def test_client_add_dns_record_workflow(self):
        """Test complete workflow of adding DNS records through client."""
        with patch('pihole6api.conn.requests.post') as mock_post:
            # Mock authentication
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {"session": {"sid": "test_session"}}
            
            # Mock add record response
            add_response = Mock()
            add_response.status_code = 200
            add_response.json.return_value = {"success": True}
            
            mock_post.side_effect = [auth_response, add_response]
            
            # Create client and add record
            client = PiHole6Client("http://test-pihole:42345", "test_password")
            result = client.local_dns.add_a_record("newserver.local", "192.168.1.200")
            
            # Verify authentication and add record calls
            expected_calls = [
                ("http://test-pihole:42345/api/auth", {"json": {"password": "test_password"}}),
                ("http://test-pihole:42345/api/config/dns/hosts", {
                    "json": {"domain": "newserver.local", "ip": "192.168.1.200"},
                    "headers": {"sid": "test_session"}
                })
            ]
            
            assert mock_post.call_count == 2
            assert result == {"success": True}

    def test_client_session_management(self):
        """Test session management through client."""
        with patch('pihole6api.conn.requests.post') as mock_post:
            # Mock authentication
            auth_response = Mock()
            auth_response.status_code = 200
            auth_response.json.return_value = {"session": {"sid": "test_session"}}
            
            # Mock exit response
            exit_response = Mock()
            exit_response.status_code = 200
            exit_response.json.return_value = {"status": "logged out"}
            
            mock_post.side_effect = [auth_response, exit_response]
            
            # Create client and close session
            client = PiHole6Client("http://test-pihole:42345", "test_password")
            result = client.close_session()
            
            # Verify both authentication and exit calls
            assert mock_post.call_count == 2
            assert result == {"status": "logged out"}


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases."""

    def test_invalid_ip_validation(self):
        """Test IP address validation in various scenarios."""
        from pihole6api.local_dns import PiHole6LocalDNS
        
        connection = Mock()
        local_dns = PiHole6LocalDNS(connection)
        
        invalid_ips = [
            "256.1.1.1",      # Out of range
            "192.168.1",      # Incomplete
            "not.an.ip",      # Text
            "192.168.1.1.1",  # Too many octets
            "",               # Empty
            "192.168.1.-1",   # Negative
        ]
        
        for invalid_ip in invalid_ips:
            with pytest.raises(ValueError, match="Invalid IP address"):
                local_dns.add_a_record("test.local", invalid_ip)

    def test_domain_validation(self):
        """Test domain name validation."""
        from pihole6api.local_dns import PiHole6LocalDNS
        
        connection = Mock()
        local_dns = PiHole6LocalDNS(connection)
        
        invalid_domains = [
            "",              # Empty
            " ",             # Whitespace only
            "test..local",   # Double dots
            ".test.local",   # Leading dot
            "test.local.",   # Trailing dot (might be valid in some contexts)
        ]
        
        for invalid_domain in invalid_domains:
            with pytest.raises(ValueError):
                local_dns.add_a_record(invalid_domain, "192.168.1.100")

    def test_concurrent_access_simulation(self):
        """Test behavior under simulated concurrent access."""
        import threading
        import time
        from pihole6api.local_dns import PiHole6LocalDNS
        
        connection = Mock()
        connection.get.return_value = {
            "config": {
                "dns": {
                    "hosts": ["192.168.1.100 server.local"],
                    "cnameRecords": []
                }
            }
        }
        
        local_dns = PiHole6LocalDNS(connection)
        results = []
        
        def worker():
            try:
                result = local_dns.get_all_records()
                results.append(result)
            except Exception as e:
                results.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
            assert "A" in result

    def test_large_dataset_handling(self):
        """Test handling of large DNS record datasets."""
        from pihole6api.local_dns import PiHole6LocalDNS
        
        connection = Mock()
        
        # Generate large dataset
        hosts = []
        cname_records = []
        
        for i in range(1000):
            hosts.append(f"192.168.{i//256}.{i%256} server{i}.local")
            if i % 2 == 0:  # Every other record gets a CNAME
                cname_records.append(f"alias{i}.local,server{i}.local")
        
        connection.get.return_value = {
            "config": {
                "dns": {
                    "hosts": hosts,
                    "cnameRecords": cname_records
                }
            }
        }
        
        local_dns = PiHole6LocalDNS(connection)
        
        # Test retrieval
        result = local_dns.get_all_records()
        
        assert len(result["A"]) == 1000
        assert len(result["CNAME"]) == 500
        
        # Test statistics
        stats = local_dns.get_statistics()
        assert stats["A"] == 1000
        assert stats["CNAME"] == 500

    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        import sys
        from pihole6api.local_dns import PiHole6LocalDNS
        
        connection = Mock()
        
        # Create a moderately large dataset
        hosts = [f"192.168.1.{i} server{i}.local" for i in range(100, 200)]
        cname_records = [f"alias{i}.local,server{i}.local" for i in range(100, 150)]
        
        connection.get.return_value = {
            "config": {
                "dns": {
                    "hosts": hosts,
                    "cnameRecords": cname_records
                }
            }
        }
        
        local_dns = PiHole6LocalDNS(connection)
        
        # Measure memory usage (basic check)
        initial_refs = sys.gettotalrefcount() if hasattr(sys, 'gettotalrefcount') else 0
        
        # Perform multiple operations
        for _ in range(10):
            records = local_dns.get_all_records()
            stats = local_dns.get_statistics()
            del records, stats
        
        # Memory shouldn't grow significantly
        # This is a basic check - in real scenarios you'd use memory profilers
        if hasattr(sys, 'gettotalrefcount'):
            final_refs = sys.gettotalrefcount()
            # Allow some growth but not excessive
            assert final_refs - initial_refs < 1000