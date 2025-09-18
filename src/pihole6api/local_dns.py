import urllib.parse
from typing import List, Dict, Optional

class PiHole6LocalDNS:
    def __init__(self, connection):
        """
        Handles Pi-hole local DNS records API endpoints.
        :param connection: Instance of PiHole6Connection for API requests.
        """
        self.connection = connection

    def get_all_records(self, record_type: Optional[str] = None) -> List[Dict]:
        """
        Retrieve all local DNS records from Pi-hole configuration.
        
        :param record_type: Filter by record type ('A', 'CNAME', or None for all)
        :return: List of local DNS records
        """
        try:
            config_response = self.connection.get("config")
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

    def get_a_records(self) -> List[Dict]:
        """
        Retrieve only local A records from Pi-hole configuration.
        
        :return: List of A records
        """
        return self.get_all_records(record_type='A')

    def get_cname_records(self) -> List[Dict]:
        """
        Retrieve only local CNAME records from Pi-hole configuration.
        
        :return: List of CNAME records
        """
        return self.get_all_records(record_type='CNAME')

    def find_by_domain(self, domain: str) -> List[Dict]:
        """
        Find local DNS records for a specific domain.
        
        :param domain: Domain name to search for
        :return: List of matching records
        """
        all_records = self.get_all_records()
        return [record for record in all_records if record.get('domain', '').lower() == domain.lower()]

    def find_by_ip(self, ip: str) -> List[Dict]:
        """
        Find A records that point to a specific IP address.
        
        :param ip: IP address to search for
        :return: List of matching A records
        """
        a_records = self.get_a_records()
        return [record for record in a_records if record.get('ip', '') == ip]

    def add_a_record(self, hostname: str, ip: str):
        """
        Add a local A record to Pi-hole.

        :param hostname: The hostname (e.g., "foo.dev")
        :param ip: The IP address (e.g., "192.168.1.1")
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{ip} {hostname}")
        return self.connection.put(f"config/dns/hosts/{encoded_value}")

    def remove_a_record(self, hostname: str, ip: str):
        """
        Remove a local A record from Pi-hole.

        :param hostname: The hostname (e.g., "foo.dev")
        :param ip: The IP address (e.g., "192.168.1.1")
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{ip} {hostname}")
        return self.connection.delete(f"config/dns/hosts/{encoded_value}")

    def add_cname_record(self, alias: str, target: str, ttl: int = 300):
        """
        Add a local CNAME record to Pi-hole.

        :param alias: The CNAME alias (e.g., "bar.xyz")
        :param target: The target hostname (e.g., "foo.dev")
        :param ttl: Time-to-live for the record (default: 300)
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{alias},{target},{ttl}")
        return self.connection.put(f"config/dns/cnameRecords/{encoded_value}")

    def remove_cname_record(self, alias: str, target: str, ttl: int = 300):
        """
        Remove a local CNAME record from Pi-hole.

        :param alias: The CNAME alias (e.g., "bar.xyz")
        :param target: The target hostname (e.g., "foo.dev")
        :param ttl: Time-to-live for the record (default: 300)
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{alias},{target},{ttl}")
        return self.connection.delete(f"config/dns/cnameRecords/{encoded_value}")

    def get_statistics(self) -> Dict:
        """
        Get statistics about local DNS records.
        
        :return: Dictionary with record counts and statistics
        """
        all_records = self.get_all_records()
        
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

    def export_records(self, format: str = "dict") -> Dict:
        """
        Export all local DNS records in various formats.
        
        :param format: Export format ("dict", "hosts", "zone")
        :return: Records in requested format
        """
        records = self.get_all_records()
        
        if format == "dict":
            return {"records": records}
        
        elif format == "hosts":
            # Export in /etc/hosts format
            hosts_lines = []
            for record in records:
                if record.get('type') == 'A':
                    hosts_lines.append(f"{record['ip']}\t{record['domain']}")
            return {"hosts_format": "\n".join(hosts_lines)}
        
        elif format == "zone":
            # Export in DNS zone file format
            zone_lines = []
            for record in records:
                if record.get('type') == 'A':
                    zone_lines.append(f"{record['domain']}.\tIN\tA\t{record['ip']}")
                elif record.get('type') == 'CNAME':
                    ttl = record.get('ttl', '300')
                    zone_lines.append(f"{record['domain']}.\t{ttl}\tIN\tCNAME\t{record['target']}.")
            return {"zone_format": "\n".join(zone_lines)}
        
        else:
            raise ValueError(f"Unsupported export format: {format}")