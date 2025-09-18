"""
DNS record management tests for pihole6api Docker integration.

Tests A record and CNAME record CRUD operations.
"""

import pytest
import os
from pihole6api import PiHole6Client


class TestDnsRecords:
    """Test DNS record CRUD operations."""

    def test_03_add_and_verify_a_records(self, fresh_client, test_config):
        """Test adding A records and verifying they persist."""
        print("\n➕ Testing A record management...")
        
        domain_base = test_config['domain_base']
        ip_base = test_config['ip_base']
        test_domain = f"test-a-record.{domain_base}"
        test_ip = f"{ip_base}.{os.getenv('TEST_A_RECORD_IP_START', '100')}"
        
        try:
            # Get initial count
            initial_records = fresh_client.local_dns.get_a_records()
            initial_count = len(initial_records)
            print(f"Initial A record count: {initial_count}")
            
            # Add test record
            result = fresh_client.local_dns.add_a_record(test_domain, test_ip)
            print(f"Add A record result: {result}")
            
            # Verify record was added
            updated_records = fresh_client.local_dns.get_a_records()
            assert test_domain in updated_records
            assert updated_records[test_domain] == test_ip
            assert len(updated_records) == initial_count + 1
            
            print(f"✅ A record added successfully: {test_domain} -> {test_ip}")
            
            # Test updating the record
            new_ip = f"{ip_base}.{os.getenv('TEST_A_RECORD_IP_UPDATE', '101')}"
            update_result = fresh_client.local_dns.update_a_record(test_domain, new_ip)
            print(f"Update A record result: {update_result}")
            
            # Verify record was updated
            updated_records = fresh_client.local_dns.get_a_records()
            assert updated_records[test_domain] == new_ip
            
            print(f"✅ A record updated successfully: {test_domain} -> {new_ip}")
            
            # Test removing the record
            remove_result = fresh_client.local_dns.remove_a_record(test_domain)
            print(f"Remove A record result: {remove_result}")
            
            # Verify record was removed
            final_records = fresh_client.local_dns.get_a_records()
            assert test_domain not in final_records
            assert len(final_records) == initial_count
            
            print(f"✅ A record removed successfully")
            
        finally:
            # Cleanup
            try:
                fresh_client.local_dns.remove_a_record(test_domain)
            except:
                pass
            fresh_client.close_session()

    def test_04_add_and_verify_cname_records(self, fresh_client, test_config):
        """Test adding CNAME records and verifying they persist."""
        print("\n🔗 Testing CNAME record management...")
        
        domain_base = test_config['domain_base']
        test_alias = f"test-cname.{domain_base}"
        test_target = f"target.{domain_base}"
        
        try:
            # Get initial count
            initial_records = fresh_client.local_dns.get_cname_records()
            initial_count = len(initial_records)
            print(f"Initial CNAME record count: {initial_count}")
            
            # Add test CNAME record
            result = fresh_client.local_dns.add_cname_record(test_alias, test_target)
            print(f"Add CNAME record result: {result}")
            
            # Verify record was added
            updated_records = fresh_client.local_dns.get_cname_records()
            assert test_alias in updated_records
            assert updated_records[test_alias] == test_target
            assert len(updated_records) == initial_count + 1
            
            print(f"✅ CNAME record added successfully: {test_alias} -> {test_target}")
            
            # Test removing the record
            remove_result = fresh_client.local_dns.remove_cname_record(test_alias)
            print(f"Remove CNAME record result: {remove_result}")
            
            # Verify record was removed
            final_records = fresh_client.local_dns.get_cname_records()
            assert test_alias not in final_records
            assert len(final_records) == initial_count
            
            print(f"✅ CNAME record removed successfully")
            
        finally:
            # Cleanup
            try:
                fresh_client.local_dns.remove_cname_record(test_alias)
            except:
                pass
            fresh_client.close_session()