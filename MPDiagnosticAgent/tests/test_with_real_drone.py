#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for MAVLink interface and log downloader with real drone

Usage:
    python3 tests/test_with_real_drone.py
    python3 tests/test_with_real_drone.py --list-only
    python3 tests/test_with_real_drone.py --download-latest
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mavlink_interface import MAVLinkInterface
from core.log_downloader import LogDownloader
from core.config import Config


def test_connection():
    """Test basic MAVLink connection"""
    print("\n" + "="*60)
    print("TEST 1: MAVLink Connection")
    print("="*60)

    mav = MAVLinkInterface()

    print(f"\nConnection string: {mav.connection_string}")
    print(f"Baudrate: {mav.baudrate}")

    if mav.connect(verbose=True):
        print("\n✓ Connection test PASSED")

        # Get system status
        print("\nGetting system status...")
        status = mav.get_system_status()

        if status:
            print("\nSystem Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")

        mav.disconnect()
        return True
    else:
        print("\n✗ Connection test FAILED")
        return False


def test_list_logs():
    """Test listing logs on drone"""
    print("\n" + "="*60)
    print("TEST 2: List Logs")
    print("="*60)

    downloader = LogDownloader()

    if not downloader.connect():
        print("✗ Failed to connect to drone")
        return False

    logs = downloader.list_logs()

    if logs:
        print(f"\n✓ Found {len(logs)} logs:")
        for i, log in enumerate(logs, 1):
            size_kb = log.size / 1024
            print(f"  {i}. Log ID {log.id}: {size_kb:.1f} KB")

        downloader.disconnect()
        return True
    else:
        print("\n⚠ No logs found on drone")
        print("  This is OK if drone hasn't flown yet")
        downloader.disconnect()
        return True


def test_download_latest():
    """Test downloading latest log"""
    print("\n" + "="*60)
    print("TEST 3: Download Latest Log")
    print("="*60)

    downloader = LogDownloader()

    if not downloader.connect():
        print("✗ Failed to connect to drone")
        return False

    # Progress callback
    def progress(done, total):
        percent = (done / total) * 100
        bar_len = 40
        filled = int(bar_len * done / total)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"\r  [{bar}] {percent:.1f}% ({done}/{total} bytes)", end='', flush=True)

    log_file = downloader.download_latest(progress_callback=progress)

    print()  # New line after progress bar

    downloader.disconnect()

    if log_file:
        print(f"\n✓ Download test PASSED")
        print(f"  File: {log_file}")
        print(f"  Size: {log_file.stat().st_size} bytes")
        return True
    else:
        print("\n✗ Download test FAILED")
        return False


def test_parameters():
    """Test reading parameters"""
    print("\n" + "="*60)
    print("TEST 4: Read Parameters")
    print("="*60)

    mav = MAVLinkInterface()

    if not mav.connect(verbose=False):
        print("✗ Failed to connect to drone")
        return False

    print("\nReading selected parameters...")
    params = mav.get_parameters(['SYSID_THISMAV', 'FRAME_TYPE', 'ARMING_CHECK'])

    if params:
        print("\nParameters:")
        for name, value in params.items():
            print(f"  {name}: {value}")

        mav.disconnect()
        print("\n✓ Parameter test PASSED")
        return True
    else:
        print("\n✗ No parameters received")
        mav.disconnect()
        return False


def main():
    """Run all tests"""
    import argparse

    parser = argparse.ArgumentParser(description='Test MPDiagnosticAgent with real drone')
    parser.add_argument('--list-only', action='store_true', help='Only list logs, do not download')
    parser.add_argument('--download-latest', action='store_true', help='Download latest log')
    parser.add_argument('--all', action='store_true', help='Run all tests')

    args = parser.parse_args()

    print("="*60)
    print("MPDiagnosticAgent - Real Drone Testing")
    print("="*60)
    print("\n⚠ Make sure drone is connected via USB!")
    print("⚠ Default port: /dev/ttyUSB0 (check config.yaml)")
    print()

    # Check config
    config = Config()
    config.print_summary()

    results = []

    if args.list_only:
        # Only list logs
        results.append(("List Logs", test_list_logs()))

    elif args.download_latest:
        # List and download
        results.append(("List Logs", test_list_logs()))
        results.append(("Download Latest", test_download_latest()))

    elif args.all:
        # Run all tests
        results.append(("Connection", test_connection()))
        results.append(("List Logs", test_list_logs()))
        results.append(("Parameters", test_parameters()))
        results.append(("Download Latest", test_download_latest()))

    else:
        # Default: connection and list
        results.append(("Connection", test_connection()))
        results.append(("List Logs", test_list_logs()))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{len(results)} tests passed")
    print("="*60)

    return passed == len(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
