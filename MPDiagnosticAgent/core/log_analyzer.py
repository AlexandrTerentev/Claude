# -*- coding: utf-8 -*-
"""
Enhanced Log Analyzer for MPDiagnosticAgent
Analyzes Mission Planner logs, telemetry logs (.tlog), and dataflash logs (.bin)

Refactored from engine/log_analyzer.py with Config integration
"""

import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Handle imports for both module and standalone usage
try:
    from .config import Config
except ImportError:
    from config import Config


class LogAnalyzer:
    """
    Unified log analyzer for Mission Planner

    Supports:
    - Mission Planner text logs (.log)
    - Telemetry logs (.tlog) - basic support
    - Dataflash logs (.bin) - basic support (requires pymavlink)
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize log analyzer

        Args:
            config: Configuration object. If None, creates default config
        """
        self.config = config if config else Config()

        # Get log paths from config
        log_paths = self.config.get_log_paths()
        self.log_file_path = log_paths['mp_log']
        self.tlog_dir = log_paths['tlog_dir']
        self.bin_dir = log_paths['bin_dir']

        # Regex patterns for log parsing
        # Format: 2025-12-04 10:47:49,165  INFO MissionPlanner.MainV2 - message
        self.log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+(\w+)\s+([\w.]+)\s+-\s+(.+)'
        )

        # PreArm error pattern
        self.prearm_pattern = re.compile(r'PreArm:\s*(.+)', re.IGNORECASE)

    def get_latest_log_path(self) -> Optional[Path]:
        """
        Get path to the latest Mission Planner log file

        Returns:
            Path to log file or None if not found
        """
        if self.log_file_path and self.log_file_path.exists():
            return self.log_file_path
        return None

    def read_last_lines(self, num_lines: int = 100) -> List[str]:
        """
        Read last N lines from the Mission Planner log file

        Args:
            num_lines: Number of lines to read from end

        Returns:
            List of log lines
        """
        try:
            log_path = self.get_latest_log_path()
            if not log_path:
                return []

            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return lines[-num_lines:] if len(lines) > num_lines else lines
        except Exception as e:
            return [f"Error reading log: {str(e)}"]

    def parse_log_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parse a single log line into components

        Args:
            line: Log line to parse

        Returns:
            Dictionary with parsed components or None if parsing fails
        """
        match = self.log_pattern.match(line)
        if match:
            return {
                'timestamp': match.group(1),
                'level': match.group(2),
                'logger': match.group(3),
                'message': match.group(4)
            }
        return None

    def find_prearm_errors(self, num_lines: int = 200) -> List[Dict[str, str]]:
        """
        Find all PreArm errors in recent log lines

        Args:
            num_lines: Number of recent lines to analyze

        Returns:
            List of PreArm errors with timestamp and message
        """
        lines = self.read_last_lines(num_lines)
        prearm_errors = []

        for line in lines:
            # Check for PreArm messages
            prearm_match = self.prearm_pattern.search(line)
            if prearm_match:
                parsed = self.parse_log_line(line)
                if parsed:
                    prearm_errors.append({
                        'timestamp': parsed['timestamp'],
                        'message': prearm_match.group(1).strip()
                    })
                else:
                    # If parsing fails, just save the message
                    prearm_errors.append({
                        'timestamp': 'Unknown',
                        'message': prearm_match.group(1).strip()
                    })

        return prearm_errors

    def find_errors(self, num_lines: int = 200, levels: List[str] = None) -> List[Dict[str, str]]:
        """
        Find ERROR and CRITICAL level messages

        Args:
            num_lines: Number of recent lines to analyze
            levels: List of log levels to search for (default: ['ERROR', 'CRITICAL'])

        Returns:
            List of error entries
        """
        if levels is None:
            levels = ['ERROR', 'CRITICAL']

        lines = self.read_last_lines(num_lines)
        errors = []

        for line in lines:
            parsed = self.parse_log_line(line)
            if parsed and parsed['level'] in levels:
                errors.append({
                    'timestamp': parsed['timestamp'],
                    'level': parsed['level'],
                    'logger': parsed['logger'],
                    'message': parsed['message']
                })

        return errors

    def get_recent_logs(self, num_lines: int = 10) -> str:
        """
        Get recent log entries formatted for display

        Args:
            num_lines: Number of recent lines to retrieve

        Returns:
            Formatted log entries
        """
        lines = self.read_last_lines(num_lines)

        if not lines:
            return "No log entries found"

        formatted_lines = []
        for line in lines:
            parsed = self.parse_log_line(line)
            if parsed:
                # Shorten timestamp
                time_only = parsed['timestamp'].split()[1]  # Get only HH:MM:SS part
                formatted_lines.append(f"[{time_only}] {parsed['level']}: {parsed['message']}")
            else:
                # If parsing fails, show raw line
                formatted_lines.append(line.strip())

        return '\n'.join(formatted_lines)

    def check_connection_status(self) -> tuple[Optional[bool], str]:
        """
        Check if drone is connected based on recent logs

        Returns:
            Tuple of (is_connected, message)
        """
        lines = self.read_last_lines(50)

        # Look for connection indicators
        for line in reversed(lines):
            if 'connected' in line.lower():
                return True, "Drone appears to be connected"
            elif 'disconnected' in line.lower() or 'not connected' in line.lower():
                return False, "Drone appears to be disconnected"

        return None, "Connection status unclear from logs"

    def summarize_issues(self) -> str:
        """
        Provide a summary of issues found in logs

        Returns:
            Summary text
        """
        # Use config setting for number of lines
        num_lines = self.config.log_lines_to_analyze

        prearm_errors = self.find_prearm_errors(num_lines)
        errors = self.find_errors(num_lines)

        summary = []

        if prearm_errors:
            summary.append(f"Found {len(prearm_errors)} PreArm error(s):")
            # Show unique errors only
            unique_errors = list(set([e['message'] for e in prearm_errors]))
            for err in unique_errors[:3]:  # Show last 3
                summary.append(f"  - {err}")

        if errors:
            summary.append(f"\nFound {len(errors)} critical error(s):")
            for err in errors[-3:]:  # Show last 3
                summary.append(f"  - [{err['level']}] {err['message']}")

        if not prearm_errors and not errors:
            summary.append("✓ No critical issues found in recent logs")

        return '\n'.join(summary)

    def get_unique_prearm_errors(self) -> List[str]:
        """
        Get list of unique PreArm error messages

        Returns:
            List of unique error messages
        """
        prearm_errors = self.find_prearm_errors()
        unique = list(set([e['message'] for e in prearm_errors]))
        return unique

    def analyze_tlog(self, tlog_file: Path) -> Dict[str, Any]:
        """
        Analyze telemetry log file (.tlog)

        Args:
            tlog_file: Path to .tlog file

        Returns:
            Analysis results (basic implementation)

        Note: Requires pymavlink for full implementation
        """
        if not tlog_file.exists():
            return {'error': 'File not found'}

        # Basic file info
        return {
            'file': str(tlog_file),
            'size': tlog_file.stat().st_size,
            'modified': datetime.fromtimestamp(tlog_file.stat().st_mtime).isoformat(),
            'note': 'Full .tlog analysis requires pymavlink (to be implemented)'
        }

    def analyze_bin(self, bin_file: Path) -> Dict[str, Any]:
        """
        Analyze dataflash log file (.bin)

        Args:
            bin_file: Path to .bin file

        Returns:
            Analysis results (basic implementation)

        Note: Requires pymavlink DFReader for full implementation
        """
        if not bin_file.exists():
            return {'error': 'File not found'}

        # Basic file info
        return {
            'file': str(bin_file),
            'size': bin_file.stat().st_size,
            'modified': datetime.fromtimestamp(bin_file.stat().st_mtime).isoformat(),
            'note': 'Full .bin analysis requires pymavlink DFReader (to be implemented)'
        }

    def list_available_logs(self) -> Dict[str, List[Path]]:
        """
        List all available log files

        Returns:
            Dictionary with lists of different log types
        """
        result = {
            'mp_logs': [],
            'tlogs': [],
            'bin_logs': []
        }

        # Mission Planner logs
        if self.log_file_path and self.log_file_path.exists():
            result['mp_logs'].append(self.log_file_path)

            # Check for rotation logs
            parent = self.log_file_path.parent
            stem = self.log_file_path.stem
            for i in range(1, 10):
                rotation_log = parent / f"{stem}.{i}"
                if rotation_log.exists():
                    result['mp_logs'].append(rotation_log)

        # Telemetry logs
        if self.tlog_dir and self.tlog_dir.exists():
            result['tlogs'] = list(self.tlog_dir.glob('*.tlog'))

        # Dataflash logs
        if self.bin_dir and self.bin_dir.exists():
            result['bin_logs'] = list(self.bin_dir.glob('*.bin'))

        return result


# Testing
if __name__ == '__main__':
    print("Testing LogAnalyzer module...\n")

    # Create analyzer with default config
    analyzer = LogAnalyzer()

    print("=" * 60)
    print("Testing Mission Planner Log Analysis")
    print("=" * 60)

    # Test recent logs
    print("\n1. Recent Logs (last 5 lines):")
    print("-" * 60)
    print(analyzer.get_recent_logs(5))

    # Test PreArm errors
    print("\n2. PreArm Errors:")
    print("-" * 60)
    prearm = analyzer.find_prearm_errors()
    if prearm:
        unique = analyzer.get_unique_prearm_errors()
        for err in unique[:3]:
            print(f"  ❌ {err}")
    else:
        print("  ✓ No PreArm errors found")

    # Test issues summary
    print("\n3. Issues Summary:")
    print("-" * 60)
    print(analyzer.summarize_issues())

    # Test available logs
    print("\n4. Available Logs:")
    print("-" * 60)
    logs = analyzer.list_available_logs()
    print(f"  MP logs: {len(logs['mp_logs'])}")
    print(f"  Telemetry logs: {len(logs['tlogs'])}")
    print(f"  Dataflash logs: {len(logs['bin_logs'])}")

    print("\n" + "=" * 60)
