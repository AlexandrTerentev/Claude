# -*- coding: utf-8 -*-
"""
Log Downloader for MPDiagnosticAgent
Downloads dataflash logs (.bin files) from ArduPilot drones via MAVLink

Based on MAVProxy log download protocol:
https://github.com/tridge/MAVProxy/blob/master/MAVProxy/modules/mavproxy_log.py
"""

import time
import os
from pathlib import Path
from typing import Optional, Callable, List, Dict
from pymavlink import mavutil

# Handle imports for both module and standalone usage
try:
    from .mavlink_interface import MAVLinkInterface
    from .config import Config
except ImportError:
    from mavlink_interface import MAVLinkInterface
    from config import Config


class LogEntry:
    """Represents a single log entry on the drone"""
    def __init__(self, log_id: int, num_logs: int, last_log_num: int,
                 time_utc: int, size: int):
        self.id = log_id
        self.num_logs = num_logs
        self.last_log_num = last_log_num
        self.time_utc = time_utc
        self.size = size

    def __repr__(self):
        return f"Log {self.id}: {self.size} bytes, UTC: {self.time_utc}"


class LogDownloader:
    """
    Downloads dataflash logs from ArduPilot drone

    Protocol:
    1. Send LOG_REQUEST_LIST → receive LOG_ENTRY messages
    2. Send LOG_REQUEST_DATA → receive LOG_DATA messages (90 bytes each)
    3. Repeat until LOG_DATA.count < 90 (end of file)
    """

    # MAVLink message IDs
    MAVLINK_MSG_ID_LOG_REQUEST_LIST = 117
    MAVLINK_MSG_ID_LOG_ENTRY = 118
    MAVLINK_MSG_ID_LOG_REQUEST_DATA = 119
    MAVLINK_MSG_ID_LOG_DATA = 120
    MAVLINK_MSG_ID_LOG_ERASE = 121
    MAVLINK_MSG_ID_LOG_REQUEST_END = 122

    # Chunk size for log data requests
    LOG_DATA_CHUNK_SIZE = 90

    def __init__(self, mavlink_interface: Optional[MAVLinkInterface] = None,
                 download_dir: Optional[Path] = None, config: Optional[Config] = None):
        """
        Initialize log downloader

        Args:
            mavlink_interface: MAVLink connection (or None to create new)
            download_dir: Directory to save downloaded logs
            config: Configuration object
        """
        self.config = config if config else Config()

        # MAVLink interface
        if mavlink_interface:
            self.mav = mavlink_interface
            self.own_connection = False
        else:
            self.mav = MAVLinkInterface(config=self.config)
            self.own_connection = True

        # Download directory
        if download_dir:
            self.download_dir = Path(download_dir)
        else:
            self.download_dir = self.config.bin_dir

        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Cache for log list (avoids repeated requests)
        self._cached_logs = None

    def connect(self) -> bool:
        """
        Connect to drone (if using own connection)

        Returns:
            True if connected
        """
        if self.own_connection:
            return self.mav.connect(verbose=True)
        return self.mav.is_connected()

    def disconnect(self):
        """Disconnect from drone (if using own connection)"""
        if self.own_connection:
            self.mav.disconnect()

    def list_logs(self, timeout: int = 10, force_refresh: bool = False) -> List[LogEntry]:
        """
        Get list of available logs on drone

        Args:
            timeout: Timeout in seconds
            force_refresh: Force reconnection to get fresh log list

        Returns:
            List of LogEntry objects
        """
        # Return cached list if available and not forcing refresh
        if self._cached_logs is not None and not force_refresh:
            print(f"✓ Using cached log list ({len(self._cached_logs)} logs)")
            return self._cached_logs

        if not self.mav.is_connected():
            print("✗ Not connected to drone")
            return []

        # Reconnect to get fresh state (workaround for ArduPilot log list limitation)
        # ArduPilot only sends LOG_ENTRY once per connection
        if force_refresh:
            print("  Reconnecting for fresh log list...")
            port = self.mav.connection_string
            baudrate = self.mav.baudrate
            timeout = self.mav.timeout

            # Disconnect current connection
            if self.mav.is_connected():
                self.mav.disconnect()
            time.sleep(0.5)

            # Create new connection
            self.mav = MAVLinkInterface(connection_string=port, baudrate=baudrate, timeout=timeout, config=self.config)
            if not self.mav.connect(verbose=False):
                print("✗ Reconnection failed")
                return []
            print("  ✓ Reconnected successfully")

        print("Requesting log list...")

        # Send LOG_REQUEST_LIST (simple approach - just like debug script)
        self.mav.master.mav.log_request_list_send(
            self.mav.target_system,
            self.mav.target_component,
            0,      # start
            0xFFFF  # end (all logs)
        )

        # Collect LOG_ENTRY messages
        logs = []
        start_time = time.time()
        last_num_logs = None
        msg_count = 0

        print(f"  Listening for LOG_ENTRY messages (timeout: {timeout}s)...")

        while time.time() - start_time < timeout:
            try:
                # Receive ANY message, filter for LOG_ENTRY manually
                msg = self.mav.master.recv_match(blocking=True, timeout=0.5)
            except Exception as e:
                if "device reports readiness" in str(e):
                    time.sleep(0.1)
                    continue
                print(f"✗ Error receiving messages: {e}")
                break

            if msg:
                msg_count += 1
                msg_type = msg.get_type()

                # Debug: show first few messages
                if msg_count <= 5:
                    print(f"  Debug: received {msg_type}")

                if msg_type == 'LOG_ENTRY':
                    if last_num_logs is None:
                        last_num_logs = msg.num_logs
                        print(f"  Drone reports {msg.num_logs} logs total")

                    log_entry = LogEntry(
                        log_id=msg.id,
                        num_logs=msg.num_logs,
                        last_log_num=msg.last_log_num,
                        time_utc=msg.time_utc,
                        size=msg.size
                    )
                    logs.append(log_entry)
                    print(f"  Received log entry {len(logs)}/{msg.num_logs}: ID={msg.id}, size={msg.size}")

                    # Check if we've received all logs
                    if len(logs) >= msg.num_logs:
                        break
            else:
                # No message received
                if logs:
                    print(f"  No more messages, got {len(logs)} logs")
                    break
                elif msg_count == 0:
                    print(f"  No messages received at all (waited {time.time() - start_time:.1f}s)")

        print(f"  Total messages received: {msg_count}, LOG_ENTRY count: {len(logs)}")

        # Send LOG_REQUEST_END to close the list operation
        try:
            self.mav.master.mav.log_request_end_send(
                self.mav.target_system,
                self.mav.target_component
            )
        except:
            pass

        # Sort by ID
        logs.sort(key=lambda x: x.id)

        print(f"✓ Found {len(logs)} logs on drone")

        # Cache the result
        self._cached_logs = logs
        return logs

    def download_log(self, log_id: int, output_file: Optional[Path] = None,
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[Path]:
        """
        Download specific log by ID

        Args:
            log_id: Log ID to download
            output_file: Output file path (auto-generated if None)
            progress_callback: Function(bytes_downloaded, total_bytes) called on progress

        Returns:
            Path to downloaded file, or None if failed
        """
        if not self.mav.is_connected():
            print("✗ Not connected to drone")
            return None

        # Use cached log list if available, otherwise request it
        if self._cached_logs is None:
            logs = self.list_logs()
        else:
            logs = self._cached_logs

        target_log = next((log for log in logs if log.id == log_id), None)

        if not target_log:
            print(f"✗ Log {log_id} not found on drone")
            return None

        total_size = target_log.size
        print(f"Downloading log {log_id} ({total_size} bytes)...")

        # Generate output filename if not provided
        if output_file is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_file = self.download_dir / f"log_{log_id}_{timestamp}.bin"

        # Download data
        offset = 0
        log_data = bytearray()

        try:
            with open(output_file, 'wb') as f:
                retry_count = 0
                max_retries = 3

                while offset < total_size:
                    # Request data chunk
                    count = min(self.LOG_DATA_CHUNK_SIZE, total_size - offset)

                    self.mav.master.mav.log_request_data_send(
                        self.mav.target_system,
                        self.mav.target_component,
                        log_id,
                        offset,
                        count
                    )

                    # Small delay between request and response
                    time.sleep(0.02)

                    # Wait for LOG_DATA response
                    timeout_start = time.time()
                    received = False
                    msg_count_in_chunk = 0

                    while time.time() - timeout_start < 15:  # 15 second timeout per chunk
                        try:
                            # Receive ANY message, filter for LOG_DATA manually
                            msg = self.mav.master.recv_match(blocking=True, timeout=1)
                        except Exception as e:
                            # Handle "device reports readiness" error
                            if "device reports readiness" in str(e):
                                time.sleep(0.2)
                                continue
                            raise

                        if msg:
                            msg_count_in_chunk += 1
                            msg_type = msg.get_type()

                            # Debug first chunk
                            if offset == 0 and msg_count_in_chunk <= 5:
                                print(f"\n  [DEBUG chunk 0] {msg_type}", end='')

                        if msg and msg.get_type() == 'LOG_DATA' and msg.id == log_id and msg.ofs == offset:
                            # Write data to file
                            data_len = msg.count
                            # Convert data to bytes if it's a list
                            data = msg.data if isinstance(msg.data, bytes) else bytes(msg.data)
                            f.write(data[:data_len])
                            offset += data_len
                            received = True
                            retry_count = 0  # Reset retry counter on success

                            # Call progress callback
                            if progress_callback:
                                progress_callback(offset, total_size)

                            # Print progress
                            progress = (offset / total_size) * 100
                            print(f"\r  Progress: {progress:.1f}% ({offset}/{total_size} bytes)", end='', flush=True)

                            break

                    if not received:
                        retry_count += 1
                        if retry_count >= max_retries:
                            print(f"\n✗ Timeout waiting for data at offset {offset} after {max_retries} retries")
                            return None
                        else:
                            print(f"\n⚠ Retry {retry_count}/{max_retries} at offset {offset}")
                            time.sleep(0.5)
                            continue

                    # Small delay between chunks
                    time.sleep(0.02)

                    # Check if this was the last chunk
                    if msg.count < self.LOG_DATA_CHUNK_SIZE:
                        break

            print(f"\n✓ Log downloaded successfully: {output_file}")
            print(f"  File size: {output_file.stat().st_size} bytes")
            return output_file

        except Exception as e:
            print(f"\n✗ Error downloading log: {e}")
            # Clean up partial file
            if output_file.exists():
                output_file.unlink()
            return None

        finally:
            # Send LOG_REQUEST_END
            self.mav.master.mav.log_request_end_send(
                self.mav.target_system,
                self.mav.target_component
            )

    def download_latest(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[Path]:
        """
        Download most recent log

        Args:
            progress_callback: Progress callback function

        Returns:
            Path to downloaded file
        """
        # Use force_refresh if no cached logs yet
        logs = self.list_logs(force_refresh=(self._cached_logs is None))

        if not logs:
            print("✗ No logs found on drone")
            return None

        # Get latest log (highest time_utc)
        latest = max(logs, key=lambda x: x.time_utc)
        print(f"Latest log: ID {latest.id}, size {latest.size} bytes")

        return self.download_log(latest.id, progress_callback=progress_callback)

    def download_all(self, progress_callback: Optional[Callable[[int, int, int], None]] = None) -> List[Path]:
        """
        Download all logs from drone

        Args:
            progress_callback: Function(log_index, total_logs, bytes_done) called on progress

        Returns:
            List of downloaded file paths
        """
        logs = self.list_logs()

        if not logs:
            print("✗ No logs found on drone")
            return []

        print(f"Downloading {len(logs)} logs...")

        downloaded = []

        for i, log_entry in enumerate(logs, 1):
            print(f"\n[{i}/{len(logs)}] Downloading log {log_entry.id}...")

            def chunk_progress(bytes_done, total_bytes):
                if progress_callback:
                    progress_callback(i, len(logs), bytes_done)

            output_file = self.download_log(log_entry.id, progress_callback=chunk_progress)

            if output_file:
                downloaded.append(output_file)
            else:
                print(f"  ⚠ Failed to download log {log_entry.id}")

        print(f"\n✓ Downloaded {len(downloaded)}/{len(logs)} logs")
        return downloaded

    def erase_all_logs(self, confirm: bool = False) -> bool:
        """
        Erase all logs from drone

        Args:
            confirm: Must be True to actually erase (safety)

        Returns:
            True if successful
        """
        if not confirm:
            print("⚠ Erase not confirmed. Set confirm=True to actually erase logs.")
            return False

        if not self.mav.is_connected():
            print("✗ Not connected to drone")
            return False

        print("⚠ ERASING ALL LOGS FROM DRONE...")

        try:
            self.mav.master.mav.log_erase_send(
                self.mav.target_system,
                self.mav.target_component
            )

            print("✓ Erase command sent")
            print("  Note: Erase may take a few seconds to complete")
            return True

        except Exception as e:
            print(f"✗ Error erasing logs: {e}")
            return False


# Testing
if __name__ == '__main__':
    print("Testing LogDownloader module...\n")
    print("=" * 60)
    print("This test requires a drone connected via USB")
    print("=" * 60)
    print()

    # Create downloader
    downloader = LogDownloader()

    print(f"Download directory: {downloader.download_dir}")
    print()

    # Connect to drone
    if not downloader.connect():
        print("\n✗ Failed to connect to drone")
        print("Make sure:")
        print("  1. Drone is connected to USB")
        print("  2. Correct port in config.yaml")
        print("  3. User has serial port permissions")
        exit(1)

    try:
        # List logs
        print("\n" + "=" * 60)
        print("Listing available logs...")
        print("=" * 60)

        logs = downloader.list_logs()

        if logs:
            print("\nAvailable logs:")
            for log in logs:
                print(f"  {log}")

            # Download latest log
            print("\n" + "=" * 60)
            print("Downloading latest log...")
            print("=" * 60)

            def progress(done, total):
                percent = (done / total) * 100
                bar_len = 40
                filled = int(bar_len * done / total)
                bar = '█' * filled + '░' * (bar_len - filled)
                print(f"\r  [{bar}] {percent:.1f}%", end='', flush=True)

            latest_file = downloader.download_latest(progress_callback=progress)

            if latest_file:
                print(f"\n\n✓ Success! Log saved to:")
                print(f"  {latest_file}")
            else:
                print("\n✗ Failed to download log")
        else:
            print("\n⚠ No logs found on drone")
            print("  Drone may need to fly first to generate logs")

    finally:
        # Disconnect
        print("\n" + "=" * 60)
        downloader.disconnect()
