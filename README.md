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
pip install -e .
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
make install       # Install in development mode
make deps          # Install dependencies
make clean         # Clean up cache files
make info          # Show test information
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

## API Modules

| Module                | Description |
|----------------------|-------------|
| `metrics`           | Query history, top clients/domains, DNS stats |
| `dns_control`       | Enable/disable blocking |
| `group_management`  | Create, update, and delete groups |
| `domain_management` | Allow/block domains (exact & regex) |
| `client_management` | Manage client-specific rules |
| `list_management`   | Manage blocklists (Adlists) |
| `config`            | Modify Pi-hole configuration |
| `ftl_info`          | Get Pi-hole core process (FTL) info |
| `dhcp`              | Manage DHCP leases |
| `network_info`      | View network devices, interfaces, routes |
| `actions`           | Flush logs, restart services |

## Contributing

Please check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

## License

This project is license under the [MIT license](LICENSE).
