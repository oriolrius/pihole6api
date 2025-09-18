import urllib.parse
from typing import List, Dict, Optional

class PiHole6LocalDNS:
    def __init__(self, connection):
        """
        Handles Pi-hole local DNS records API endpoints.
        :param connection: Instance of PiHole6Connection for API requests.
        """
        self.connection = connection

    def get_all_records(self, record_type: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Retrieve all local DNS records from Pi-hole configuration.
        
        :param record_type: Filter by record type ('A', 'CNAME', or None for all)
        :return: Dictionary with 'A' and 'CNAME' keys containing domain -> target mappings
        """
        try:
            config_response = self.connection.get("config")
            config_data = config_response.get("config", {})
            dns_config = config_data.get("dns", {})
            
            result = {"A": {}, "CNAME": {}}
            
            # Extract A records from hosts
            hosts = dns_config.get("hosts", [])
            
            # Process A records if requested or no filter
            if record_type is None or record_type.upper() == 'A':
                for host_entry in hosts:
                    parts = host_entry.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        hostnames = parts[1:]
                        for hostname in hostnames:
                            result["A"][hostname] = ip
            
            # Extract CNAME records 
            cname_records = dns_config.get("cnameRecords", [])
            
            # Process CNAME records if requested or no filter
            if record_type is None or record_type.upper() == 'CNAME':
                for cname_entry in cname_records:
                    parts = cname_entry.split(",")
                    if len(parts) >= 2:
                        source = parts[0]
                        target = parts[1]
                        result["CNAME"][source] = target
            
            return result
            
        except Exception as e:
            print(f"Error retrieving DNS records: {e}")
            return {"A": {}, "CNAME": {}}

    def get_a_records(self) -> Dict[str, str]:
        """
        Retrieve only local A records from Pi-hole configuration.
        
        :return: Dictionary of domain -> IP mappings
        """
        all_records = self.get_all_records()
        return all_records["A"]

    def get_cname_records(self) -> Dict[str, str]:
        """
        Retrieve only local CNAME records from Pi-hole configuration.
        
        :return: Dictionary of alias -> target mappings
        """
        all_records = self.get_all_records()
        return all_records["CNAME"]

    def add_a_record(self, hostname: str, ip: str):
        """
        Add a local A record to Pi-hole.

        :param hostname: The hostname (e.g., "foo.dev")
        :param ip: The IP address (e.g., "192.168.1.1")
        :return: API response
        """
        encoded_value = urllib.parse.quote(f"{ip} {hostname}")
        return self.connection.put(f"config/dns/hosts/{encoded_value}")

    def remove_a_record(self, hostname: str, ip: str = None):
        """
        Remove a local A record from Pi-hole.

        :param hostname: The hostname (e.g., "foo.dev")
        :param ip: The IP address (e.g., "192.168.1.1") - if None, find existing IP
        :return: API response
        """
        if ip is None:
            # Find the existing IP for this hostname
            a_records = self.get_a_records()
            if hostname not in a_records:
                raise ValueError(f"Hostname {hostname} not found in A records")
            ip = a_records[hostname]
        
        encoded_value = urllib.parse.quote(f"{ip} {hostname}")
        return self.connection.delete(f"config/dns/hosts/{encoded_value}")

    def update_a_record(self, hostname: str, new_ip: str):
        """
        Update an existing A record with a new IP address.
        
        :param hostname: The hostname to update
        :param new_ip: The new IP address
        :return: API response
        """
        # First remove the old record
        try:
            self.remove_a_record(hostname)
        except:
            pass  # Ignore if record doesn't exist
        
        # Add the new record
        return self.add_a_record(hostname, new_ip)

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

    def remove_cname_record(self, alias: str, target: str = None, ttl: int = 300):
        """
        Remove a local CNAME record from Pi-hole.

        :param alias: The CNAME alias (e.g., "bar.xyz")
        :param target: The target hostname (e.g., "foo.dev") - if None, find existing target
        :param ttl: Time-to-live for the record (default: 300)
        :return: API response
        """
        if target is None:
            # Find the existing target for this alias
            cname_records = self.get_cname_records()
            if alias not in cname_records:
                raise ValueError(f"CNAME alias {alias} not found")
            target = cname_records[alias]
        
        encoded_value = urllib.parse.quote(f"{alias},{target},{ttl}")
        return self.connection.delete(f"config/dns/cnameRecords/{encoded_value}")

    def get_statistics(self) -> Dict:
        """
        Get statistics about local DNS records.
        
        :return: Dictionary with record counts and statistics
        """
        all_records = self.get_all_records()
        a_records = all_records["A"]
        cname_records = all_records["CNAME"]
        
        # Get unique IPs and domains per IP
        unique_ips = set(a_records.values())
        domains_per_ip = {}
        for domain, ip in a_records.items():
            if ip not in domains_per_ip:
                domains_per_ip[ip] = []
            domains_per_ip[ip].append(domain)
        
        return {
            "A": len(a_records),
            "CNAME": len(cname_records),
            "unique_ips": len(unique_ips),
            "domains_per_ip": domains_per_ip
        }

    def search_records(self, query: str) -> Dict[str, Dict[str, str]]:
        """
        Search for DNS records matching a query string.
        
        :param query: Search query to match against domain names
        :return: Dictionary with matching records
        """
        all_records = self.get_all_records()
        query_lower = query.lower()
        
        matching_a = {domain: ip for domain, ip in all_records["A"].items() 
                      if query_lower in domain.lower()}
        matching_cname = {alias: target for alias, target in all_records["CNAME"].items() 
                          if query_lower in alias.lower()}
        
        return {"A": matching_a, "CNAME": matching_cname}

    def get_records_by_ip(self, ip: str) -> List[str]:
        """
        Get all domain names that point to a specific IP address.
        
        :param ip: IP address to search for
        :return: List of domain names pointing to this IP
        """
        a_records = self.get_a_records()
        return [domain for domain, record_ip in a_records.items() if record_ip == ip]

    def export_records(self, filename: str, format: str = "json"):
        """
        Export DNS records to a file in specified format.
        
        :param filename: Output filename
        :param format: Export format ("json" or "csv")
        """
        all_records = self.get_all_records()
        
        if format.lower() == "json":
            import json
            with open(filename, 'w') as f:
                json.dump(all_records, f, indent=2)
        elif format.lower() == "csv":
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Domain", "Type", "Target", "TTL"])
                
                # Write A records
                for domain, ip in all_records["A"].items():
                    writer.writerow([domain, "A", ip, ""])
                
                # Write CNAME records
                for alias, target in all_records["CNAME"].items():
                    writer.writerow([alias, "CNAME", target, "300"])
        else:
            raise ValueError(f"Unsupported format: {format}")

    def add_a_record_with_validation(self, hostname: str, ip: str):
        """
        Add an A record with input validation.
        
        :param hostname: Domain name
        :param ip: IP address
        :return: API response
        """
        import ipaddress
        
        # Validate IP address
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")
        
        # Validate hostname
        if not hostname or hostname.strip() == "":
            raise ValueError("Hostname cannot be empty")
        
        return self.add_a_record(hostname, ip)