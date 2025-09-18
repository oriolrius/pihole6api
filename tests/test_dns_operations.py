"""
DNS operations tests for pihole6api Docker integration.

Tests statistics, search functionality, and export capabilities.
"""

import pytest
import os
import tempfile
from pathlib import Path
from pihole6api import PiHole6Client


class TestDnsOperations:
    """Test DNS statistics, search, and export operations."""

    def test_05_dns_statistics_and_search(self, fresh_client, test_config):
        """Test DNS statistics and search functionality."""
        print("\n📊 Testing DNS statistics and search...")
        
        domain_base = test_config['domain_base']
        ip_base = test_config['ip_base']
        
        try:
            # Add some test data for statistics
            test_records = [
                (f"stats-test1.{domain_base}", f"{ip_base}.{os.getenv('TEST_STATS_IP_1', '201')}"),
                (f"stats-test2.{domain_base}", f"{ip_base}.{os.getenv('TEST_STATS_IP_2', '202')}"),
                (f"stats-test3.{domain_base}", f"{ip_base}.{os.getenv('TEST_STATS_IP_1', '201')}"),  # Same IP as test1
            ]
            
            for domain, ip in test_records:
                fresh_client.local_dns.add_a_record(domain, ip)
            
            # Test statistics
            stats = fresh_client.local_dns.get_statistics()
            print(f"DNS Statistics: {stats}")
            
            assert isinstance(stats, dict)
            assert "A" in stats
            assert "CNAME" in stats
            assert "unique_ips" in stats
            assert "domains_per_ip" in stats
            
            # Should have at least our test records
            assert stats["A"] >= 3
            assert stats["unique_ips"] >= 2
            
            print("✅ Statistics calculation works correctly")
            
            # Test search functionality
            search_results = fresh_client.local_dns.search_records("stats-test")
            print(f"Search results for 'stats-test': {search_results}")
            
            assert isinstance(search_results, dict)
            assert "A" in search_results
            assert "CNAME" in search_results
            assert len(search_results["A"]) == 3  # Should find all our test records
            
            print("✅ Search functionality works correctly")
            
            # Test search by IP
            test_ip = f"{ip_base}.{os.getenv('TEST_STATS_IP_1', '201')}"
            ip_results = fresh_client.local_dns.get_records_by_ip(test_ip)
            print(f"Records for IP {test_ip}: {ip_results}")
            
            assert len(ip_results) == 2  # stats-test1 and stats-test3
            assert f"stats-test1.{domain_base}" in ip_results
            assert f"stats-test3.{domain_base}" in ip_results
            
            print("✅ Search by IP works correctly")
            
            # Cleanup test records
            for domain, _ in test_records:
                try:
                    fresh_client.local_dns.remove_a_record(domain)
                except:
                    pass
            
        finally:
            # Cleanup
            for domain, _ in [
                (f"stats-test1.{domain_base}", ""),
                (f"stats-test2.{domain_base}", ""),
                (f"stats-test3.{domain_base}", ""),
            ]:
                try:
                    fresh_client.local_dns.remove_a_record(domain)
                except:
                    pass
            fresh_client.close_session()

    def test_06_export_functionality(self, fresh_client, test_config):
        """Test export functionality for DNS records."""
        print("\n💾 Testing export functionality...")
        
        domain_base = test_config['domain_base']
        ip_base = test_config['ip_base']
        
        try:
            # Add test records for export
            test_records = [
                (f"export-test1.{domain_base}", f"{ip_base}.210"),
                (f"export-test2.{domain_base}", f"{ip_base}.211"),
            ]
            
            for domain, ip in test_records:
                fresh_client.local_dns.add_a_record(domain, ip)
            
            # Test JSON export
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as f:
                json_path = f.name
            
            try:
                fresh_client.local_dns.export_records(json_path, format='json')
                
                # Verify file exists and has content
                assert Path(json_path).exists()
                assert Path(json_path).stat().st_size > 0
                
                print("✅ JSON export works correctly")
                
            finally:
                try:
                    Path(json_path).unlink()
                except:
                    pass
            
            # Test CSV export
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as f:
                csv_path = f.name
            
            try:
                fresh_client.local_dns.export_records(csv_path, format='csv')
                
                # Verify file exists and has content
                assert Path(csv_path).exists()
                assert Path(csv_path).stat().st_size > 0
                
                print("✅ CSV export works correctly")
                
            finally:
                try:
                    Path(csv_path).unlink()
                except:
                    pass
            
            # Cleanup test records
            for domain, _ in test_records:
                try:
                    fresh_client.local_dns.remove_a_record(domain)
                except:
                    pass
            
        finally:
            # Cleanup
            for domain, _ in [
                (f"export-test1.{domain_base}", ""),
                (f"export-test2.{domain_base}", ""),
            ]:
                try:
                    fresh_client.local_dns.remove_a_record(domain)
                except:
                    pass
            fresh_client.close_session()