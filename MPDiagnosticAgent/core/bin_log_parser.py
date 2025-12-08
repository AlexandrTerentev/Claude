#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binary Log Parser for MPDiagnosticAgent
Parses .bin dataflash logs from ArduPilot
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re

# Try to import pymavlink
try:
    from pymavlink import mavutil
    PYMAVLINK_AVAILABLE = True
except ImportError:
    PYMAVLINK_AVAILABLE = False
    print("⚠️ pymavlink not available - .bin parsing disabled")


class BinLogParser:
    """
    Parser for ArduPilot .bin (dataflash) logs
    Extracts PreArm errors and other diagnostic info
    """

    def __init__(self):
        """Initialize parser"""
        self.current_log = None
        self.mlog = None

    def parse_log(self, log_path: Path) -> Dict[str, Any]:
        """
        Parse a .bin log file

        Args:
            log_path: Path to .bin file

        Returns:
            Dictionary with parsed data
        """
        if not PYMAVLINK_AVAILABLE:
            return {
                'error': 'pymavlink not installed',
                'prearm_errors': [],
                'events': [],
                'messages': []
            }

        if not log_path.exists():
            return {
                'error': f'File not found: {log_path}',
                'prearm_errors': [],
                'events': [],
                'messages': []
            }

        result = {
            'file': str(log_path),
            'prearm_errors': [],
            'events': [],
            'messages': [],
            'errors': [],
            'parameters': {},
            'stats': {},
            'technical': {
                'vibrations': [],
                'motors': [],
                'gps': [],
                'attitude': [],
                'pid': []
            }
        }

        try:
            # Open log with mavutil
            print(f"📖 Parsing {log_path.name}...")
            self.mlog = mavutil.mavlink_connection(str(log_path))

            message_count = 0
            prearm_found = 0
            error_found = 0

            # Counters for technical data
            msg_type_counts = {}

            # Read all messages
            while True:
                msg = self.mlog.recv_match(blocking=False)
                if msg is None:
                    break

                message_count += 1
                msg_type = msg.get_type()

                # Count message types
                msg_type_counts[msg_type] = msg_type_counts.get(msg_type, 0) + 1

                # Extract different message types
                if msg_type == 'MSG':
                    # Text messages (includes PreArm)
                    text = getattr(msg, 'Message', '')

                    if 'PreArm' in text or 'prearm' in text.lower():
                        result['prearm_errors'].append({
                            'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,  # Convert to seconds
                            'text': text,
                            'type': 'prearm'
                        })
                        prearm_found += 1

                    result['messages'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'text': text
                    })

                elif msg_type == 'ERR':
                    # Error messages
                    subsys = getattr(msg, 'Subsys', 0)
                    ecode = getattr(msg, 'ECode', 0)

                    result['errors'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'subsystem': subsys,
                        'error_code': ecode,
                        'description': self._decode_error(subsys, ecode)
                    })
                    error_found += 1

                elif msg_type == 'EV':
                    # Events
                    event_id = getattr(msg, 'Id', 0)
                    result['events'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'id': event_id,
                        'description': self._decode_event(event_id)
                    })

                elif msg_type == 'PARM':
                    # Parameters
                    name = getattr(msg, 'Name', '')
                    value = getattr(msg, 'Value', 0)
                    result['parameters'][name] = value

                # TECHNICAL DATA COLLECTION
                elif msg_type == 'VIBE':
                    # Vibration data
                    result['technical']['vibrations'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'VibeX': getattr(msg, 'VibeX', 0),
                        'VibeY': getattr(msg, 'VibeY', 0),
                        'VibeZ': getattr(msg, 'VibeZ', 0),
                        'Clip0': getattr(msg, 'Clip0', 0),
                        'Clip1': getattr(msg, 'Clip1', 0),
                        'Clip2': getattr(msg, 'Clip2', 0)
                    })

                elif msg_type == 'RCOU':
                    # Motor/servo outputs
                    result['technical']['motors'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'C1': getattr(msg, 'C1', 0),
                        'C2': getattr(msg, 'C2', 0),
                        'C3': getattr(msg, 'C3', 0),
                        'C4': getattr(msg, 'C4', 0)
                    })

                elif msg_type == 'GPS':
                    # GPS data
                    result['technical']['gps'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'Status': getattr(msg, 'Status', 0),
                        'NSats': getattr(msg, 'NSats', 0),
                        'HDop': getattr(msg, 'HDop', 9999) / 100.0,  # Convert to float
                        'Spd': getattr(msg, 'Spd', 0)
                    })

                elif msg_type == 'ATT':
                    # Attitude data
                    result['technical']['attitude'].append({
                        'timestamp': getattr(msg, 'TimeUS', 0) / 1000000,
                        'Roll': getattr(msg, 'Roll', 0),
                        'Pitch': getattr(msg, 'Pitch', 0),
                        'Yaw': getattr(msg, 'Yaw', 0)
                    })

            result['stats'] = {
                'total_messages': message_count,
                'prearm_errors': prearm_found,
                'errors': error_found,
                'events': len(result['events']),
                'parameters': len(result['parameters']),
                'message_types': msg_type_counts
            }

            print(f"  ✓ Parsed {message_count} messages")
            print(f"  ✓ Found {prearm_found} PreArm errors")
            print(f"  ✓ Found {error_found} error messages")

            return result

        except Exception as e:
            print(f"  ✗ Error parsing log: {e}")
            result['error'] = str(e)
            return result

        finally:
            if self.mlog:
                self.mlog.close()

    def _decode_error(self, subsys: int, ecode: int) -> str:
        """Decode error subsystem and code"""
        subsystems = {
            1: "Main",
            2: "Radio",
            3: "Compass",
            4: "Optical Flow",
            5: "Throttle Failsafe",
            6: "Battery Failsafe",
            7: "GPS Failsafe",
            8: "GCS Failsafe",
            9: "Fence",
            10: "Flight Mode",
            11: "GPS",
            12: "Crash Check",
            13: "Flip",
            14: "Autotune",
            15: "Parachute",
            16: "EKF/Inertial Nav",
            17: "Failsafe Radio",
            18: "Failsafe Battery",
            19: "Failsafe GCS",
            20: "Failsafe EKF"
        }

        subsys_name = subsystems.get(subsys, f"Unknown({subsys})")
        return f"{subsys_name} Error {ecode}"

    def _decode_event(self, event_id: int) -> str:
        """Decode event ID"""
        events = {
            10: "Armed",
            11: "Disarmed",
            15: "Auto Armed",
            17: "Land Complete Maybe",
            18: "Land Complete",
            28: "Not Landed",
            25: "Set Home",
            43: "EKF Alt Reset",
            63: "EKF Yaw Reset"
        }

        return events.get(event_id, f"Event {event_id}")

    def find_latest_bin_log(self, log_dir: Path) -> Optional[Path]:
        """
        Find latest .bin log in directory

        Args:
            log_dir: Directory to search

        Returns:
            Path to latest .bin file or None
        """
        if not log_dir.exists():
            return None

        bin_files = list(log_dir.glob("*.bin"))
        if not bin_files:
            return None

        # Sort by modification time
        bin_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return bin_files[0]

    def extract_prearm_from_directory(self, log_dir: Path, max_logs: int = 3) -> List[Dict[str, Any]]:
        """
        Extract PreArm errors from recent .bin logs in directory

        Args:
            log_dir: Directory with .bin files
            max_logs: Maximum number of logs to check

        Returns:
            List of PreArm errors from all checked logs
        """
        all_prearms = []

        if not log_dir.exists():
            print(f"⚠️ Directory not found: {log_dir}")
            return all_prearms

        # Find .bin files
        bin_files = list(log_dir.glob("*.bin"))
        if not bin_files:
            print(f"ℹ️ No .bin files in {log_dir}")
            return all_prearms

        # Sort by modification time (newest first)
        bin_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        print(f"\n📁 Checking {min(len(bin_files), max_logs)} recent .bin logs...")

        # Parse recent logs
        for log_file in bin_files[:max_logs]:
            result = self.parse_log(log_file)

            if result['prearm_errors']:
                for prearm in result['prearm_errors']:
                    prearm['source_file'] = log_file.name
                    all_prearms.append(prearm)

        print(f"✓ Total PreArm errors found: {len(all_prearms)}")
        return all_prearms


# Testing
if __name__ == '__main__':
    print("Testing BinLogParser module...")
    print("=" * 60)

    parser = BinLogParser()

    # Test with Mission Planner logs
    log_dir = Path.home() / ".local/share/Mission Planner/logs/QUADROTOR/1"

    if log_dir.exists():
        print(f"\n📂 Searching in: {log_dir}")

        # Find latest log
        latest = parser.find_latest_bin_log(log_dir)
        if latest:
            print(f"📄 Latest log: {latest.name}")

            # Parse it
            result = parser.parse_log(latest)

            print(f"\n📊 Statistics:")
            print(f"  Messages: {result['stats']['total_messages']}")
            print(f"  PreArm errors: {result['stats']['prearm_errors']}")
            print(f"  Errors: {result['stats']['errors']}")
            print(f"  Events: {result['stats']['events']}")

            if result['prearm_errors']:
                print(f"\n⚠️ PreArm Errors:")
                for i, err in enumerate(result['prearm_errors'][:5], 1):
                    print(f"  {i}. {err['text']}")

        # Extract from multiple logs
        print(f"\n{'='*60}")
        print("Testing extract from multiple logs...")
        all_prearms = parser.extract_prearm_from_directory(log_dir, max_logs=3)

        if all_prearms:
            print(f"\n📋 All PreArm errors from recent logs:")
            for i, err in enumerate(all_prearms[:10], 1):
                print(f"  {i}. [{err['source_file']}] {err['text']}")
    else:
        print(f"⚠️ Log directory not found: {log_dir}")

    print("\n" + "=" * 60)
    print("✓ Tests complete")
