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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PiHoleDockerTestManager:
    """Manages Pi-hole Docker container for testing."""
    
    def __init__(self, compose_file="docker-compose.test.yml"):
        self.compose_file = Path(__file__).parent / compose_file
        self.container_name = "pihole-test"
        self.test_url = "http://localhost:42345"
        self.test_password = "test_password_123"
        self.startup_timeout = 60
        self.health_check_retries = 12
        self.health_check_interval = 5
    
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
                
                # Check if Pi-hole API is responding
                response = requests.get(f"{self.test_url}/admin/api.php", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Pi-hole is ready! (attempt {attempt + 1})")
                    return True
                    
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
            
            # Create client and add some test DNS records
            client = PiHole6Client(self.test_url, self.test_password)
            
            # Add test A records
            test_records = [
                ("server1.test.local", "192.168.99.10"),
                ("server2.test.local", "192.168.99.11"),
                ("nas.test.local", "192.168.99.20"),
            ]
            
            for domain, ip in test_records:
                try:
                    result = client.local_dns.add_a_record(domain, ip)
                    logger.info(f"Added test record: {domain} -> {ip}")
                except Exception as e:
                    logger.warning(f"Failed to add test record {domain}: {e}")
            
            # Add test CNAME records
            cname_records = [
                ("www.test.local", "server1.test.local"),
                ("api.test.local", "server2.test.local"),
            ]
            
            for alias, target in cname_records:
                try:
                    result = client.local_dns.add_cname_record(alias, target)
                    logger.info(f"Added test CNAME: {alias} -> {target}")
                except Exception as e:
                    logger.warning(f"Failed to add test CNAME {alias}: {e}")
            
            client.close_session()
            logger.info("Test data setup complete")
            return True
            
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