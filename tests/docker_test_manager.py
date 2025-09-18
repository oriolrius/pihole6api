#!/usr/bin/env python3
"""
Docker test manager for Pi-hole integration tests.

This script manages the lifecycle of Docker containers for testing.
"""

import subprocess
import time
import requests
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load test environment configuration
load_dotenv(Path(__file__).parent / ".env.test")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PiHoleDockerTestManager:
    """Manages Pi-hole Docker container for testing."""
    
    def __init__(self, compose_file=None):
        # Load configuration from environment with fallbacks
        compose_file = compose_file or os.getenv("PIHOLE_DOCKER_COMPOSE_FILE", "docker-compose.test.yml")
        self.compose_file = Path(__file__).parent / compose_file
        self.container_name = os.getenv("PIHOLE_TEST_CONTAINER_NAME", "pihole-test")
        self.test_url = os.getenv("PIHOLE_TEST_URL", "http://localhost:42345")
        self.test_password = os.getenv("PIHOLE_TEST_PASSWORD", "test_password_123")
        self.startup_timeout = int(os.getenv("PIHOLE_TEST_STARTUP_TIMEOUT", "60"))
        self.health_check_retries = int(os.getenv("PIHOLE_TEST_HEALTH_CHECK_RETRIES", "12"))
        self.health_check_interval = int(os.getenv("PIHOLE_TEST_HEALTH_CHECK_INTERVAL", "5"))
    
    def start_container(self):
        """Start the Pi-hole test container."""
        logger.info("Starting Pi-hole test container...")
        
        try:
            # Stop any existing container first
            self.stop_container(silent=True)
            
            # Start the container
            cmd = ["docker", "compose", "-f", str(self.compose_file), "up", "-d"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Container started successfully")
            
            # Wait for container to be healthy
            if self.wait_for_healthy():
                logger.info("Pi-hole is ready for testing!")
                return True
            else:
                logger.error("Pi-hole failed to become healthy")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start container: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            return False
    
    def stop_container(self, silent=False):
        """Stop and remove the Pi-hole test container."""
        if not silent:
            logger.info("Stopping Pi-hole test container...")
        
        try:
            # Stop and remove containers
            cmd = ["docker", "compose", "-f", str(self.compose_file), "down", "-v"]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if not silent:
                logger.info("Container stopped and removed")
            return True
            
        except subprocess.CalledProcessError as e:
            if not silent:
                logger.error(f"Failed to stop container: {e}")
            return False
    
    def wait_for_healthy(self):
        """Wait for Pi-hole to become healthy and ready."""
        logger.info("Waiting for Pi-hole to become ready...")
        
        for attempt in range(self.health_check_retries):
            try:
                # Check if container is running
                if not self.is_container_running():
                    logger.warning(f"Container not running on attempt {attempt + 1}")
                    time.sleep(self.health_check_interval)
                    continue
                
                # Check if Pi-hole web interface is responding
                response = requests.get(f"{self.test_url}/admin", timeout=10)
                if response.status_code not in [200, 308]:  # 308 is redirect to /admin/
                    logger.debug(f"Web interface not ready: {response.status_code}")
                    time.sleep(self.health_check_interval)
                    continue
                
                # Try to authenticate to verify API is fully functional
                auth_response = requests.post(
                    f"{self.test_url}/api/auth",
                    json={"password": self.test_password},
                    timeout=10
                )
                
                if auth_response.status_code == 200:
                    auth_data = auth_response.json()
                    if "session" in auth_data and "sid" in auth_data["session"]:
                        logger.info(f"Pi-hole is fully ready! (attempt {attempt + 1})")
                        return True
                    else:
                        logger.debug(f"Authentication response malformed: {auth_data}")
                else:
                    logger.debug(f"Authentication failed: {auth_response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.debug(f"Health check failed on attempt {attempt + 1}: {e}")
            
            if attempt < self.health_check_retries - 1:
                logger.info(f"Attempt {attempt + 1} failed, retrying in {self.health_check_interval}s...")
                time.sleep(self.health_check_interval)
        
        logger.error("Pi-hole failed to become ready within timeout")
        return False
    
    def is_container_running(self):
        """Check if the Pi-hole container is running."""
        try:
            cmd = ["docker", "ps", "--filter", f"name={self.container_name}", "--format", "{{.Names}}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return self.container_name in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def get_container_logs(self):
        """Get logs from the Pi-hole container."""
        try:
            cmd = ["docker", "compose", "-f", str(self.compose_file), "logs", self.container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Failed to get logs: {e}"
    
    def setup_test_data(self):
        """Setup initial test data in Pi-hole."""
        logger.info("Setting up test data...")
        
        try:
            # Import the library to setup test DNS records
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            from pihole6api import PiHole6Client
            
            # Create client and verify it works
            client = PiHole6Client(self.test_url, self.test_password)
            
            # Test that we can get current configuration
            try:
                current_records = client.local_dns.get_all_records()
                logger.info(f"Successfully connected! Current A records: {len(current_records.get('A', {}))}, CNAME records: {len(current_records.get('CNAME', {}))}")
            except Exception as e:
                logger.error(f"Failed to get current DNS records: {e}")
                client.close_session()
                return False
            
            # Get configuration from environment
            domain_base = os.getenv("TEST_DOMAIN_BASE", "test.local")
            ip_base = os.getenv("TEST_IP_BASE", "192.168.99")
            
            # Add test A records using environment configuration
            test_records = [
                (f"server1.{domain_base}", f"{ip_base}.{os.getenv('PRELOAD_SERVER1_IP', '10')}"),
                (f"server2.{domain_base}", f"{ip_base}.{os.getenv('PRELOAD_SERVER2_IP', '11')}"),
                (f"nas.{domain_base}", f"{ip_base}.{os.getenv('PRELOAD_NAS_IP', '20')}"),
            ]
            
            for domain, ip in test_records:
                try:
                    result = client.local_dns.add_a_record(domain, ip)
                    logger.info(f"Added test A record: {domain} -> {ip}")
                except Exception as e:
                    logger.warning(f"Failed to add test A record {domain}: {e}")
            
            # Add test CNAME records using environment configuration
            cname_records = [
                (f"www.{domain_base}", f"server1.{domain_base}"),
                (f"api.{domain_base}", f"server2.{domain_base}"),
            ]
            
            for alias, target in cname_records:
                try:
                    result = client.local_dns.add_cname_record(alias, target)
                    logger.info(f"Added test CNAME: {alias} -> {target}")
                except Exception as e:
                    logger.warning(f"Failed to add test CNAME {alias}: {e}")
            
            # Verify test data was added
            try:
                final_records = client.local_dns.get_all_records()
                a_count = len(final_records.get('A', {}))
                cname_count = len(final_records.get('CNAME', {}))
                logger.info(f"Test data setup complete. Total A records: {a_count}, CNAME records: {cname_count}")
                
                client.close_session()
                return True
                
            except Exception as e:
                logger.error(f"Failed to verify test data: {e}")
                client.close_session()
                return False
            
        except Exception as e:
            logger.error(f"Failed to setup test data: {e}")
            return False


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage Pi-hole Docker test container")
    parser.add_argument("action", choices=["start", "stop", "restart", "logs", "setup-data"])
    parser.add_argument("--wait", action="store_true", help="Wait for container to be ready")
    
    args = parser.parse_args()
    
    manager = PiHoleDockerTestManager()
    
    if args.action == "start":
        if manager.start_container():
            if args.wait:
                manager.setup_test_data()
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.action == "stop":
        if manager.stop_container():
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.action == "restart":
        manager.stop_container()
        if manager.start_container():
            if args.wait:
                manager.setup_test_data()
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.action == "logs":
        print(manager.get_container_logs())
    
    elif args.action == "setup-data":
        if manager.setup_test_data():
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()