# -*- coding: utf-8 -*-
"""
Configuration Manager for MPDiagnosticAgent
Handles auto-detection of Mission Planner, cross-platform paths, and user settings
"""

import os
import platform
import yaml
from pathlib import Path
from typing import Dict, Optional, Any


class Config:
    """
    Configuration manager with auto-detection and cross-platform support

    Features:
    - Auto-detect Mission Planner installation (Linux/Windows)
    - Load/save user configuration from YAML
    - Cross-platform path handling
    - Default values for all settings
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_file: Path to config.yaml. If None, uses default location
        """
        self.platform = self._detect_platform()
        self.config_file = config_file or self._get_default_config_path()

        # Load configuration (or use defaults)
        self.config = self._load_config()

        # Detect Mission Planner if auto_detect is enabled
        if self.config['mission_planner']['auto_detect']:
            detected_path = self._find_mission_planner()
            if detected_path:
                self.config['mission_planner']['detected_path'] = str(detected_path)

        # Build all paths
        self._build_paths()

    def _detect_platform(self) -> str:
        """Detect operating system"""
        system = platform.system()
        if system == 'Linux':
            return 'linux'
        elif system == 'Windows':
            return 'windows'
        elif system == 'Darwin':
            return 'macos'
        else:
            return 'unknown'

    def _get_default_config_path(self) -> Path:
        """Get default configuration file path"""
        # Try to find config in project directory first
        project_root = Path(__file__).parent.parent
        config_path = project_root / 'config' / 'config.yaml'

        if config_path.exists():
            return config_path

        # Otherwise use user home directory
        home_config = Path.home() / '.mpdiagnostic' / 'config.yaml'
        return home_config

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or return defaults"""
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                print(f"✓ Configuration loaded from: {self.config_file}")
                return config
            except Exception as e:
                print(f"⚠ Error loading config: {e}")
                print("Using default configuration")
                return self._get_default_config()
        else:
            print(f"⚠ Config file not found: {self.config_file}")
            print("Using default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'mission_planner': {
                'auto_detect': True,
                'manual_path': None,
                'detected_path': None
            },
            'log_locations': {
                'mission_planner_log': 'auto',
                'tlog_directory': 'auto',
                'bin_directory': 'auto'
            },
            'mavlink': {
                'default_port': '/dev/ttyUSB0' if self.platform == 'linux' else 'COM3',
                'baudrate': 921600,
                'timeout': 300,
                'retry_count': 3
            },
            'diagnostics': {
                'log_lines_to_analyze': 300,
                'wiki_integration': True,
                'language': 'auto'
            },
            'testing': {
                'drone_available': False,
                'test_connection_on_startup': False
            }
        }

    def _find_mission_planner(self) -> Optional[Path]:
        """
        Auto-detect Mission Planner installation

        Returns:
            Path to Mission Planner directory or None if not found
        """
        # Check manual path first
        manual_path = self.config['mission_planner'].get('manual_path')
        if manual_path:
            path = Path(manual_path)
            if path.exists():
                print(f"✓ Using manual Mission Planner path: {path}")
                return path

        # Platform-specific search
        candidates = []

        if self.platform == 'linux':
            candidates = [
                Path.home() / 'missionplanner',
                Path('/opt/missionplanner'),
                Path('/usr/local/missionplanner'),
                Path.home() / 'Mission Planner',
            ]
        elif self.platform == 'windows':
            candidates = [
                Path('C:/Program Files/Mission Planner'),
                Path('C:/Program Files (x86)/Mission Planner'),
                Path(os.getenv('APPDATA', '')) / 'Mission Planner',
                Path.home() / 'Mission Planner',
            ]
        elif self.platform == 'macos':
            candidates = [
                Path.home() / 'Applications' / 'Mission Planner',
                Path('/Applications/Mission Planner'),
                Path.home() / 'missionplanner',
            ]

        # Search for Mission Planner
        for path in candidates:
            if path.exists():
                # Verify it's actually Mission Planner by checking for key files
                if self._verify_mission_planner(path):
                    print(f"✓ Auto-detected Mission Planner at: {path}")
                    return path

        print("⚠ Mission Planner not auto-detected")
        return None

    def _verify_mission_planner(self, path: Path) -> bool:
        """
        Verify that a path contains Mission Planner installation

        Args:
            path: Path to check

        Returns:
            True if this looks like Mission Planner directory
        """
        # Check for common Mission Planner files/directories
        indicators = [
            'Mission Planner',  # Directory
            'MissionPlanner.exe',  # Windows executable
            'MissionPlanner.log',  # Log file (in subdirectory)
        ]

        for indicator in indicators:
            check_path = path / indicator
            if check_path.exists():
                return True

        return False

    def _build_paths(self):
        """Build all path properties from configuration"""
        # Get Mission Planner base path
        mp_path = self._get_mp_path()

        # Mission Planner log
        if self.config['log_locations']['mission_planner_log'] == 'auto':
            if mp_path:
                self.mp_log_path = mp_path / 'Mission Planner' / 'MissionPlanner.log'
            else:
                self.mp_log_path = None
        else:
            self.mp_log_path = Path(self.config['log_locations']['mission_planner_log'])

        # Telemetry log directory
        if self.config['log_locations']['tlog_directory'] == 'auto':
            if mp_path:
                self.tlog_dir = mp_path / 'logs'
            else:
                self.tlog_dir = Path.home() / 'mplogs'
        else:
            self.tlog_dir = Path(self.config['log_locations']['tlog_directory'])

        # Dataflash log directory
        if self.config['log_locations']['bin_directory'] == 'auto':
            if mp_path:
                self.bin_dir = mp_path / 'logs' / 'QUADCOPTER'
            else:
                self.bin_dir = self.tlog_dir / 'QUADCOPTER'
        else:
            self.bin_dir = Path(self.config['log_locations']['bin_directory'])

        # Create directories if they don't exist
        self._ensure_directories()

    def _get_mp_path(self) -> Optional[Path]:
        """Get Mission Planner path (detected or manual)"""
        # Prefer manual path
        manual = self.config['mission_planner'].get('manual_path')
        if manual:
            return Path(manual)

        # Fall back to detected
        detected = self.config['mission_planner'].get('detected_path')
        if detected:
            return Path(detected)

        return None

    @property
    def mission_planner_path(self) -> Optional[Path]:
        """Get Mission Planner path (property for GUI compatibility)"""
        return self._get_mp_path()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        dirs_to_create = [self.tlog_dir, self.bin_dir]

        for directory in dirs_to_create:
            if directory and not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    print(f"✓ Created directory: {directory}")
                except Exception as e:
                    print(f"⚠ Could not create directory {directory}: {e}")

    def save_config(self, filepath: Optional[str] = None):
        """
        Save current configuration to YAML file

        Args:
            filepath: Path to save config. If None, uses self.config_file
        """
        save_path = Path(filepath) if filepath else Path(self.config_file)

        # Ensure parent directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ Configuration saved to: {save_path}")
        except Exception as e:
            print(f"✗ Error saving configuration: {e}")

    # Convenience properties
    @property
    def mavlink_port(self) -> str:
        """Get default MAVLink port"""
        return self.config['mavlink']['default_port']

    @property
    def mavlink_baudrate(self) -> int:
        """Get MAVLink baudrate"""
        return self.config['mavlink']['baudrate']

    @property
    def mavlink_timeout(self) -> int:
        """Get MAVLink timeout in seconds"""
        return self.config['mavlink']['timeout']

    @property
    def log_lines_to_analyze(self) -> int:
        """Get number of log lines to analyze"""
        return self.config['diagnostics']['log_lines_to_analyze']

    @property
    def wiki_integration_enabled(self) -> bool:
        """Check if Wiki integration is enabled"""
        return self.config['diagnostics']['wiki_integration']

    @property
    def language(self) -> str:
        """Get preferred language (auto/ru/en)"""
        return self.config['diagnostics']['language']

    def get_log_paths(self) -> Dict[str, Path]:
        """
        Get all log file paths

        Returns:
            Dictionary with log file paths
        """
        return {
            'mp_log': self.mp_log_path,
            'tlog_dir': self.tlog_dir,
            'bin_dir': self.bin_dir
        }

    def print_summary(self):
        """Print configuration summary"""
        print("\n" + "="*60)
        print("MPDiagnosticAgent Configuration Summary")
        print("="*60)
        print(f"Platform: {self.platform}")
        print(f"Config file: {self.config_file}")
        print(f"\nMission Planner:")
        mp_path = self._get_mp_path()
        if mp_path:
            print(f"  Path: {mp_path}")
        else:
            print(f"  Path: Not detected")

        print(f"\nLog Locations:")
        print(f"  MP Log: {self.mp_log_path}")
        if self.mp_log_path and self.mp_log_path.exists():
            print(f"    ✓ Exists ({self.mp_log_path.stat().st_size} bytes)")
        elif self.mp_log_path:
            print(f"    ✗ Not found")

        print(f"  Telemetry: {self.tlog_dir}")
        if self.tlog_dir.exists():
            print(f"    ✓ Exists")
        else:
            print(f"    ✗ Not found")

        print(f"  Dataflash: {self.bin_dir}")
        if self.bin_dir.exists():
            print(f"    ✓ Exists")
        else:
            print(f"    ✗ Not found")

        print(f"\nMAVLink:")
        print(f"  Port: {self.mavlink_port}")
        print(f"  Baudrate: {self.mavlink_baudrate}")
        print(f"  Timeout: {self.mavlink_timeout}s")

        print(f"\nDiagnostics:")
        print(f"  Log lines to analyze: {self.log_lines_to_analyze}")
        print(f"  Wiki integration: {self.wiki_integration_enabled}")
        print(f"  Language: {self.language}")
        print("="*60 + "\n")


# Testing
if __name__ == '__main__':
    print("Testing Config module...\n")

    # Create config instance
    config = Config()

    # Print summary
    config.print_summary()

    # Test getting paths
    paths = config.get_log_paths()
    print("Log paths:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
