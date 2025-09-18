"""
Integration workflow tests for pihole6api Docker integration.

Tests end-to-end workflow validation and complete system integration.
"""

import pytest
import os
from pihole6api import PiHole6Client


class TestIntegrationWorkflow:
    """Test complete workflow and end-to-end integration."""

    def test_10_complete_workflow_validation(self, fresh_client, test_config):
        """Final test to validate the complete workflow works end-to-end."""
        print("\n🎯 Running complete workflow validation...")
        
        domain_base = test_config['domain_base']
        ip_base = test_config['ip_base']
        
        # This test validates the entire workflow from connection to cleanup
        try:
            # Step 1: Get initial state
            initial_records = fresh_client.local_dns.get_all_records()
            initial_a_count = len(initial_records["A"])
            initial_cname_count = len(initial_records["CNAME"])
            
            print(f"Initial state: {initial_a_count} A records, {initial_cname_count} CNAME records")
            
            # Step 2: Add test records
            test_domain = f"workflow-test.{domain_base}"
            test_ip = f"{ip_base}.{os.getenv('TEST_WORKFLOW_IP', '250')}"
            test_alias = f"workflow-alias.{domain_base}"
            
            fresh_client.local_dns.add_a_record(test_domain, test_ip)
            fresh_client.local_dns.add_cname_record(test_alias, test_domain)
            
            # Step 3: Verify additions
            updated_records = fresh_client.local_dns.get_all_records()
            assert len(updated_records["A"]) == initial_a_count + 1
            assert len(updated_records["CNAME"]) == initial_cname_count + 1
            assert updated_records["A"][test_domain] == test_ip
            assert updated_records["CNAME"][test_alias] == test_domain
            
            # Step 4: Test search functionality
            search_results = fresh_client.local_dns.search_records("workflow")
            assert len(search_results["A"]) >= 1
            assert len(search_results["CNAME"]) >= 1
            
            # Step 5: Test statistics
            stats = fresh_client.local_dns.get_statistics()
            assert stats["A"] >= initial_a_count + 1
            assert stats["CNAME"] >= initial_cname_count + 1
            
            # Step 6: Clean up
            fresh_client.local_dns.remove_cname_record(test_alias)
            fresh_client.local_dns.remove_a_record(test_domain)
            
            # Step 7: Verify cleanup
            final_records = fresh_client.local_dns.get_all_records()
            assert len(final_records["A"]) == initial_a_count
            assert len(final_records["CNAME"]) == initial_cname_count
            assert test_domain not in final_records["A"]
            assert test_alias not in final_records["CNAME"]
            
            print("✅ Complete workflow validation successful!")
            
        finally:
            # Cleanup any remaining test records
            try:
                fresh_client.local_dns.remove_cname_record(f"workflow-alias.{domain_base}")
            except:
                pass
            try:
                fresh_client.local_dns.remove_a_record(f"workflow-test.{domain_base}")
            except:
                pass
            fresh_client.close_session()