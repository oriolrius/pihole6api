import json
import urllib.parse
from typing import List, Dict, Optional

class PiHole6Configuration:
    def __init__(self, connection):
        """
        Handles Pi-hole configuration API endpoints.
        :param connection: Instance of PiHole6Connection for API requests.
        """
        self.connection = connection

    def export_settings(self):
        """
        Export Pi-hole settings via the Teleporter API.
        :return: Binary content of the exported settings archive.
        """
        return self.connection.get("teleporter", is_binary=True)

    def import_settings(self, file_path, import_options=None):
        """
        Import Pi-hole settings using a Teleporter archive.

        :param file_path: Path to the .tar.gz Teleporter file.
        :param import_options: Dictionary of import options (default: import everything).
        :return: API response.
        """
        with open(file_path, "rb") as file:
            files = {"file": (file_path, file, "application/gzip")}
            data = {"import": json.dumps(import_options)} if import_options else {}

            return self.connection.post("teleporter", files=files, data=data)

    def get_config(self, detailed=False):
        """
        Get the current configuration of Pi-hole.

        :param detailed: Boolean flag to get detailed configuration.
        :return: API response containing configuration data.
        """
        return self.connection.get("config", params={"detailed": str(detailed).lower()})

    def update_config(self, config_changes):
        """
        Modify the Pi-hole configuration.

        :param config_changes: Dictionary containing configuration updates.
        :return: API response confirming changes.
        """
        payload = {"config": config_changes}
        return self.connection.patch("config", data=payload)

    def get_config_section(self, element, detailed=False):
        """
        Get a specific part of the Pi-hole configuration.

        :param element: The section of the configuration to retrieve.
        :param detailed: Boolean flag for detailed output.
        :return: API response with the requested config section.
        """
        return self.connection.get(f"config/{element}", params={"detailed": str(detailed).lower()})

    def add_config_item(self, element, value):
        """
        Add an item to a configuration array.

        :param element: The config section to modify.
        :param value: The value to add.
        :return: API response confirming the addition.
        """
        return self.connection.put(f"config/{element}/{value}")

    def delete_config_item(self, element, value):
        """
        Delete an item from a configuration array.

        :param element: The config section to modify.
        :param value: The value to remove.
        :return: API response confirming the deletion.
        """
        return self.connection.delete(f"config/{element}/{value}")

    def add_local_a_record(self, host, ip):
        """
        Add a local A record to Pi-hole.

        :param host: The hostname (e.g., "foo.dev")
        :param ip: The IP address (e.g., "192.168.1.1")
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{ip} {host}")
        return self.connection.put(f"config/dns/hosts/{encoded_value}")

    def remove_local_a_record(self, host, ip):
        """
        Remove a local A record from Pi-hole.

        :param host: The hostname (e.g., "foo.dev")
        :param ip: The IP address (e.g., "192.168.1.1")
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{ip} {host}")
        return self.connection.delete(f"config/dns/hosts/{encoded_value}")

    def add_local_cname(self, host, target, ttl=300):
        """
        Add a local CNAME record to Pi-hole.

        :param host: The CNAME alias (e.g., "bar.xyz")
        :param target: The target hostname (e.g., "foo.dev")
        :param ttl: Time-to-live for the record (default: 300)
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{host},{target},{ttl}")
        return self.connection.put(f"config/dns/cnameRecords/{encoded_value}")

    def remove_local_cname(self, host, target, ttl=300):
        """
        Remove a local CNAME record from Pi-hole.

        :param host: The CNAME alias (e.g., "bar.xyz")
        :param target: The target hostname (e.g., "foo.dev")
        :param ttl: Time-to-live for the record (default: 300)
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{host},{target},{ttl}")
        return self.connection.delete(f"config/dns/cnameRecords/{encoded_value}")

    def get_local_dns_records(self, record_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve all local DNS records from Pi-hole configuration.
        
        :param record_type: Filter by record type ('A', 'CNAME', or None for all)
        :return: List of local DNS records
        """
        try:
            config_response = self.get_config()
            config_data = config_response.get("config", {})
            dns_config = config_data.get("dns", {})
            
            # Extract A records from hosts
            hosts = dns_config.get("hosts", [])
            cname_records = dns_config.get("cnameRecords", [])
            
            all_records = []
            
            # Process A records if requested or no filter
            if record_type is None or record_type.upper() == 'A':
                for host_entry in hosts:
                    parts = host_entry.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        hostnames = parts[1:]
                        for hostname in hostnames:
                            all_records.append({
                                "domain": hostname,
                                "ip": ip,
                                "type": "A",
                                "raw_entry": host_entry
                            })
            
            # Process CNAME records if requested or no filter
            if record_type is None or record_type.upper() == 'CNAME':
                for cname_entry in cname_records:
                    parts = cname_entry.split(",")
                    if len(parts) >= 2:
                        source = parts[0]
                        target = parts[1]
                        ttl = parts[2] if len(parts) > 2 else "default"
                        all_records.append({
                            "domain": source,
                            "target": target,
                            "type": "CNAME",
                            "ttl": ttl,
                            "raw_entry": cname_entry
                        })
            
            return all_records
            
        except Exception as e:
            raise Exception(f"Error retrieving local DNS records: {e}")

    def get_local_a_records(self) -> List[Dict]:
        """
        Retrieve only local A records from Pi-hole configuration.
        
        :return: List of A records
        """
        return self.get_local_dns_records(record_type='A')

    def get_local_cname_records(self) -> List[Dict]:
        """
        Retrieve only local CNAME records from Pi-hole configuration.
        
        :return: List of CNAME records
        """
        return self.get_local_dns_records(record_type='CNAME')

    def find_record_by_domain(self, domain: str) -> List[Dict]:
        """
        Find local DNS records for a specific domain.
        
        :param domain: Domain name to search for
        :return: List of matching records
        """
        all_records = self.get_local_dns_records()
        return [record for record in all_records if record.get('domain', '').lower() == domain.lower()]

    def get_dns_statistics(self) -> Dict:
        """
        Get statistics about local DNS records.
        
        :return: Dictionary with record counts and statistics
        """
        all_records = self.get_local_dns_records()
        
        a_records = [r for r in all_records if r.get('type') == 'A']
        cname_records = [r for r in all_records if r.get('type') == 'CNAME']
        
        # Get unique domains and IPs
        unique_domains = set()
        unique_ips = set()
        
        for record in a_records:
            unique_domains.add(record.get('domain', ''))
            unique_ips.add(record.get('ip', ''))
        
        for record in cname_records:
            unique_domains.add(record.get('domain', ''))
        
        return {
            "total_records": len(all_records),
            "a_records": len(a_records),
            "cname_records": len(cname_records),
            "unique_domains": len(unique_domains),
            "unique_ips": len(unique_ips),
            "records_by_type": {
                "A": len(a_records),
                "CNAME": len(cname_records)
            }
        }
