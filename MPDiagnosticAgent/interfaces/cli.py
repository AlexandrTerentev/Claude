#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MPDiagnosticAgent - Command Line Interface
Provides command-line access to all diagnostic functions

Usage:
    mpdiag status                      # Full status check
    mpdiag motors                      # Diagnose motors
    mpdiag download --latest           # Download latest log
    mpdiag download --list             # List logs on drone
    mpdiag analyze FILE                # Analyze log file
    mpdiag wiki TOPIC                  # Search Wiki
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.diagnostic_engine import DiagnosticEngine
from core.log_downloader import LogDownloader
from core.config import Config


class MPDCLI:
    """Command-line interface for MPDiagnosticAgent"""

    def __init__(self, language: str = 'auto'):
        """
        Initialize CLI

        Args:
            language: Preferred language ('ru', 'en', or 'auto')
        """
        self.config = Config()
        self.engine = DiagnosticEngine(config=self.config, language=language)
        self.downloader: Optional[LogDownloader] = None

    def cmd_status(self, args):
        """Full status check"""
        print(self.engine.process_query('status'))
        return 0

    def cmd_motors(self, args):
        """Diagnose motor issues"""
        print(self.engine.process_query('motors'))
        return 0

    def cmd_vibrations(self, args):
        """Analyze vibrations"""
        print(self.engine.process_query('vibrations'))
        return 0

    def cmd_compass(self, args):
        """Diagnose compass"""
        print(self.engine.process_query('compass'))
        return 0

    def cmd_prearm(self, args):
        """Check PreArm errors"""
        print(self.engine.process_query('prearm'))
        return 0

    def cmd_errors(self, args):
        """Check for errors in logs"""
        print(self.engine.process_query('check errors'))
        return 0

    def cmd_logs(self, args):
        """Show recent logs"""
        print(self.engine.process_query('show logs'))
        return 0

    def cmd_calibration(self, args):
        """Show calibration guide"""
        print(self.engine.process_query('calibration'))
        return 0

    def cmd_wiki(self, args):
        """Search ArduPilot Wiki"""
        topic = args.topic
        print(self.engine.process_query(f'wiki {topic}'))
        return 0

    def cmd_query(self, args):
        """Process custom query"""
        query = args.query
        print(self.engine.process_query(query))
        return 0

    def cmd_download(self, args):
        """Download logs from drone"""
        # Auto-detect port if not specified
        port = args.port or self.config.mavlink_port

        # Try to find available ports if configured port doesn't exist
        from core.mavlink_interface import MAVLinkInterface
        available_ports = MAVLinkInterface.find_available_ports()

        if available_ports:
            print(f"Found available ports: {', '.join(available_ports)}")
            if port not in available_ports and available_ports:
                print(f"⚠ Configured port {port} not found, trying {available_ports[0]}")
                port = available_ports[0]

        print(f"Connecting to drone on {port}...")

        try:
            self.downloader = LogDownloader(config=self.config)
            # Override port with detected one
            self.downloader.mav.connection_string = port

            if not self.downloader.connect():
                print("✗ Failed to connect to drone")
                print("  Check:")
                print(f"    1. Drone is connected (available ports: {available_ports or 'none'})")
                print("    2. Correct port in config.yaml")
                print("    3. User has serial port permissions")
                return 1

            print("✓ Connected to drone")

            # List logs
            if args.list:
                print("\nListing logs on drone...")
                logs = self.downloader.list_logs()

                if logs:
                    print(f"\nFound {len(logs)} logs:\n")
                    for i, log in enumerate(logs, 1):
                        size_kb = log.size / 1024
                        print(f"  {i}. Log ID {log.id}: {size_kb:.1f} KB")
                else:
                    print("⚠ No logs found on drone")

                return 0

            # Download latest
            if args.latest:
                print("\nDownloading latest log...")

                def progress(done, total):
                    percent = (done / total) * 100
                    bar_len = 50
                    filled = int(bar_len * done / total)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    print(f"\r  [{bar}] {percent:.1f}% ({done}/{total} bytes)", end='', flush=True)

                log_file = self.downloader.download_latest(progress_callback=progress)

                if log_file:
                    print(f"\n\n✓ Download successful!")
                    print(f"  File: {log_file}")
                    print(f"  Size: {log_file.stat().st_size} bytes")
                    return 0
                else:
                    print("\n✗ Download failed")
                    return 1

            # Download specific log ID
            if args.log_id is not None:
                print(f"\nDownloading log {args.log_id}...")

                def progress(done, total):
                    percent = (done / total) * 100
                    bar_len = 50
                    filled = int(bar_len * done / total)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    print(f"\r  [{bar}] {percent:.1f}%", end='', flush=True)

                log_file = self.downloader.download_log(args.log_id, progress_callback=progress)

                if log_file:
                    print(f"\n\n✓ Download successful!")
                    print(f"  File: {log_file}")
                    return 0
                else:
                    print("\n✗ Download failed")
                    return 1

            # No action specified
            print("✗ Specify --list, --latest, or --log-id ID")
            return 1

        except Exception as e:
            print(f"✗ Error: {e}")
            return 1

        finally:
            if self.downloader:
                self.downloader.disconnect()

    def cmd_analyze(self, args):
        """Analyze log file"""
        log_file = Path(args.file)

        if not log_file.exists():
            print(f"✗ File not found: {log_file}")
            return 1

        print(f"Analyzing: {log_file}\n")

        # Check file type
        if log_file.suffix == '.bin':
            print("⚠ Full .bin analysis requires pymavlink extras")
            print("  For now, showing basic info...")
            print(f"\n  File size: {log_file.stat().st_size} bytes")
            print("\nUse Mission Planner or MAVProxy for full .bin analysis")
            return 0

        elif log_file.suffix == '.log':
            # Analyze Mission Planner log
            # This would use LogAnalyzer directly
            print("Mission Planner log analysis...")
            print("Use: mpdiag errors")
            print("     mpdiag prearm")
            return 0

        elif log_file.suffix == '.tlog':
            print("⚠ .tlog analysis requires mavlogdump")
            print(f"\n  File size: {log_file.stat().st_size} bytes")
            return 0

        else:
            print(f"✗ Unknown file type: {log_file.suffix}")
            print("  Supported: .bin, .log, .tlog")
            return 1

    def cmd_config(self, args):
        """Show configuration"""
        print("CONFIGURATION:")
        print("=" * 60)
        print(f"\nConfig file: {self.config.config_file}")
        mp_path = self.config.config.get('mission_planner', {}).get('auto_detect_path', 'auto-detect')
        print(f"Mission Planner: {mp_path}")
        print(f"\nLog paths:")
        log_paths = self.config.get_log_paths()
        for key, value in log_paths.items():
            print(f"  {key}: {value}")
        print(f"\nMAVLink:")
        print(f"  Port: {self.config.mavlink_port}")
        mavlink_cfg = self.config.config.get('mavlink', {})
        print(f"  Baudrate: {mavlink_cfg.get('baudrate', 'N/A')}")
        print(f"  Timeout: {mavlink_cfg.get('timeout', 'N/A')}s")
        return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='MPDiagnosticAgent - ArduPilot Diagnostic Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mpdiag status                  # Full drone status
  mpdiag motors                  # Diagnose motor issues
  mpdiag download --latest       # Download latest log from drone
  mpdiag download --list         # List logs on drone
  mpdiag wiki prearm             # Search Wiki for PreArm info
  mpdiag query "why won't motors spin?"  # Custom query
  mpdiag config                  # Show configuration
        """
    )

    parser.add_argument('--language', choices=['ru', 'en', 'auto'], default='auto',
                       help='Interface language (default: auto)')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Status command
    subparsers.add_parser('status', help='Full drone status check')

    # Motors command
    subparsers.add_parser('motors', help='Diagnose motor/arming issues')

    # Vibrations command
    subparsers.add_parser('vibrations', help='Analyze vibrations')

    # Compass command
    subparsers.add_parser('compass', help='Diagnose compass')

    # PreArm command
    subparsers.add_parser('prearm', help='Check PreArm errors')

    # Errors command
    subparsers.add_parser('errors', help='Check for errors in logs')

    # Logs command
    subparsers.add_parser('logs', help='Show recent log entries')

    # Calibration command
    subparsers.add_parser('calibration', help='Show calibration guide')

    # Wiki command
    wiki_parser = subparsers.add_parser('wiki', help='Search ArduPilot Wiki')
    wiki_parser.add_argument('topic', help='Topic to search')

    # Query command
    query_parser = subparsers.add_parser('query', help='Process custom query')
    query_parser.add_argument('query', help='Question or command')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download logs from drone')
    download_parser.add_argument('--port', help='Serial port (default: from config)')
    download_group = download_parser.add_mutually_exclusive_group()
    download_group.add_argument('--list', action='store_true', help='List logs on drone')
    download_group.add_argument('--latest', action='store_true', help='Download latest log')
    download_group.add_argument('--log-id', type=int, help='Download specific log ID')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze log file')
    analyze_parser.add_argument('file', help='Log file to analyze')

    # Config command
    subparsers.add_parser('config', help='Show configuration')

    # Parse arguments
    args = parser.parse_args()

    # If no command, show help
    if not args.command:
        parser.print_help()
        return 0

    # Create CLI instance
    cli = MPDCLI(language=args.language)

    # Route to appropriate command
    command_map = {
        'status': cli.cmd_status,
        'motors': cli.cmd_motors,
        'vibrations': cli.cmd_vibrations,
        'compass': cli.cmd_compass,
        'prearm': cli.cmd_prearm,
        'errors': cli.cmd_errors,
        'logs': cli.cmd_logs,
        'calibration': cli.cmd_calibration,
        'wiki': cli.cmd_wiki,
        'query': cli.cmd_query,
        'download': cli.cmd_download,
        'analyze': cli.cmd_analyze,
        'config': cli.cmd_config,
    }

    cmd_func = command_map.get(args.command)
    if cmd_func:
        try:
            return cmd_func(args)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            return 130
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print(f"✗ Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
