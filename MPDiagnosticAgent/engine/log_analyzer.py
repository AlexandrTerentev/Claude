# -*- coding: utf-8 -*-
"""
Log Analyzer for Mission Planner Diagnostic Agent
Parses Mission Planner logs to find errors, PreArm messages, and issues
"""

import re
import os
from datetime import datetime


class LogAnalyzer:
    """Analyzes Mission Planner log files"""

    def __init__(self, log_base_path='/home/user_1/missionplanner'):
        self.log_base_path = log_base_path
        self.log_file_path = os.path.join(log_base_path, 'Mission Planner', 'MissionPlanner.log')

        # Regex patterns for log parsing
        # Format: 2025-12-04 10:47:49,165  INFO MissionPlanner.MainV2 - message
        self.log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+(\w+)\s+([\w.]+)\s+-\s+(.+)'
        )

        # PreArm error pattern
        self.prearm_pattern = re.compile(r'PreArm:\s*(.+)', re.IGNORECASE)

    def get_latest_log_path(self):
        """Return path to the latest Mission Planner log file"""
        if os.path.exists(self.log_file_path):
            return self.log_file_path
        return None

    def read_last_lines(self, num_lines=100):
        """Read last N lines from the log file"""
        try:
            log_path = self.get_latest_log_path()
            if not log_path:
                return []

            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return lines[-num_lines:] if len(lines) > num_lines else lines
        except Exception as e:
            return [f"Error reading log: {str(e)}"]

    def parse_log_line(self, line):
        """Parse a single log line into components"""
        match = self.log_pattern.match(line)
        if match:
            return {
                'timestamp': match.group(1),
                'level': match.group(2),
                'logger': match.group(3),
                'message': match.group(4)
            }
        return None

    def find_prearm_errors(self, num_lines=200):
        """Find all PreArm errors in recent log lines"""
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

    def find_errors(self, num_lines=200, levels=['ERROR', 'CRITICAL']):
        """Find ERROR and CRITICAL level messages"""
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

    def get_recent_logs(self, num_lines=10):
        """Get recent log entries formatted for display"""
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

    def check_connection_status(self):
        """Check if drone is connected based on recent logs"""
        lines = self.read_last_lines(50)

        # Look for connection indicators
        for line in reversed(lines):
            if 'connected' in line.lower():
                return True, "Drone appears to be connected"
            elif 'disconnected' in line.lower() or 'not connected' in line.lower():
                return False, "Drone appears to be disconnected"

        return None, "Connection status unclear from logs"

    def summarize_issues(self):
        """Provide a summary of issues found in logs"""
        prearm_errors = self.find_prearm_errors()
        errors = self.find_errors()

        summary = []

        if prearm_errors:
            summary.append(f"Found {len(prearm_errors)} PreArm error(s):")
            for err in prearm_errors[-3:]:  # Show last 3
                summary.append(f"  - {err['message']}")

        if errors:
            summary.append(f"\nFound {len(errors)} critical error(s):")
            for err in errors[-3:]:  # Show last 3
                summary.append(f"  - [{err['level']}] {err['message']}")

        if not prearm_errors and not errors:
            summary.append("No critical issues found in recent logs")

        return '\n'.join(summary)


# Test function
if __name__ == '__main__':
    analyzer = LogAnalyzer()
    print("Testing LogAnalyzer...")
    print("\n=== Recent Logs ===")
    print(analyzer.get_recent_logs(5))
    print("\n=== PreArm Errors ===")
    print(analyzer.find_prearm_errors())
    print("\n=== Issues Summary ===")
    print(analyzer.summarize_issues())
