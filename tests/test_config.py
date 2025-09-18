#!/usr/bin/env python3
"""
Test configuration loader for Pi-hole Docker tests.

This module loads test configuration from .env.test file and provides
easy access to test parameters throughout the test suite.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class TestConfig:
    """Centralized test configuration management."""
    
    def __init__(self, env_file: str = ".env.test"):
        """
        Initialize test configuration from environment file.
        
        :param env_file: Path to environment file (relative to tests directory)
        """
        self.config = {}
        self._load_env_file(env_file)
        self._set_defaults()
    
    def _load_env_file(self, env_file: str):
        """Load configuration from .env file."""
        env_path = Path(__file__).parent / env_file
        
        if not env_path.exists():
            print(f"Warning: Environment file {env_path} not found, using defaults")
            return
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            self.config[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Failed to load {env_path}: {e}")
    
    def _set_defaults(self):
        """Set default values for missing configuration."""
        defaults = {
            'PIHOLE_TEST_URL': 'http://localhost:42345',
            'PIHOLE_TEST_PASSWORD': 'test_password_123',
            'PIHOLE_TEST_CONTAINER_NAME': 'pihole-test',
            'PIHOLE_DOCKER_COMPOSE_FILE': 'docker-compose.test.yml',
            'PIHOLE_TEST_STARTUP_TIMEOUT': '60',
            'PIHOLE_TEST_HEALTH_CHECK_RETRIES': '12',
            'PIHOLE_TEST_HEALTH_CHECK_INTERVAL': '5',
            'TEST_DOMAIN_BASE': 'test.local',
            'TEST_IP_BASE': '192.168.99',
            'TEST_A_RECORD_IP_START': '100',
            'TEST_A_RECORD_IP_UPDATE': '101',
            'TEST_CNAME_RECORD_IP_START': '200',
            'TEST_EXPORT_RECORD_IP_START': '210',
            'TEST_BULK_RECORD_IP_START': '150',
            'TEST_STATS_RECORD_IP_START': '201',
            'TEST_WORKFLOW_RECORD_IP': '250',
            'PRELOAD_SERVER1_IP': '10',
            'PRELOAD_SERVER2_IP': '11',
            'PRELOAD_NAS_IP': '20',
            'BULK_RECORD_COUNT': '10',
            'PERFORMANCE_TIMEOUT': '30',
            'EXPORT_TEST_FORMATS': 'json,csv',
            'TEMP_EXPORT_DIR': '/tmp/pihole-test-exports',
            'DOCKER_NETWORK_NAME': 'pihole-test-network',
            'DOCKER_CLEANUP_ON_EXIT': 'true',
            'VERBOSE_OUTPUT': 'false',
            'PARALLEL_EXECUTION': 'false',
            'STOP_ON_FAILURE': 'false'
        }
        
        for key, default_value in defaults.items():
            if key not in self.config:
                self.config[key] = default_value
    
    def get(self, key: str, default: Any = None) -> str:
        """Get configuration value by key."""
        return self.config.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get configuration value as integer."""
        try:
            return int(self.config.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get configuration value as boolean."""
        value = self.config.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_list(self, key: str, delimiter: str = ',', default: list = None) -> list:
        """Get configuration value as list."""
        if default is None:
            default = []
        value = self.config.get(key, '')
        if not value:
            return default
        return [item.strip() for item in value.split(delimiter) if item.strip()]
    
    # Convenience properties for commonly used values
    @property
    def pihole_url(self) -> str:
        """Pi-hole test URL."""
        return self.get('PIHOLE_TEST_URL')
    
    @property
    def pihole_password(self) -> str:
        """Pi-hole test password."""
        return self.get('PIHOLE_TEST_PASSWORD')
    
    @property
    def container_name(self) -> str:
        """Docker container name."""
        return self.get('PIHOLE_TEST_CONTAINER_NAME')
    
    @property
    def compose_file(self) -> str:
        """Docker compose file path."""
        return self.get('PIHOLE_DOCKER_COMPOSE_FILE')
    
    @property
    def test_ip_base(self) -> str:
        """Base IP address for test records."""
        return self.get('TEST_IP_BASE')
    
    @property
    def test_domain_base(self) -> str:
        """Base domain for test records."""
        return self.get('TEST_DOMAIN_BASE')
    
    def get_test_ip(self, offset: int) -> str:
        """Get test IP address with offset from base."""
        return f"{self.test_ip_base}.{offset}"
    
    def get_test_domain(self, subdomain: str) -> str:
        """Get test domain with subdomain prefix."""
        return f"{subdomain}.{self.test_domain_base}"
    
    # Specific test data generators
    def get_a_record_test_ip(self) -> str:
        """Get IP for A record tests."""
        return self.get_test_ip(self.get_int('TEST_A_RECORD_IP_START'))
    
    def get_a_record_update_ip(self) -> str:
        """Get IP for A record update tests."""
        return self.get_test_ip(self.get_int('TEST_A_RECORD_IP_UPDATE'))
    
    def get_stats_test_ips(self) -> list:
        """Get IPs for statistics tests."""
        base_offset = self.get_int('TEST_STATS_RECORD_IP_START')
        return [
            self.get_test_ip(base_offset),     # 192.168.99.201
            self.get_test_ip(base_offset + 1), # 192.168.99.202  
            self.get_test_ip(base_offset)      # 192.168.99.201 (duplicate)
        ]
    
    def get_export_test_ips(self) -> list:
        """Get IPs for export tests."""
        base_offset = self.get_int('TEST_EXPORT_RECORD_IP_START')
        return [
            self.get_test_ip(base_offset),     # 192.168.99.210
            self.get_test_ip(base_offset + 1)  # 192.168.99.211
        ]
    
    def get_bulk_test_ips(self, count: Optional[int] = None) -> list:
        """Get IPs for bulk operation tests."""
        if count is None:
            count = self.get_int('BULK_RECORD_COUNT')
        base_offset = self.get_int('TEST_BULK_RECORD_IP_START')
        return [self.get_test_ip(base_offset + i) for i in range(count)]
    
    def get_workflow_test_ip(self) -> str:
        """Get IP for workflow tests."""
        return self.get_test_ip(self.get_int('TEST_WORKFLOW_RECORD_IP'))
    
    def get_preload_test_data(self) -> list:
        """Get pre-load test data for container setup."""
        return [
            (f"server1.{self.test_domain_base}", self.get_test_ip(self.get_int('PRELOAD_SERVER1_IP'))),
            (f"server2.{self.test_domain_base}", self.get_test_ip(self.get_int('PRELOAD_SERVER2_IP'))),
            (f"nas.{self.test_domain_base}", self.get_test_ip(self.get_int('PRELOAD_NAS_IP')))
        ]


# Global test configuration instance
test_config = TestConfig()


def get_test_config() -> TestConfig:
    """Get the global test configuration instance."""
    return test_config


# Convenience functions for backward compatibility
def get_pihole_url() -> str:
    """Get Pi-hole test URL."""
    return test_config.pihole_url


def get_pihole_password() -> str:
    """Get Pi-hole test password."""
    return test_config.pihole_password


def get_test_ip(offset: int) -> str:
    """Get test IP with offset."""
    return test_config.get_test_ip(offset)


def get_test_domain(subdomain: str) -> str:
    """Get test domain with subdomain."""
    return test_config.get_test_domain(subdomain)


if __name__ == "__main__":
    # Demo/test the configuration loader
    config = TestConfig()
    
    print("🔧 Test Configuration Loaded:")
    print(f"  Pi-hole URL: {config.pihole_url}")
    print(f"  Container: {config.container_name}")
    print(f"  IP Base: {config.test_ip_base}")
    print(f"  Domain Base: {config.test_domain_base}")
    print(f"  A Record Test IP: {config.get_a_record_test_ip()}")
    print(f"  Stats Test IPs: {config.get_stats_test_ips()}")
    print(f"  Bulk Test Count: {config.get_int('BULK_RECORD_COUNT')}")
    print(f"  Preload Data: {config.get_preload_test_data()}")