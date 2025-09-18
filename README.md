# 🍓 pihole6api

This package provides a simple, modular SDK for the PiHole 6 REST API.

## Features

* Automatically handles authentication and renewal
* Graceful error management
* Logically organized modules
* Easily maintained

## Installation

**Install using `pip`:**

```bash
pip install pihole6api
```

**Install from source:**

```bash
git clone https://github.com/sbarbett/pihole6api.git
cd pihole6api
uv sync && uv pip install -e .
```

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and virtual environment handling.

**Prerequisites:**

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Setup development environment:**

```bash
git clone https://github.com/sbarbett/pihole6api.git
cd pihole6api
uv sync  # Creates virtual environment and installs all dependencies
```

**Running tests:**

```bash
# Run all tests
make test

# Run specific test categories
make test-auth     # Authentication tests
make test-dns      # DNS management tests
make test-quick    # Core tests only (excludes performance tests)

# Other useful commands
make install       # Install in development mode (uv sync)
make deps          # Install dependencies (uv sync)
make clean         # Clean up cache files
make info          # Show test information
```

**Working with dependencies:**

The project uses `uv.lock` to ensure reproducible builds. When adding new dependencies:

```bash
uv add package-name              # Add runtime dependency
uv add --dev package-name        # Add development dependency
uv sync                          # Sync environment with lock file
```

## Quick Start

### Initialize the Client

```python
from pihole6api import PiHole6Client
client = PiHole6Client("https://your-pihole.local/", "your-password")
```

### Example Usage

#### Get Pi-Hole Metrics

```python
history = client.metrics.get_history()
print(history)  # {'history': [{'timestamp': 1740120900, 'total': 0, 'cached': 0 ...}]}
queries = client.metrics.get_queries()
print(queries)
```

#### Enable/Disable Blocking

```python
client.dns_control.set_blocking_status(False, 60)
print(client.dns_control.get_blocking_status()) # {'blocking': 'disabled', 'timer': 60 ...}
```

#### Manage Groups

```python
client.group_management.add_group("Custom Group", comment="For testing")
client.group_management.delete_group("Custom Group")
```

#### Manage Domains

```python
client.domain_management.add_domain("ads.example.com", "deny", "exact")
client.domain_management.delete_domain("ads.example.com", "deny", "exact")
```

#### Manage Links

```python
client.list_management.add_list("https://example.com/blocklist.txt", "block")
client.list_management.delete_list("https://example.com/blocklist.txt", "block")
```

#### Export/Import PiHole Settings

```python
# Export settings and save as a .zip file
with open("pihole-settings.zip", "wb") as f:
    f.write(client.config.export_settings())

client.config.import_settings("pihole-settings.zip", {"config": True, "gravity": {"group": True}})
```

#### Flush Logs & Restart DNS

```python
client.actions.flush_logs()
client.actions.restart_dns()
```

## API Reference

### PiHole6Client

The main client class that provides access to all Pi-hole API functionality.

```python
from pihole6api import PiHole6Client

client = PiHole6Client(base_url, password)
```

**Constructor Parameters:**
- `base_url` (str): The base URL of your Pi-hole instance (e.g., "http://pi.hole/api/")
- `password` (str): Pi-hole web admin password or application password

**Client Methods:**

#### `get_padd_summary(full=False)`
Get summarized data for PADD (Pi-hole dashboard).
- `full` (bool): Return full dataset if True
- **Returns:** Dictionary with PADD summary data

#### `close_session()`
Close the Pi-hole session and clean up connections.
- **Returns:** API response confirming session closure

#### `version()`
Get package version and metadata information.
- **Returns:** Dictionary with version, description, and project URL

---

### API Modules

The client provides access to specialized modules for different Pi-hole functionalities:

## Metrics Module (`client.metrics`)

Handles Pi-hole metrics, statistics, and query history.

### History Methods

#### `get_history()`
Get activity graph data for the Pi-hole dashboard.
- **Returns:** Dictionary with historical query data

#### `get_history_clients(clients=20)`
Get per-client activity graph data.
- `clients` (int): Number of clients to return (0 = all clients)
- **Returns:** Dictionary with per-client historical data

#### `get_history_database(start, end)`
Get long-term activity graph data from database.
- `start` (int): Start date as Unix timestamp
- `end` (int): End date as Unix timestamp
- **Returns:** Long-term historical data

#### `get_history_database_clients(start, end)`
Get per-client long-term activity data.
- `start` (int): Start date as Unix timestamp
- `end` (int): End date as Unix timestamp
- **Returns:** Per-client long-term data

### Query Methods

#### `get_queries(length=100, from_ts=None, until_ts=None, upstream=None, domain=None, client=None, cursor=None)`
Get query log with optional filtering.
- `length` (int): Number of queries to retrieve (default: 100)
- `from_ts` (int, optional): Unix timestamp to filter from
- `until_ts` (int, optional): Unix timestamp to filter until
- `upstream` (str, optional): Filter by upstream destination
- `domain` (str, optional): Filter by domain (supports wildcards)
- `client` (str, optional): Filter by client
- `cursor` (str, optional): Pagination cursor
- **Returns:** Filtered query log data

#### `get_query_suggestions()`
Get query filter suggestions for the query log.
- **Returns:** Available filter suggestions

### Statistics Methods

#### `get_stats_summary()`
Get overview of Pi-hole activity.
- **Returns:** Summary statistics (total queries, blocked, etc.)

#### `get_stats_query_types()`
Get current query type distribution.
- **Returns:** Query types breakdown

#### `get_stats_top_clients(blocked=None, count=None)`
Get top clients by query volume.
- `blocked` (bool, optional): Filter by blocked/allowed queries
- `count` (int, optional): Number of results to return
- **Returns:** Top clients list

#### `get_stats_top_domains(blocked=None, count=None)`
Get top domains by query volume.
- `blocked` (bool, optional): Filter by blocked/allowed queries  
- `count` (int, optional): Number of results to return
- **Returns:** Top domains list

#### `get_stats_upstreams()`
Get upstream DNS server statistics.
- **Returns:** Upstream server data

#### `get_stats_recent_blocked(count=None)`
Get most recently blocked domains.
- `count` (int, optional): Number of results to return
- **Returns:** Recently blocked domains

### Database Statistics Methods

#### `get_stats_database_summary(start, end)`
Get database content details for date range.
- `start` (int): Start Unix timestamp
- `end` (int): End Unix timestamp
- **Returns:** Database summary for period

#### `get_stats_database_query_types(start, end)`
Get query types from long-term database.
- `start` (int): Start Unix timestamp
- `end` (int): End Unix timestamp  
- **Returns:** Query types for period

#### `get_stats_database_top_clients(start, end, blocked=None, count=None)`
Get top clients from long-term database.
- `start` (int): Start Unix timestamp
- `end` (int): End Unix timestamp
- `blocked` (bool, optional): Filter blocked/allowed
- `count` (int, optional): Number of results
- **Returns:** Top clients for period

#### `get_stats_database_top_domains(start, end, blocked=None, count=None)`
Get top domains from long-term database.
- `start` (int): Start Unix timestamp
- `end` (int): End Unix timestamp
- `blocked` (bool, optional): Filter blocked/allowed
- `count` (int, optional): Number of results
- **Returns:** Top domains for period

#### `get_stats_database_upstreams(start, end)`
Get upstream metrics from database.
- `start` (int): Start Unix timestamp
- `end` (int): End Unix timestamp
- **Returns:** Upstream data for period

---

## DNS Control Module (`client.dns_control`)

Manages Pi-hole DNS blocking functionality.

#### `get_blocking_status()`
Get current DNS blocking status.
- **Returns:** Dictionary with blocking status and timer

#### `set_blocking_status(blocking, timer=None)`
Change DNS blocking status.
- `blocking` (bool): True to enable, False to disable blocking
- `timer` (int, optional): Timer in seconds for temporary change
- **Returns:** API response confirming change

---

## Domain Management Module (`client.domain_management`)

Manages allow/block domain lists (exact and regex).

#### `get_all_domains(domain_type=None, kind=None)`
Get all configured domains.
- `domain_type` (str, optional): Filter by "allow" or "deny"
- `kind` (str, optional): Filter by "exact" or "regex"
- **Returns:** List of all matching domains

#### `add_domain(domain, domain_type, kind, comment=None, groups=None, enabled=True)`
Add a new domain to Pi-hole.
- `domain` (str|list): Domain name(s) to add
- `domain_type` (str): "allow" or "deny"
- `kind` (str): "exact" or "regex"
- `comment` (str, optional): Comment for the domain
- `groups` (list, optional): List of group IDs
- `enabled` (bool): Enable the domain (default: True)
- **Returns:** API response confirming addition

#### `get_domain(domain, domain_type, kind)`
Get information about a specific domain.
- `domain` (str): Domain name
- `domain_type` (str): "allow" or "deny"
- `kind` (str): "exact" or "regex"
- **Returns:** Domain information

#### `update_domain(domain, domain_type, kind, new_type=None, new_kind=None, comment=None, groups=None, enabled=True)`
Update an existing domain entry.
- `domain` (str): Domain name
- `domain_type` (str): Current domain type
- `kind` (str): Current kind
- `new_type` (str, optional): New domain type
- `new_kind` (str, optional): New kind
- `comment` (str, optional): Updated comment
- `groups` (list, optional): Updated group list
- `enabled` (bool): Enable status
- **Returns:** API response confirming update

#### `delete_domain(domain, domain_type, kind)`
Delete a single domain.
- `domain` (str): Domain name
- `domain_type` (str): "allow" or "deny"
- `kind` (str): "exact" or "regex"
- **Returns:** API response confirming deletion

#### `batch_delete_domains(domains)`
Delete multiple domains at once.
- `domains` (list): List of domain dictionaries with "item", "type", "kind" keys
- **Returns:** API response confirming batch deletion

---

## List Management Module (`client.list_management`)

Manages blocklist and allowlist URLs (Adlists).

#### `get_lists(list_type=None)`
Get all configured lists.
- `list_type` (str, optional): Filter by "allow" or "block"
- **Returns:** List of all matching lists

#### `add_list(address, list_type, comment=None, groups=None, enabled=True)`
Add a new list to Pi-hole.
- `address` (str|list): URL(s) of the list
- `list_type` (str): "allow" or "block"
- `comment` (str, optional): Comment for the list
- `groups` (list, optional): List of group IDs
- `enabled` (bool): Enable the list (default: True)
- **Returns:** API response confirming addition

#### `get_list(address, list_type)`
Get information about a specific list.
- `address` (str): URL of the list
- `list_type` (str): "allow" or "block"
- **Returns:** List information

#### `update_list(address, list_type, comment=None, groups=None, enabled=True)`
Update an existing list.
- `address` (str): URL of the list
- `list_type` (str): "allow" or "block"
- `comment` (str, optional): Updated comment
- `groups` (list, optional): Updated group list
- `enabled` (bool): Enable status
- **Returns:** API response confirming update

#### `delete_list(address, list_type)`
Delete a single list.
- `address` (str): URL of the list
- `list_type` (str): "allow" or "block"
- **Returns:** API response confirming deletion

#### `batch_delete_lists(lists)`
Delete multiple lists at once.
- `lists` (list): List of dictionaries with "item" and "type" keys
- **Returns:** API response confirming batch deletion

---

## Local DNS Module (`client.local_dns`)

Manages local DNS records (A and CNAME records).

#### `get_all_records(record_type=None)`
Get all local DNS records.
- `record_type` (str, optional): Filter by "A" or "CNAME"
- **Returns:** Dictionary with "A" and "CNAME" keys containing records

#### `get_a_records()`
Get only local A records.
- **Returns:** Dictionary of hostname -> IP mappings

#### `get_cname_records()`
Get only local CNAME records.
- **Returns:** Dictionary of alias -> target mappings

#### `add_a_record(hostname, ip)`
Add a local A record.
- `hostname` (str): The hostname (e.g., "foo.dev")
- `ip` (str): The IP address (e.g., "192.168.1.1")
- **Returns:** API response confirming addition

#### `add_cname_record(source, target)`
Add a local CNAME record.
- `source` (str): The alias domain
- `target` (str): The target domain
- **Returns:** API response confirming addition

#### `delete_a_record(hostname)`
Delete a local A record.
- `hostname` (str): The hostname to remove
- **Returns:** API response confirming deletion

#### `delete_cname_record(source)`
Delete a local CNAME record.
- `source` (str): The alias domain to remove
- **Returns:** API response confirming deletion

---

## Configuration Module (`client.config`)

Manages Pi-hole configuration settings and teleporter functionality.

#### `get_config(detailed=False)`
Get current Pi-hole configuration.
- `detailed` (bool): Get detailed configuration
- **Returns:** Configuration data

#### `update_config(config_changes)`
Modify Pi-hole configuration.
- `config_changes` (dict): Dictionary of configuration updates
- **Returns:** API response confirming changes

#### `get_config_section(element, detailed=False)`
Get specific configuration section.
- `element` (str): Configuration section name
- `detailed` (bool): Detailed output flag
- **Returns:** Requested configuration section

#### `add_config_item(element, value)`
Add item to configuration array.
- `element` (str): Configuration section
- `value` (str): Value to add
- **Returns:** API response confirming addition

#### `delete_config_item(element, value)`
Remove item from configuration array.
- `element` (str): Configuration section
- `value` (str): Value to remove
- **Returns:** API response confirming deletion

#### `export_settings()`
Export Pi-hole settings as archive.
- **Returns:** Binary content of settings archive

#### `import_settings(file_path, import_options=None)`
Import Pi-hole settings from archive.
- `file_path` (str): Path to teleporter archive file
- `import_options` (dict, optional): Import configuration options
- **Returns:** API response confirming import

---

## Actions Module (`client.actions`)

System action endpoints for maintenance operations.

#### `flush_arp()`
Flush the network ARP cache.
- **Returns:** API response confirming action

#### `flush_logs()`
Flush the DNS query logs.
- **Returns:** API response confirming action

#### `run_gravity()`
Run gravity to update blocklists.
- **Returns:** API response confirming action

#### `restart_dns()`
Restart the Pi-hole FTL DNS resolver.
- **Returns:** API response confirming action

---

## Group Management Module (`client.group_management`)

Manages Pi-hole groups for organizing domains and clients.

#### `get_groups()`
Get all configured groups.
- **Returns:** List of all groups

#### `add_group(name, comment=None, enabled=True)`
Add a new group.
- `name` (str): Group name
- `comment` (str, optional): Group comment
- `enabled` (bool): Enable the group
- **Returns:** API response confirming addition

#### `get_group(name)`
Get information about specific group.
- `name` (str): Group name
- **Returns:** Group information

#### `update_group(name, new_name=None, comment=None, enabled=True)`
Update an existing group.
- `name` (str): Current group name
- `new_name` (str, optional): New group name
- `comment` (str, optional): Updated comment
- `enabled` (bool): Enable status
- **Returns:** API response confirming update

#### `delete_group(name)`
Delete a group.
- `name` (str): Group name to delete
- **Returns:** API response confirming deletion

---

## Client Management Module (`client.client_management`)

Manages client-specific settings and rules.

#### `get_clients()`
Get all configured clients.
- **Returns:** List of all clients

#### `add_client(name, addresses=None, comment=None, groups=None)`
Add a new client.
- `name` (str): Client name
- `addresses` (list, optional): List of client IP/MAC addresses
- `comment` (str, optional): Client comment
- `groups` (list, optional): List of group IDs
- **Returns:** API response confirming addition

#### `get_client(name)`
Get information about specific client.
- `name` (str): Client name
- **Returns:** Client information

#### `update_client(name, new_name=None, addresses=None, comment=None, groups=None)`
Update an existing client.
- `name` (str): Current client name
- `new_name` (str, optional): New client name
- `addresses` (list, optional): Updated addresses
- `comment` (str, optional): Updated comment
- `groups` (list, optional): Updated group list
- **Returns:** API response confirming update

#### `delete_client(name)`
Delete a client.
- `name` (str): Client name to delete
- **Returns:** API response confirming deletion

---

## FTL Info Module (`client.ftl_info`)

Provides information about Pi-hole's FTL (Faster Than Light) DNS server.

#### `get_ftl_info()`
Get FTL process information.
- **Returns:** FTL status and version information

---

## Network Info Module (`client.network_info`)

Provides network-related information and device discovery.

#### `get_network_info()`
Get network interfaces and configuration.
- **Returns:** Network interface information

#### `get_network_devices()`
Get discovered network devices.
- **Returns:** List of network devices

---

## DHCP Module (`client.dhcp`)

Manages DHCP lease information and settings.

#### `get_dhcp_leases()`
Get current DHCP lease information.
- **Returns:** List of DHCP leases

#### `get_dhcp_config()`
Get DHCP server configuration.
- **Returns:** DHCP configuration settings

---

## Error Handling

All API methods return the raw API response from Pi-hole. In case of errors, the response will typically contain error information in the following format:

```python
{
    "error": "Error description",
    "details": "Additional error details"
}
```

For network-related errors, exceptions may be raised:
- `ConnectionError`: Network connectivity issues
- `TimeoutError`: Request timeout
- `Exception`: Authentication or API errors

## Example Usage Patterns

### Basic Monitoring
```python
from pihole6api import PiHole6Client

client = PiHole6Client("http://pi.hole", "password")

# Get overall statistics
stats = client.metrics.get_stats_summary()
print(f"Total queries: {stats['total_queries']}")
print(f"Blocked: {stats['blocked_queries']}")

# Get recent activity
recent = client.metrics.get_history()
```

### Domain Management
```python
# Add domains to blocklist
client.domain_management.add_domain("ads.example.com", "deny", "exact")
client.domain_management.add_domain(".*\.tracker\..*", "deny", "regex")

# Add to allowlist
client.domain_management.add_domain("safe.example.com", "allow", "exact")

# Get all blocked domains
blocked = client.domain_management.get_all_domains("deny")
```

### Temporary Blocking Control
```python
# Disable blocking for 5 minutes
client.dns_control.set_blocking_status(False, timer=300)

# Check status
status = client.dns_control.get_blocking_status()
print(f"Blocking: {status['blocking']}, Time left: {status.get('timer', 0)}")
```

### Configuration Backup
```python
# Export settings
backup = client.config.export_settings()
with open("pihole-backup.tar.gz", "wb") as f:
    f.write(backup)

# Import settings later
client.config.import_settings("pihole-backup.tar.gz")
```

## Contributing

Please check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## License

This project is licensed under the [MIT license](LICENSE).
