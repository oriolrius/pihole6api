"""
Validation and performance tests for pihole6api Docker integration.

Tests error handling, input validation, and bulk operations performance.
"""

import pytest
import os
import time
from pihole6api import PiHole6Client


class TestValidationPerformance:
    """Test input validation and performance operations."""

    def test_07_error_handling_and_validation(self, fresh_client, test_config):
        """Test error handling and input validation."""
        print("\n⚠️  Testing error handling...")
        
        domain_base = test_config['domain_base']
        
        try:
            # Test invalid IP addresses
            invalid_ips = ["256.1.1.1", "not.an.ip", "192.168.1", ""]
            
            for invalid_ip in invalid_ips:
                with pytest.raises(ValueError):
                    fresh_client.local_dns.add_a_record(f"test.{domain_base}", invalid_ip)
            
            print("✅ IP validation works correctly")
            
            # Test invalid domain names
            invalid_domains = ["", " ", "test..local"]
            
            for invalid_domain in invalid_domains:
                with pytest.raises(ValueError):
                    fresh_client.local_dns.add_a_record(invalid_domain, "192.168.1.1")
            
            print("✅ Domain validation works correctly")
            
            # Test invalid export formats
            with pytest.raises(ValueError):
                fresh_client.local_dns.export_records("/tmp/test.txt", format="invalid")
            
            print("✅ Export format validation works correctly")
            
        finally:
            fresh_client.close_session()

    def test_08_bulk_operations_performance(self, fresh_client, test_config):
        """Test bulk operations and performance."""
        print("\n🚀 Testing bulk operations...")
        
        domain_base = test_config['domain_base']
        ip_base = test_config['ip_base']
        bulk_count = int(os.getenv('TEST_BULK_COUNT', '10'))
        
        try:
            # Add multiple records quickly
            bulk_records = []
            for i in range(bulk_count):
                domain = f"bulk-test-{i}.{domain_base}"
                ip = f"{ip_base}.{int(os.getenv('TEST_BULK_IP_START', '150')) + i}"
                bulk_records.append((domain, ip))
            
            print(f"Adding {len(bulk_records)} records...")
            start_time = time.time()
            
            for domain, ip in bulk_records:
                fresh_client.local_dns.add_a_record(domain, ip)
            
            add_time = time.time() - start_time
            print(f"✅ Added {len(bulk_records)} records in {add_time:.2f} seconds")
            
            # Verify all records were added
            all_records = fresh_client.local_dns.get_a_records()
            for domain, ip in bulk_records:
                assert domain in all_records
                assert all_records[domain] == ip
            
            print("✅ All bulk records verified successfully")
            
            # Test bulk removal performance
            print(f"Removing {len(bulk_records)} records...")
            start_time = time.time()
            
            for domain, _ in bulk_records:
                fresh_client.local_dns.remove_a_record(domain)
            
            remove_time = time.time() - start_time
            print(f"✅ Removed {len(bulk_records)} records in {remove_time:.2f} seconds")
            
            # Verify all records were removed
            all_records = fresh_client.local_dns.get_a_records()
            for domain, _ in bulk_records:
                assert domain not in all_records
            
            print("✅ All bulk records removed successfully")
            
        finally:
            # Cleanup any remaining test records
            for i in range(bulk_count):
                try:
                    domain = f"bulk-test-{i}.{domain_base}"
                    fresh_client.local_dns.remove_a_record(domain)
                except:
                    pass
            fresh_client.close_session()