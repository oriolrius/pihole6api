class PiHole6NetworkInfo:
    def __init__(self, connection):
        """Handles Pi-hole network information API endpoints."""
        self.connection = connection

    def get_devices(self):
        """Get information about devices on the local network."""
        return self.connection.get("network/devices")

    def delete_device(self, device_id):
        """
        Delete a device from the network table.

        :param device_id: The ID of the device to delete.
        """
        return self.connection.delete(f"network/devices/{device_id}")

    def get_gateway(self):
        """Get information about the gateway of the Pi-hole."""
        return self.connection.get("network/gateway")

    def get_interfaces(self):
        """Get information about network interfaces of the Pi-hole."""
        return self.connection.get("network/interfaces")

    def get_routes(self):
        """Get information about network routes of the Pi-hole."""
        return self.connection.get("network/routes")
