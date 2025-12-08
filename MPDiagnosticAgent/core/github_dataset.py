#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Dataset Loader for MPDiagnosticAgent
Downloads and searches ArduPilot documentation from GitHub
"""

import subprocess
from pathlib import Path
import os

class GitHubDataset:
    """
    Load ArduPilot Wiki/documentation from GitHub for AI context
    """

    def __init__(self):
        """Initialize GitHub dataset loader"""
        self.cache_dir = Path.home() / ".mpdiag" / "docs"
        self.wiki_dir = self.cache_dir / "ardupilot_wiki"
        self.wiki_url = "https://github.com/ArduPilot/ardupilot_wiki.git"

        # Hardcoded important documentation links (faster than cloning whole wiki)
        self.doc_links = {
            'battery': 'https://ardupilot.org/copter/docs/common-powermodule-landingpage.html',
            'rc': 'https://ardupilot.org/copter/docs/common-rc-systems.html',
            'gps': 'https://ardupilot.org/copter/docs/common-gps-how-it-works.html',
            'compass': 'https://ardupilot.org/copter/docs/common-compass-setup-advanced.html',
            'ekf': 'https://ardupilot.org/copter/docs/ekf-inav-failsafe.html',
            'prearm': 'https://ardupilot.org/copter/docs/prearm_safety_check.html',
            'calibration': 'https://ardupilot.org/copter/docs/common-compass-calibration-in-mission-planner.html',
            'failsafe': 'https://ardupilot.org/copter/docs/failsafe-landing-page.html',
            'tuning': 'https://ardupilot.org/copter/docs/tuning.html',
        }

    def download_docs(self, force_update: bool = False) -> bool:
        """
        Clone or update ArduPilot Wiki

        Args:
            force_update: Force git pull even if already cloned

        Returns:
            True if successful
        """
        try:
            # Create cache directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            if not self.wiki_dir.exists():
                # Clone wiki
                print(f"📥 Downloading ArduPilot Wiki to {self.wiki_dir}...")
                result = subprocess.run(
                    ["git", "clone", "--depth=1", self.wiki_url, str(self.wiki_dir)],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 min timeout
                )

                if result.returncode == 0:
                    print("✅ Wiki downloaded successfully")
                    return True
                else:
                    print(f"❌ Failed to clone wiki: {result.stderr}")
                    return False

            elif force_update:
                # Update existing wiki
                print("🔄 Updating ArduPilot Wiki...")
                result = subprocess.run(
                    ["git", "-C", str(self.wiki_dir), "pull"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    print("✅ Wiki updated")
                    return True
                else:
                    print(f"⚠️ Failed to update: {result.stderr}")
                    return False
            else:
                print(f"✓ Wiki already exists at {self.wiki_dir}")
                return True

        except subprocess.TimeoutExpired:
            print("❌ Timeout downloading wiki")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def search(self, query: str, max_results: int = 3, context_lines: int = 2) -> str:
        """
        Search for query in documentation

        Args:
            query: Search term
            max_results: Maximum number of results
            context_lines: Lines of context around match

        Returns:
            Search results as formatted string
        """
        if not self.wiki_dir.exists():
            return "⚠️ Wiki not downloaded. Run download_docs() first."

        try:
            # Search with grep
            result = subprocess.run(
                [
                    "grep", "-r", "-i",  # Recursive, case-insensitive
                    f"-C{context_lines}",  # Context lines
                    "--include=*.md",  # Only markdown files
                    "--include=*.rst",  # And RST files
                    query,
                    str(self.wiki_dir)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )

            if not result.stdout:
                return f"ℹ️ No documentation found for '{query}'"

            # Parse and format results
            lines = result.stdout.split('\n')
            formatted_results = []
            current_file = None
            result_count = 0

            for line in lines[:50]:  # Limit to first 50 lines
                if '--' in line:  # Separator between matches
                    continue

                if ':' in line:
                    # Extract filename and content
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        file_path = parts[0]
                        content = ':'.join(parts[1:])

                        # Get relative path
                        rel_path = Path(file_path).relative_to(self.wiki_dir)

                        if str(rel_path) != current_file:
                            if result_count >= max_results:
                                break
                            current_file = str(rel_path)
                            result_count += 1
                            formatted_results.append(f"\n📄 {rel_path}")

                        formatted_results.append(f"   {content.strip()}")

            if not formatted_results:
                return f"ℹ️ No relevant matches for '{query}'"

            return "\n".join(formatted_results[:100])  # Limit output size

        except subprocess.TimeoutExpired:
            return "⚠️ Search timeout"
        except Exception as e:
            return f"⚠️ Search error: {e}"

    def get_error_docs(self, error_type: str) -> str:
        """
        Get documentation for specific error type

        Args:
            error_type: Type of error (battery, rc, gps, compass, ekf, etc.)

        Returns:
            Relevant documentation
        """
        # Map error types to search terms
        search_terms = {
            'battery': ['battery monitor', 'battery failsafe', 'voltage'],
            'rc': ['rc system', 'radio control', 'receiver'],
            'gps': ['gps', 'hdop', 'satellite'],
            'compass': ['compass', 'magnetometer', 'calibration'],
            'ekf': ['ekf', 'navekf', 'variance', 'kalman'],
            'gyro': ['imu', 'gyro', 'accelerometer'],
            'mode': ['flight mode', 'loiter', 'stabilize']
        }

        terms = search_terms.get(error_type.lower(), [error_type])

        results = []
        for term in terms[:2]:  # Limit to 2 searches
            result = self.search(term, max_results=2, context_lines=1)
            if not result.startswith('⚠️') and not result.startswith('ℹ️'):
                results.append(result)

        if results:
            return "\n\n".join(results)
        else:
            return f"ℹ️ No specific documentation found for {error_type}"

    def is_downloaded(self) -> bool:
        """Check if wiki is already downloaded"""
        return self.wiki_dir.exists() and (self.wiki_dir / ".git").exists()

    def get_doc_links(self, error_type: str) -> str:
        """
        Get documentation links for error type

        Args:
            error_type: Type of error

        Returns:
            Formatted documentation links
        """
        links = []

        # Check for direct match
        if error_type.lower() in self.doc_links:
            links.append(f"📚 {error_type.title()}: {self.doc_links[error_type.lower()]}")

        # Check for partial matches
        for key, url in self.doc_links.items():
            if error_type.lower() in key or key in error_type.lower():
                links.append(f"📚 {key.title()}: {url}")

        if not links:
            # Return general doc links
            links.append(f"📚 PreArm Checks: {self.doc_links['prearm']}")
            links.append(f"📚 Failsafe: {self.doc_links['failsafe']}")

        return "\n".join(links[:3])  # Max 3 links

    def get_quick_context(self, error_type: str) -> str:
        """
        Get quick context for AI without downloading full wiki

        Args:
            error_type: Type of error

        Returns:
            Context string with docs links
        """
        # Quick knowledge base (without downloading wiki)
        quick_docs = {
            'battery': """
BATTERY MONITOR:
- Requires BATT_MONITOR parameter (0=disabled, 3=analog voltage only, 4=analog voltage+current)
- Check voltage divider settings: BATT_VOLT_MULT
- Minimum voltage: BATT_LOW_VOLT (default 10.5V for 3S)
            """,
            'rc': """
RC SYSTEMS:
- RC_PROTOCOLS: 1=All enabled, 2=PPM, 4=SBUS, 8=DSM
- Check RC receiver is bound to transmitter
- Verify cables: RCIN port on flight controller
- Radio Calibration required in Mission Planner
            """,
            'gps': """
GPS:
- GPS_TYPE: 0=None, 1=Auto detect
- Minimum 6 satellites for ARM
- HDOP must be < 2.0
- Clear view of sky required
            """,
            'compass': """
COMPASS:
- Requires calibration before first flight
- COMPASS_USE: 1=enabled
- Keep away from magnetic interference
- External compass preferred over internal
            """,
            'ekf': """
EKF (Extended Kalman Filter):
- EKF3 is default on modern ArduPilot
- Variance errors indicate sensor issues
- Check GPS, compass, accel calibration
- Review logs for EKF_CHECK_*Зарождение
            """
        }

        context = quick_docs.get(error_type.lower(), f"No quick docs for {error_type}")
        links = self.get_doc_links(error_type)

        return f"{context}\n\nДОКУМЕНТАЦИЯ:\n{links}"


# Testing
if __name__ == '__main__':
    print("Testing GitHubDataset module...")
    print("=" * 60)

    dataset = GitHubDataset()

    # Test download
    print("\n1. Testing download...")
    dataset.download_docs()

    # Test search
    print("\n2. Testing search for 'PreArm'...")
    results = dataset.search("PreArm", max_results=2)
    print(results)

    # Test error docs
    print("\n3. Testing error docs for 'battery'...")
    docs = dataset.get_error_docs('battery')
    print(docs[:500])  # Print first 500 chars

    print("\n" + "=" * 60)
    print("✓ Tests complete")
