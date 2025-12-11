import requests
import urllib3
from typing import Dict, List, Optional
from datetime import datetime

# Disable SSL warnings for Cloudflare
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AccessControlAPI:
    """Complete Python API client for Pi Zero Access Control System"""

    def __init__(self, base_url: str, api_key: str, verify_ssl: bool = False):
        """
        Initialize the API client.

        Args:
            base_url: Base URL (e.g., 'https://residential_tirumala_zero.easyslot.in')
            api_key: Your API key
            verify_ssl: Set to False for Cloudflare issues (default: False)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.token = None
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # ==================== AUTHENTICATION ====================

    def login(self, username: str, password: str) -> bool:
        """
        Login to get authentication token.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            bool: True if login successful
        """
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                self.token = data.get("token")
                print("✓ Login successful")
                return True
            return False
        except Exception as e:
            print(f"✗ Login failed: {e}")
            return False

    def logout(self) -> bool:
        """Logout and invalidate token."""
        try:
            response = self.session.post(
                f"{self.base_url}/logout",
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            self.token = None
            print("✓ Logout successful")
            return True
        except Exception as e:
            print(f"✗ Logout failed: {e}")
            return False

    # ==================== SYSTEM STATUS ====================

    def get_status(self) -> Optional[Dict]:
        """
        Get system status including components, storage, and temperature.

        Returns:
            System status dictionary
        """
        try:
            response = self.session.get(
                f"{self.base_url}/status",
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting status: {e}")
            return None

    def health_check(self) -> Optional[Dict]:
        """Get quick health check (internet, Firebase, pigpio)."""
        try:
            response = self.session.get(
                f"{self.base_url}/health_check",
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error in health check: {e}")
            return None

    # ==================== USER MANAGEMENT ====================

    def get_users(self) -> Optional[List[Dict]]:
        """
        Get all users with their information.

        Returns:
            List of user dictionaries
        """
        try:
            response = self.session.get(
                f"{self.base_url}/get_users",
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting users: {e}")
            return None

    def add_user(self, card_number: str, user_id: str, name: str, ref_id: str = "") -> bool:
        """
        Add a new user.

        Args:
            card_number: Card number (numeric string)
            user_id: User ID
            name: User's name
            ref_id: Optional reference ID

        Returns:
            bool: True if successful
        """
        try:
            response = self.session.post(
                f"{self.base_url}/add_user",
                headers=self._get_headers(),
                json={
                    "card_number": card_number,
                    "id": user_id,
                    "name": name,
                    "ref_id": ref_id
                },
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ User added: {name}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error adding user: {e}")
            return False

    def delete_user(self, card_number: str) -> bool:
        """Delete a user."""
        try:
            response = self.session.post(
                f"{self.base_url}/delete_user",
                headers=self._get_headers(),
                json={"card_number": card_number},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ User deleted: {card_number}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error deleting user: {e}")
            return False

    def block_user(self, card_number: str) -> bool:
        """Block a user from accessing."""
        try:
            response = self.session.post(
                f"{self.base_url}/block_user",
                headers=self._get_headers(),
                json={"card_number": card_number},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ User blocked: {card_number}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error blocking user: {e}")
            return False

    def unblock_user(self, card_number: str) -> bool:
        """Unblock a user."""
        try:
            response = self.session.post(
                f"{self.base_url}/unblock_user",
                headers=self._get_headers(),
                json={"card_number": card_number},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ User unblocked: {card_number}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error unblocking user: {e}")
            return False

    def toggle_privacy(self, card_number: str, enable: bool, password: str) -> bool:
        """
        Toggle privacy protection for a user (requires admin password).

        Args:
            card_number: Card number
            enable: True to enable privacy, False to disable
            password: Admin password for confirmation
        """
        try:
            response = self.session.post(
                f"{self.base_url}/toggle_privacy",
                headers=self._get_headers(),
                json={
                    "card_number": card_number,
                    "enable": enable,
                    "password": password
                },
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                action = "enabled" if enable else "disabled"
                print(f"✓ Privacy {action} for: {card_number}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error toggling privacy: {e}")
            return False

    # ==================== RELAY CONTROL ====================

    def control_relay(self, relay_number: int, action: str = "normal") -> bool:
        """
        Control relay (door lock).

        Args:
            relay_number: Relay number (1, 2, or 3)
            action: 'normal' (pulse 1s), 'open_hold', or 'close_hold'

        Returns:
            bool: True if successful
        """
        try:
            response = self.session.post(
                f"{self.base_url}/relay",
                headers=self._get_headers(),
                json={
                    "relay": relay_number,
                    "action": action
                },
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ Relay {relay_number}: {action}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error controlling relay: {e}")
            return False

    def pulse_relay(self, relay_number: int) -> bool:
        """Pulse relay for 1 second (normal operation)."""
        return self.control_relay(relay_number, "normal")

    def open_relay(self, relay_number: int) -> bool:
        """Open relay and hold."""
        return self.control_relay(relay_number, "open_hold")

    def close_relay(self, relay_number: int) -> bool:
        """Close relay and hold."""
        return self.control_relay(relay_number, "close_hold")

    # ==================== TRANSACTIONS ====================

    def get_transactions(self, limit: int = 50) -> Optional[List[Dict]]:
        """
        Get recent transactions.

        Args:
            limit: Number of transactions to retrieve (default: 50)

        Returns:
            List of transaction dictionaries
        """
        try:
            response = self.session.get(
                f"{self.base_url}/get_transactions",
                params={"limit": limit},
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting transactions: {e}")
            return None

    def get_today_stats(self) -> Optional[Dict]:
        """Get today's access statistics."""
        try:
            response = self.session.get(
                f"{self.base_url}/get_today_stats",
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"✗ Error getting today's stats: {e}")
            return None

    def download_transactions_csv(self, limit: int = 500) -> Optional[str]:
        """
        Download transactions as CSV.

        Args:
            limit: Number of transactions to export

        Returns:
            CSV string content
        """
        try:
            response = self.session.get(
                f"{self.base_url}/download_transactions_csv",
                params={"limit": limit},
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("csv")
            return None
        except Exception as e:
            print(f"✗ Error downloading CSV: {e}")
            return None

    # ==================== ANALYTICS ====================

    def get_analytics(self, days: int = 7, card_number: str = None) -> Optional[Dict]:
        """
        Get comprehensive analytics.

        Args:
            days: Number of days to analyze (default: 7)
            card_number: Optional - analyze specific user

        Returns:
            Analytics dictionary
        """
        try:
            params = {"days": days}
            if card_number:
                params["card"] = card_number

            response = self.session.get(
                f"{self.base_url}/get_analytics",
                params=params,
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("analytics")
            return None
        except Exception as e:
            print(f"✗ Error getting analytics: {e}")
            return None

    def get_user_report(self, card_number: str, days: int = 30) -> Optional[Dict]:
        """
        Get detailed report for specific user.

        Args:
            card_number: Card number
            days: Number of days to include (default: 30)

        Returns:
            User report dictionary
        """
        try:
            response = self.session.get(
                f"{self.base_url}/get_user_report",
                params={"card": card_number, "days": days},
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("report")
            return None
        except Exception as e:
            print(f"✗ Error getting user report: {e}")
            return None

    # ==================== TIME MANAGEMENT ====================

    def get_system_time(self) -> Optional[Dict]:
        """Get current system time and timezone info."""
        try:
            response = self.session.get(
                f"{self.base_url}/get_system_time",
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data
            return None
        except Exception as e:
            print(f"✗ Error getting system time: {e}")
            return None

    def set_system_time(self, timestamp: int) -> bool:
        """
        Set system time (requires sudo permissions on Pi).

        Args:
            timestamp: Unix timestamp in seconds

        Returns:
            bool: True if successful
        """
        try:
            response = self.session.post(
                f"{self.base_url}/set_system_time",
                headers=self._get_headers(),
                json={"timestamp": timestamp},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ System time updated")
                return True
            return False
        except Exception as e:
            print(f"✗ Error setting system time: {e}")
            return False

    def set_time_from_browser(self) -> bool:
        """Set system time from current computer time."""
        import time
        return self.set_system_time(int(time.time()))

    def enable_ntp(self, enable: bool = True) -> bool:
        """
        Enable or disable NTP time synchronization.

        Args:
            enable: True to enable, False to disable
        """
        try:
            response = self.session.post(
                f"{self.base_url}/enable_ntp",
                headers=self._get_headers(),
                json={"enable": enable},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                action = "enabled" if enable else "disabled"
                print(f"✓ NTP {action}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error configuring NTP: {e}")
            return False

    # ==================== CONFIGURATION ====================

    def get_config(self) -> Optional[Dict]:
        """Get current system configuration."""
        try:
            response = self.session.get(
                f"{self.base_url}/get_config",
                headers=self._get_headers(),
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return data.get("config")
            return None
        except Exception as e:
            print(f"✗ Error getting config: {e}")
            return None

    def update_config(self, config: Dict) -> bool:
        """
        Update system configuration.

        Args:
            config: Configuration dictionary with keys:
                - wiegand_bits: {"reader_1": 26, "reader_2": 26, "reader_3": 26}
                - wiegand_timeout_ms: 25
                - scan_delay_seconds: 60
                - entry_exit_tracking: {"enabled": False, "min_gap_seconds": 300}
                - entity_id: "your_entity_id"
        """
        try:
            response = self.session.post(
                f"{self.base_url}/update_config",
                headers=self._get_headers(),
                json={"config": config},
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ Configuration updated")
                return True
            return False
        except Exception as e:
            print(f"✗ Error updating config: {e}")
            return False

    def update_security(self, new_password: str = None, new_api_key: str = None) -> bool:
        """
        Update security settings (admin password and/or API key).

        Args:
            new_password: New admin password (min 8 chars)
            new_api_key: New API key (min 16 chars)
        """
        try:
            payload = {}
            if new_password:
                payload["new_password"] = new_password
            if new_api_key:
                payload["new_api_key"] = new_api_key

            response = self.session.post(
                f"{self.base_url}/update_security",
                headers=self._get_headers(),
                json=payload,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                print(f"✓ Security settings updated")
                return True
            return False
        except Exception as e:
            print(f"✗ Error updating security: {e}")
            return False


# ==================== EXAMPLE USAGE ====================

def main():
    """Example usage of all API functions"""

    # Configuration
    BASE_URL = "https://residential_tirumala_zero.easyslot.in"
    API_KEY = "your-api-key-change-this"
    USERNAME = "admin"
    PASSWORD = "admin123"

    # Initialize API
    api = AccessControlAPI(BASE_URL, API_KEY, verify_ssl=False)

    # Login
    if not api.login(USERNAME, PASSWORD):
        return

    print("\n" + "=" * 80)
    print("SYSTEM STATUS")
    print("=" * 80)

    # Get system status
    status = api.get_status()
    if status:
        print(f"System: {status.get('system')}")
        print(f"Firebase: {status['components']['firebase']}")
        print(f"Internet: {status['components']['internet']}")
        print(f"CPU Temp: {status['temperature']['cpu_celsius']}°C")

    print("\n" + "=" * 80)
    print("USER MANAGEMENT")
    print("=" * 80)

    # Get all users
    users = api.get_users()
    if users:
        print(f"\nTotal Users: {len(users)}\n")
        for user in users[:5]:  # Show first 5
            print(f"  • {user['name']} (Card: {user['card_number']})")

    # Add a new user
    # api.add_user("99999999", "TEST001", "Test User", "REF001")

    # Block/Unblock user
    # api.block_user("99999999")
    # api.unblock_user("99999999")

    # Delete user
    # api.delete_user("99999999")

    print("\n" + "=" * 80)
    print("RELAY CONTROL")
    print("=" * 80)

    # Control relays (doors)
    # api.pulse_relay(1)           # Pulse relay 1 for 1 second
    # api.open_relay(2)            # Open and hold relay 2
    # api.close_relay(2)           # Close relay 2
    print("(Relay control commented out for safety)")

    print("\n" + "=" * 80)
    print("TRANSACTIONS")
    print("=" * 80)

    # Get today's stats
    stats = api.get_today_stats()
    if stats:
        print(f"\nToday's Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Granted: {stats['granted']}")
        print(f"  Denied: {stats['denied']}")
        print(f"  Blocked: {stats['blocked']}")

    # Get recent transactions
    transactions = api.get_transactions(limit=10)
    if transactions:
        print(f"\nRecent Transactions ({len(transactions)}):")
        for tx in transactions[:3]:
            ts = datetime.fromtimestamp(tx['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  • {tx['name']} - {tx['status']} - {ts}")

    print("\n" + "=" * 80)
    print("ANALYTICS")
    print("=" * 80)

    # Get analytics for last 7 days
    analytics = api.get_analytics(days=7)
    if analytics:
        print(f"\n7-Day Analytics:")
        print(f"  Total Transactions: {analytics['total_transactions']}")
        print(f"  Unique Users: {analytics['unique_users']}")
        print(f"  Peak Hour: {analytics['peak_hour']}:00")
        print(f"  Busiest Reader: {analytics['busiest_reader']}")

    # Get user report
    if users and len(users) > 0:
        first_user_card = users[0]['card_number']
        report = api.get_user_report(first_user_card, days=7)
        if report:
            print(f"\nUser Report: {report['user']['name']}")
            print(f"  Total Accesses: {report['summary']['total_accesses']}")
            print(f"  Avg Per Day: {report['summary']['avg_per_day']}")

    print("\n" + "=" * 80)
    print("CONFIGURATION")
    print("=" * 80)

    # Get current config
    config = api.get_config()
    if config:
        print(f"\nCurrent Configuration:")
        print(f"  Wiegand Bits: {config['wiegand_bits']}")
        print(f"  Scan Delay: {config['scan_delay_seconds']}s")
        print(f"  Entity ID: {config['entity_id']}")

    # Update configuration (example)
    # new_config = {
    #     "wiegand_bits": {"reader_1": 26, "reader_2": 26, "reader_3": 26},
    #     "scan_delay_seconds": 60,
    #     "entry_exit_tracking": {"enabled": False, "min_gap_seconds": 300}
    # }
    # api.update_config(new_config)

    print("\n" + "=" * 80)
    print("TIME MANAGEMENT")
    print("=" * 80)

    # Get system time
    sys_time = api.get_system_time()
    if sys_time:
        print(f"\nSystem Time: {sys_time['formatted']}")
        print(f"Timezone: {sys_time['timezone']}")

    # Set time from current computer
    # api.set_time_from_browser()

    # Enable NTP
    # api.enable_ntp(True)

    print("\n" + "=" * 80)
    print("CSV EXPORT")
    print("=" * 80)

    # Download transactions as CSV
    csv_data = api.download_transactions_csv(limit=100)
    if csv_data:
        print(f"\nCSV Export Preview:")
        print("\n".join(csv_data.split("\n")[:5]))  # Show first 5 lines

        # Save to file
        # with open("transactions.csv", "w") as f:
        #     f.write(csv_data)
        # print("✓ Saved to transactions.csv")

    # Logout
    api.logout()

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
