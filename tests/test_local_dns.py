"""
Tests for PiHole6LocalDNS class functionality.

These tests verify the comprehensive local DNS management features
including A records, CNAME records, statistics, and export functionality.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from pihole6api.local_dns import PiHole6LocalDNS


class TestPiHole6LocalDNS:
    """Test class for local DNS management functionality."""

    @pytest.fixture
    def mock_connection(self):
        """Create a mock connection for local DNS tests."""
        connection = Mock()
        connection.session_id = "test_session_123"
        return connection

    @pytest.fixture
    def local_dns(self, mock_connection):
        """Create PiHole6LocalDNS instance with mock connection."""
        return PiHole6LocalDNS(mock_connection)

    @pytest.fixture
    def sample_config_response(self):
        """Sample configuration response from Pi-hole API."""
        return {
            "config": {
                "dns": {
                    "hosts": [
                        "192.168.1.100 server1.local",
                        "192.168.1.101 server2.local server2-alt.local",
                        "10.0.0.5 nas.home.local storage.local",
                        "172.16.1.10 printer.local"
                    ],
                    "cnameRecords": [
                        "www.local,server1.local",
                        "api.local,server2.local,3600",
                        "storage.local,nas.home.local",
                        "backup.local,storage.local,7200"
                    ]
                }
            }
        }

    def test_get_all_records_success(self, local_dns, mock_connection, sample_config_response):
        """Test successful retrieval of all DNS records."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.get_all_records()
        
        # Verify API call
        mock_connection.get.assert_called_once_with("config")
        
        # Verify parsed results
        expected_a_records = {
            "server1.local": "192.168.1.100",
            "server2.local": "192.168.1.101",
            "server2-alt.local": "192.168.1.101",
            "nas.home.local": "10.0.0.5",
            "storage.local": "10.0.0.5",
            "printer.local": "172.16.1.10"
        }
        
        expected_cname_records = {
            "www.local": "server1.local",
            "api.local": "server2.local",
            "storage.local": "nas.home.local",
            "backup.local": "storage.local"
        }
        
        assert result["A"] == expected_a_records
        assert result["CNAME"] == expected_cname_records

    def test_get_a_records_only(self, local_dns, mock_connection, sample_config_response):
        """Test retrieval of A records only."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.get_a_records()
        
        expected = {
            "server1.local": "192.168.1.100",
            "server2.local": "192.168.1.101",
            "server2-alt.local": "192.168.1.101",
            "nas.home.local": "10.0.0.5",
            "storage.local": "10.0.0.5",
            "printer.local": "172.16.1.10"
        }
        
        assert result == expected

    def test_get_cname_records_only(self, local_dns, mock_connection, sample_config_response):
        """Test retrieval of CNAME records only."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.get_cname_records()
        
        expected = {
            "www.local": "server1.local",
            "api.local": "server2.local",
            "storage.local": "nas.home.local",
            "backup.local": "storage.local"
        }
        
        assert result == expected

    def test_get_statistics(self, local_dns, mock_connection, sample_config_response):
        """Test DNS statistics calculation."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.get_statistics()
        
        expected = {
            "A": 6,
            "CNAME": 4,
            "unique_ips": 4,
            "domains_per_ip": {
                "192.168.1.100": 1,
                "192.168.1.101": 2,
                "10.0.0.5": 2,
                "172.16.1.10": 1
            }
        }
        
        assert result == expected

    def test_add_a_record_success(self, local_dns, mock_connection):
        """Test successful addition of A record."""
        mock_connection.post.return_value = {"success": True}
        
        result = local_dns.add_a_record("newserver.local", "192.168.1.200")
        
        # Verify API call
        expected_data = {
            "domain": "newserver.local",
            "ip": "192.168.1.200"
        }
        mock_connection.post.assert_called_once_with("config/dns/hosts", data=expected_data)
        
        assert result == {"success": True}

    def test_add_a_record_invalid_ip(self, local_dns, mock_connection):
        """Test addition of A record with invalid IP."""
        with pytest.raises(ValueError) as exc_info:
            local_dns.add_a_record("test.local", "invalid_ip")
        
        assert "Invalid IP address" in str(exc_info.value)
        mock_connection.post.assert_not_called()

    def test_add_a_record_invalid_domain(self, local_dns, mock_connection):
        """Test addition of A record with invalid domain."""
        with pytest.raises(ValueError) as exc_info:
            local_dns.add_a_record("", "192.168.1.100")
        
        assert "Domain cannot be empty" in str(exc_info.value)
        mock_connection.post.assert_not_called()

    def test_add_cname_record_success(self, local_dns, mock_connection):
        """Test successful addition of CNAME record."""
        mock_connection.post.return_value = {"success": True}
        
        result = local_dns.add_cname_record("alias.local", "target.local", 3600)
        
        expected_data = {
            "source": "alias.local",
            "target": "target.local",
            "ttl": 3600
        }
        mock_connection.post.assert_called_once_with("config/dns/cnameRecords", data=expected_data)
        
        assert result == {"success": True}

    def test_add_cname_record_default_ttl(self, local_dns, mock_connection):
        """Test addition of CNAME record with default TTL."""
        mock_connection.post.return_value = {"success": True}
        
        local_dns.add_cname_record("alias.local", "target.local")
        
        expected_data = {
            "source": "alias.local",
            "target": "target.local",
            "ttl": None
        }
        mock_connection.post.assert_called_once_with("config/dns/cnameRecords", data=expected_data)

    def test_remove_a_record_success(self, local_dns, mock_connection):
        """Test successful removal of A record."""
        mock_connection.delete.return_value = {"success": True}
        
        result = local_dns.remove_a_record("oldserver.local")
        
        mock_connection.delete.assert_called_once_with("config/dns/hosts/oldserver.local")
        assert result == {"success": True}

    def test_remove_cname_record_success(self, local_dns, mock_connection):
        """Test successful removal of CNAME record."""
        mock_connection.delete.return_value = {"success": True}
        
        result = local_dns.remove_cname_record("oldalias.local")
        
        mock_connection.delete.assert_called_once_with("config/dns/cnameRecords/oldalias.local")
        assert result == {"success": True}

    def test_update_a_record_success(self, local_dns, mock_connection):
        """Test successful update of A record."""
        mock_connection.put.return_value = {"success": True}
        
        result = local_dns.update_a_record("server.local", "192.168.1.250")
        
        expected_data = {
            "domain": "server.local",
            "ip": "192.168.1.250"
        }
        mock_connection.put.assert_called_once_with("config/dns/hosts/server.local", data=expected_data)
        
        assert result == {"success": True}

    def test_get_records_by_ip(self, local_dns, mock_connection, sample_config_response):
        """Test retrieval of domains by IP address."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.get_records_by_ip("192.168.1.101")
        
        expected = ["server2.local", "server2-alt.local"]
        assert sorted(result) == sorted(expected)

    def test_get_records_by_ip_not_found(self, local_dns, mock_connection, sample_config_response):
        """Test retrieval of domains for non-existent IP."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.get_records_by_ip("192.168.1.999")
        
        assert result == []

    def test_search_records_by_domain(self, local_dns, mock_connection, sample_config_response):
        """Test searching records by domain pattern."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.search_records("server")
        
        expected = {
            "A": {
                "server1.local": "192.168.1.100",
                "server2.local": "192.168.1.101",
                "server2-alt.local": "192.168.1.101"
            },
            "CNAME": {}
        }
        
        assert result == expected

    def test_search_records_case_insensitive(self, local_dns, mock_connection, sample_config_response):
        """Test case-insensitive domain search."""
        mock_connection.get.return_value = sample_config_response
        
        result = local_dns.search_records("LOCAL")
        
        # Should find all records since they all contain "local"
        assert len(result["A"]) == 6
        assert len(result["CNAME"]) == 4

    def test_export_records_json(self, local_dns, mock_connection, sample_config_response):
        """Test exporting records to JSON format."""
        mock_connection.get.return_value = sample_config_response
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            local_dns.export_records(tmp_filename, "json")
            
            # Verify file was created and contains correct data
            assert os.path.exists(tmp_filename)
            
            with open(tmp_filename, 'r') as f:
                exported_data = json.load(f)
            
            assert "A" in exported_data
            assert "CNAME" in exported_data
            assert len(exported_data["A"]) == 6
            assert len(exported_data["CNAME"]) == 4
            
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_export_records_csv(self, local_dns, mock_connection, sample_config_response):
        """Test exporting records to CSV format."""
        mock_connection.get.return_value = sample_config_response
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            local_dns.export_records(tmp_filename, "csv")
            
            # Verify file was created
            assert os.path.exists(tmp_filename)
            
            with open(tmp_filename, 'r') as f:
                content = f.read()
            
            # Verify CSV headers and some content
            assert "Domain,Type,Target,TTL" in content
            assert "server1.local,A,192.168.1.100," in content
            assert "www.local,CNAME,server1.local," in content
            
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_export_records_invalid_format(self, local_dns, mock_connection):
        """Test export with invalid format."""
        with pytest.raises(ValueError) as exc_info:
            local_dns.export_records("test.txt", "invalid_format")
        
        assert "Unsupported export format" in str(exc_info.value)

    def test_api_error_handling(self, local_dns, mock_connection):
        """Test handling of API errors."""
        mock_connection.get.side_effect = Exception("API connection failed")
        
        with pytest.raises(Exception) as exc_info:
            local_dns.get_all_records()
        
        assert "API connection failed" in str(exc_info.value)

    def test_malformed_config_response(self, local_dns, mock_connection):
        """Test handling of malformed configuration response."""
        # Missing dns config
        malformed_response = {"config": {}}
        mock_connection.get.return_value = malformed_response
        
        result = local_dns.get_all_records()
        
        # Should return empty records for malformed response
        assert result == {"A": {}, "CNAME": {}}

    def test_empty_dns_config(self, local_dns, mock_connection):
        """Test handling of empty DNS configuration."""
        empty_response = {
            "config": {
                "dns": {
                    "hosts": [],
                    "cnameRecords": []
                }
            }
        }
        mock_connection.get.return_value = empty_response
        
        result = local_dns.get_all_records()
        
        assert result == {"A": {}, "CNAME": {}}

    def test_partial_dns_config(self, local_dns, mock_connection):
        """Test handling of partial DNS configuration."""
        partial_response = {
            "config": {
                "dns": {
                    "hosts": ["192.168.1.100 server.local"]
                    # Missing cnameRecords
                }
            }
        }
        mock_connection.get.return_value = partial_response
        
        result = local_dns.get_all_records()
        
        expected = {
            "A": {"server.local": "192.168.1.100"},
            "CNAME": {}
        }
        
        assert result == expected

    def test_malformed_host_entries(self, local_dns, mock_connection):
        """Test handling of malformed host entries."""
        malformed_response = {
            "config": {
                "dns": {
                    "hosts": [
                        "192.168.1.100 server.local",  # Valid
                        "invalid_entry",  # Invalid - no IP
                        "",  # Empty entry
                        "192.168.1.101"  # Invalid - no hostname
                    ],
                    "cnameRecords": []
                }
            }
        }
        mock_connection.get.return_value = malformed_response
        
        result = local_dns.get_all_records()
        
        # Should only parse valid entries
        expected = {
            "A": {"server.local": "192.168.1.100"},
            "CNAME": {}
        }
        
        assert result == expected

    def test_malformed_cname_entries(self, local_dns, mock_connection):
        """Test handling of malformed CNAME entries."""
        malformed_response = {
            "config": {
                "dns": {
                    "hosts": [],
                    "cnameRecords": [
                        "www.local,server.local",  # Valid
                        "invalid_entry",  # Invalid - no comma
                        "",  # Empty entry
                        "alias.local,"  # Invalid - no target
                    ]
                }
            }
        }
        mock_connection.get.return_value = malformed_response
        
        result = local_dns.get_all_records()
        
        # Should only parse valid entries
        expected = {
            "A": {},
            "CNAME": {"www.local": "server.local"}
        }
        
        assert result == expected