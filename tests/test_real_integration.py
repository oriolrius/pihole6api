"""
Comprehensive Docker-based tests for pihole6api library.

These tests run against a real Pi-hole Docker container and validate
all functionality end-to-end including authentication, DNS management,
and data persistence.
"""

import pytest
import os
import sys
import time
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load test environment configuration
load_dotenv(Path(__file__).parent / ".env.test")

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pihole6api import PiHole6Client
from tests.docker_test_manager import PiHoleDockerTestManager


class TestPiHoleDockerIntegration:
    """Comprehensive Docker-based integration tests."""
    
    @classmethod
    def setup_class(cls):
        """Setup Docker container before running tests."""
        cls.manager = PiHoleDockerTestManager()
        cls.base_url = os.getenv("PIHOLE_TEST_URL", "http://localhost:42345")
        cls.password = os.getenv("PIHOLE_TEST_PASSWORD", "test_password_123")
        
        # Get test configuration from environment
        cls.domain_base = os.getenv("TEST_DOMAIN_BASE", "test.local")
        cls.ip_base = os.getenv("TEST_IP_BASE", "192.168.99")
        
        print("\n🐳 Starting Pi-hole Docker container...")
        if not cls.manager.start_container():
            pytest.fail("Failed to start Pi-hole Docker container")
        
        print("⏳ Waiting for Pi-hole to be fully ready...")
        time.sleep(5)  # Give it extra time to initialize
        
        # Verify we can connect
        try:
            test_client = PiHole6Client(cls.base_url, cls.password)
            test_client.close_session()
            print("✅ Pi-hole is ready for testing!")
        except Exception as e:
            cls.manager.stop_container()
            pytest.fail(f"Pi-hole is not responding properly: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Cleanup Docker container after tests."""
        print("\n🧹 Cleaning up Docker container...")
        if hasattr(cls, 'manager'):
            cls.manager.stop_container()
    
    def test_01_authentication_and_connection(self):
        """Test that we can authenticate and establish a session."""
        print("\n🔐 Testing authentication...")
        
        # Test successful authentication
        client = PiHole6Client(self.base_url, self.password)
        assert client.connection.session_id is not None
        assert len(client.connection.session_id) > 0
        print(f"✅ Authentication successful, session ID: {client.connection.session_id[:8]}...")
        
        # Test that we can close the session
        result = client.close_session()
        print("✅ Session closed successfully")
        
        # Test authentication failure
        with pytest.raises(Exception):
            PiHole6Client(self.base_url, "wrong_password")
        print("✅ Authentication correctly rejects wrong password")
    
    def test_02_get_initial_dns_configuration(self):
        """Test retrieving the initial DNS configuration."""
        print("\n📋 Testing DNS configuration retrieval...")
        
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Get all DNS records
            records = client.local_dns.get_all_records()
            
            # Validate structure
            assert isinstance(records, dict)
            assert "A" in records
            assert "CNAME" in records
            assert isinstance(records["A"], dict)
            assert isinstance(records["CNAME"], dict)
            
            print(f"✅ Retrieved DNS config - A records: {len(records['A'])}, CNAME records: {len(records['CNAME'])}")
            
            # Test individual methods
            a_records = client.local_dns.get_a_records()
            cname_records = client.local_dns.get_cname_records()
            
            assert a_records == records["A"]
            assert cname_records == records["CNAME"]
            
            print("✅ Individual record type retrieval works correctly")
            
        finally:
            client.close_session()
    
    def test_03_add_and_verify_a_records(self):
        """Test adding A records and verifying they persist."""
        print("\n➕ Testing A record management...")
        
        client = PiHole6Client(self.base_url, self.password)
        test_domain = f"test-a-record.{self.domain_base}"
        test_ip = f"{self.ip_base}.{os.getenv('TEST_A_RECORD_IP_START', '100')}"
        
        try:
            # Get initial count
            initial_records = client.local_dns.get_a_records()
            initial_count = len(initial_records)
            print(f"Initial A record count: {initial_count}")
            
            # Add test record
            result = client.local_dns.add_a_record(test_domain, test_ip)
            print(f"Add A record result: {result}")
            
            # Verify record was added
            updated_records = client.local_dns.get_a_records()
            assert test_domain in updated_records
            assert updated_records[test_domain] == test_ip
            assert len(updated_records) == initial_count + 1
            
            print(f"✅ A record added successfully: {test_domain} -> {test_ip}")
            
            # Test updating the record
            new_ip = f"{self.ip_base}.{os.getenv('TEST_A_RECORD_IP_UPDATE', '101')}"
            update_result = client.local_dns.update_a_record(test_domain, new_ip)
            print(f"Update A record result: {update_result}")
            
            # Verify record was updated
            updated_records = client.local_dns.get_a_records()
            assert updated_records[test_domain] == new_ip
            
            print(f"✅ A record updated successfully: {test_domain} -> {new_ip}")
            
            # Test removing the record
            remove_result = client.local_dns.remove_a_record(test_domain)
            print(f"Remove A record result: {remove_result}")
            
            # Verify record was removed
            final_records = client.local_dns.get_a_records()
            assert test_domain not in final_records
            assert len(final_records) == initial_count
            
            print(f"✅ A record removed successfully")
            
        finally:
            # Cleanup
            try:
                client.local_dns.remove_a_record(test_domain)
            except:
                pass
            client.close_session()
    
    def test_04_add_and_verify_cname_records(self):
        """Test adding CNAME records and verifying they persist."""
        print("\n🔗 Testing CNAME record management...")
        
        client = PiHole6Client(self.base_url, self.password)
        test_alias = f"test-cname.{self.domain_base}"
        test_target = f"target.{self.domain_base}"
        
        try:
            # Get initial count
            initial_records = client.local_dns.get_cname_records()
            initial_count = len(initial_records)
            print(f"Initial CNAME record count: {initial_count}")
            
            # Add test CNAME record
            result = client.local_dns.add_cname_record(test_alias, test_target)
            print(f"Add CNAME record result: {result}")
            
            # Verify record was added
            updated_records = client.local_dns.get_cname_records()
            assert test_alias in updated_records
            assert updated_records[test_alias] == test_target
            assert len(updated_records) == initial_count + 1
            
            print(f"✅ CNAME record added successfully: {test_alias} -> {test_target}")
            
            # Test removing the record
            remove_result = client.local_dns.remove_cname_record(test_alias)
            print(f"Remove CNAME record result: {remove_result}")
            
            # Verify record was removed
            final_records = client.local_dns.get_cname_records()
            assert test_alias not in final_records
            assert len(final_records) == initial_count
            
            print(f"✅ CNAME record removed successfully")
            
        finally:
            # Cleanup
            try:
                client.local_dns.remove_cname_record(test_alias)
            except:
                pass
            client.close_session()
    
    def test_05_dns_statistics_and_search(self):
        """Test DNS statistics and search functionality."""
        print("\n📊 Testing DNS statistics and search...")
        
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Add some test data for statistics
            test_records = [
                (f"stats-test1.{self.domain_base}", f"{self.ip_base}.{os.getenv('TEST_STATS_IP_1', '201')}"),
                (f"stats-test2.{self.domain_base}", f"{self.ip_base}.{os.getenv('TEST_STATS_IP_2', '202')}"),
                (f"stats-test3.{self.domain_base}", f"{self.ip_base}.{os.getenv('TEST_STATS_IP_1', '201')}"),  # Same IP as test1
            ]
            
            for domain, ip in test_records:
                client.local_dns.add_a_record(domain, ip)
            
            # Test statistics
            stats = client.local_dns.get_statistics()
            print(f"DNS Statistics: {stats}")
            
            assert isinstance(stats, dict)
            assert "A" in stats
            assert "CNAME" in stats
            assert "unique_ips" in stats
            assert "domains_per_ip" in stats
            
            assert isinstance(stats["A"], int)
            assert isinstance(stats["CNAME"], int)
            assert isinstance(stats["unique_ips"], int)
            assert isinstance(stats["domains_per_ip"], dict)
            
            assert stats["A"] >= 3  # At least our test records
            assert stats["unique_ips"] >= 2  # At least our test IPs
            
            print("✅ Statistics calculation works correctly")
            
            # Test search functionality
            search_results = client.local_dns.search_records("stats-test")
            print(f"Search results for 'stats-test': {search_results}")
            
            assert isinstance(search_results, dict)
            assert "A" in search_results
            assert "CNAME" in search_results
            assert len(search_results["A"]) == 3  # Should find all our test records
            
            print("✅ Search functionality works correctly")
            
            # Test search by IP
            test_ip = f"{self.ip_base}.{os.getenv('TEST_STATS_IP_1', '201')}"
            ip_results = client.local_dns.get_records_by_ip(test_ip)
            print(f"Records for IP {test_ip}: {ip_results}")
            
            assert len(ip_results) == 2  # stats-test1 and stats-test3
            assert f"stats-test1.{self.domain_base}" in ip_results
            assert f"stats-test3.{self.domain_base}" in ip_results
            
            print("✅ Search by IP works correctly")
            
            # Cleanup test records
            for domain, _ in test_records:
                try:
                    client.local_dns.remove_a_record(domain)
                except:
                    pass
                    
        finally:
            client.close_session()
    
    def test_06_export_functionality(self):
        """Test DNS record export in different formats."""
        print("\n💾 Testing export functionality...")
        
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Add some test data for export
            test_records = [
                ("export-test1.local", "192.168.99.210"),
                ("export-test2.local", "192.168.99.211"),
            ]
            
            test_cnames = [
                ("export-cname1.local", "export-test1.local"),
                ("export-cname2.local", "export-test2.local"),
            ]
            
            for domain, ip in test_records:
                client.local_dns.add_a_record(domain, ip)
            
            for alias, target in test_cnames:
                client.local_dns.add_cname_record(alias, target)
            
            # Test JSON export
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
                json_file = tmp.name
            
            try:
                client.local_dns.export_records(json_file, "json")
                assert os.path.exists(json_file)
                assert os.path.getsize(json_file) > 0
                
                # Verify JSON content
                import json
                with open(json_file, 'r') as f:
                    exported_data = json.load(f)
                
                assert "A" in exported_data
                assert "CNAME" in exported_data
                
                # Check our test data is in the export
                for domain, ip in test_records:
                    assert domain in exported_data["A"]
                    assert exported_data["A"][domain] == ip
                
                print("✅ JSON export works correctly")
                
            finally:
                if os.path.exists(json_file):
                    os.unlink(json_file)
            
            # Test CSV export
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                csv_file = tmp.name
            
            try:
                client.local_dns.export_records(csv_file, "csv")
                assert os.path.exists(csv_file)
                assert os.path.getsize(csv_file) > 0
                
                # Verify CSV content
                with open(csv_file, 'r') as f:
                    csv_content = f.read()
                
                assert "Domain,Type,Target,TTL" in csv_content
                
                # Check our test data is in the export
                for domain, ip in test_records:
                    assert f"{domain},A,{ip}," in csv_content
                
                print("✅ CSV export works correctly")
                
            finally:
                if os.path.exists(csv_file):
                    os.unlink(csv_file)
            
            # Cleanup test records
            for domain, _ in test_records:
                try:
                    client.local_dns.remove_a_record(domain)
                except:
                    pass
            
            for alias, _ in test_cnames:
                try:
                    client.local_dns.remove_cname_record(alias)
                except:
                    pass
                    
        finally:
            client.close_session()
    
    def test_07_error_handling_and_validation(self):
        """Test error handling and input validation."""
        print("\n⚠️  Testing error handling...")
        
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Test invalid IP addresses
            invalid_ips = ["256.1.1.1", "not.an.ip", "192.168.1", ""]
            
            for invalid_ip in invalid_ips:
                with pytest.raises(ValueError):
                    client.local_dns.add_a_record(f"test.{self.domain_base}", invalid_ip)
            
            print("✅ IP validation works correctly")
            
            # Test invalid domain names
            invalid_domains = ["", " ", "test..local"]
            
            for invalid_domain in invalid_domains:
                with pytest.raises(ValueError):
                    client.local_dns.add_a_record(invalid_domain, "192.168.1.100")
            
            print("✅ Domain validation works correctly")
            
            # Test invalid export format
            with pytest.raises(ValueError):
                client.local_dns.export_records("test.txt", "invalid_format")
            
            print("✅ Export format validation works correctly")
            
        finally:
            client.close_session()
    
    def test_08_bulk_operations_performance(self):
        """Test bulk operations and performance."""
        print("\n🚀 Testing bulk operations...")
        
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Add multiple records quickly
            bulk_records = []
            bulk_count = int(os.getenv('TEST_BULK_COUNT', '10'))
            start_ip = int(os.getenv('TEST_BULK_IP_START', '150'))
            
            for i in range(bulk_count):
                domain = f"bulk-test-{i}.{self.domain_base}"
                ip = f"{self.ip_base}.{start_ip + i}"
                bulk_records.append((domain, ip))
            
            print(f"Adding {len(bulk_records)} records...")
            start_time = time.time()
            
            for domain, ip in bulk_records:
                client.local_dns.add_a_record(domain, ip)
            
            add_time = time.time() - start_time
            print(f"✅ Added {len(bulk_records)} records in {add_time:.2f} seconds")
            
            # Verify all records were added
            all_records = client.local_dns.get_a_records()
            for domain, ip in bulk_records:
                assert domain in all_records
                assert all_records[domain] == ip
            
            print("✅ All bulk records verified successfully")
            
            # Remove all records
            start_time = time.time()
            
            for domain, _ in bulk_records:
                client.local_dns.remove_a_record(domain)
            
            remove_time = time.time() - start_time
            print(f"✅ Removed {len(bulk_records)} records in {remove_time:.2f} seconds")
            
            # Verify all records were removed
            final_records = client.local_dns.get_a_records()
            for domain, _ in bulk_records:
                assert domain not in final_records
            
            print("✅ All bulk records removed successfully")
            
        finally:
            # Cleanup any remaining records
            for domain, _ in bulk_records:
                try:
                    client.local_dns.remove_a_record(domain)
                except:
                    pass
            client.close_session()
    
    def test_09_session_persistence_and_reuse(self):
        """Test session management and persistence."""
        print("\n🔄 Testing session management...")
        
        # Test that sessions work across multiple operations
        client = PiHole6Client(self.base_url, self.password)
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
            close_result = client.close_session()
            print(f"Session close result: {close_result}")
            
            print("✅ Session management works correctly")
            
        except Exception as e:
            print(f"Session test failed: {e}")
            try:
                client.close_session()
            except:
                pass
            raise
    
    def test_10_complete_workflow_validation(self):
        """Final test to validate the complete workflow works end-to-end."""
        print("\n🎯 Running complete workflow validation...")
        
        # This test validates the entire workflow from connection to cleanup
        client = PiHole6Client(self.base_url, self.password)
        
        try:
            # Step 1: Get initial state
            initial_records = client.local_dns.get_all_records()
            initial_a_count = len(initial_records["A"])
            initial_cname_count = len(initial_records["CNAME"])
            
            print(f"Initial state: {initial_a_count} A records, {initial_cname_count} CNAME records")
            
            # Step 2: Add test records
            test_domain = f"workflow-test.{self.domain_base}"
            test_ip = f"{self.ip_base}.{os.getenv('TEST_WORKFLOW_IP', '250')}"
            test_alias = f"workflow-alias.{self.domain_base}"
            
            client.local_dns.add_a_record(test_domain, test_ip)
            client.local_dns.add_cname_record(test_alias, test_domain)
            
            # Step 3: Verify additions
            updated_records = client.local_dns.get_all_records()
            assert len(updated_records["A"]) == initial_a_count + 1
            assert len(updated_records["CNAME"]) == initial_cname_count + 1
            assert updated_records["A"][test_domain] == test_ip
            assert updated_records["CNAME"][test_alias] == test_domain
            
            # Step 4: Test statistics
            stats = client.local_dns.get_statistics()
            assert stats["A"] == initial_a_count + 1
            assert stats["CNAME"] == initial_cname_count + 1
            
            # Step 5: Test search
            search_results = client.local_dns.search_records("workflow")
            assert len(search_results["A"]) == 1
            assert len(search_results["CNAME"]) == 1
            
            # Step 6: Clean up
            client.local_dns.remove_a_record(test_domain)
            client.local_dns.remove_cname_record(test_alias)
            
            # Step 7: Verify cleanup
            final_records = client.local_dns.get_all_records()
            assert len(final_records["A"]) == initial_a_count
            assert len(final_records["CNAME"]) == initial_cname_count
            assert test_domain not in final_records["A"]
            assert test_alias not in final_records["CNAME"]
            
            print("✅ Complete workflow validation successful!")
            
        finally:
            # Final cleanup
            try:
                client.local_dns.remove_a_record(test_domain)
                client.local_dns.remove_cname_record(test_alias)
            except:
                pass
            client.close_session()
            
        print("\n🎉 All Docker-based integration tests completed successfully!")