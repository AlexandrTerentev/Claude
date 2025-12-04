import socket
import time
from threading import Thread
from typing import Callable


class NetworkMonitor:
    """Monitors internet connectivity and triggers callbacks on state changes."""

    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.is_monitoring = False
        self.was_connected = True
        self.monitor_thread: Thread | None = None
        self.on_reconnect: Callable[[], None] | None = None
        self.on_disconnect: Callable[[], None] | None = None

    def start_monitoring(
        self,
        on_reconnect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None
    ):
        """Start monitoring internet connectivity."""
        print("[NetworkMonitor] start_monitoring called", flush=True)

        if self.is_monitoring:
            print("[NetworkMonitor] Already monitoring, skipping", flush=True)
            return

        self.on_reconnect = on_reconnect
        self.on_disconnect = on_disconnect
        self.is_monitoring = True
        self.was_connected = self.check_connection()

        print(f"[NetworkMonitor] Initial connection state: {self.was_connected}", flush=True)

        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"[NetworkMonitor] Thread started: {self.monitor_thread.is_alive()}", flush=True)

    def stop_monitoring(self):
        """Stop monitoring internet connectivity."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
            self.monitor_thread = None

    def check_connection(self) -> bool:
        """Check if internet is available by pinging Google DNS."""
        try:
            # Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            pass

        try:
            # Fallback: try Cloudflare DNS
            socket.create_connection(("1.1.1.1", 53), timeout=3)
            return True
        except OSError:
            return False

    def _monitor_loop(self):
        """Main monitoring loop."""
        print(f"[NetworkMonitor] Starting loop, initial state: was_connected={self.was_connected}", flush=True)

        while self.is_monitoring:
            is_connected = self.check_connection()

            print(f"[NetworkMonitor] Check: is_connected={is_connected}, was_connected={self.was_connected}", flush=True)

            # Detect state change
            if is_connected and not self.was_connected:
                # Internet restored
                print("[NetworkMonitor] Internet connection restored - triggering callback", flush=True)
                if self.on_reconnect:
                    self.on_reconnect()

            elif not is_connected and self.was_connected:
                # Internet lost
                print("[NetworkMonitor] Internet connection lost", flush=True)
                if self.on_disconnect:
                    self.on_disconnect()

            self.was_connected = is_connected
            time.sleep(self.check_interval)

        print("[NetworkMonitor] Loop stopped", flush=True)

    def is_connected(self) -> bool:
        """Get current connection status."""
        return self.was_connected
