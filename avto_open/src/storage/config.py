import json
import os
import platform
from pathlib import Path

from core.assembly import Assembly


class ConfigManager:
    """Manages saving and loading of assemblies."""

    def __init__(self):
        self.config_dir = self._get_config_dir()
        self.assemblies_file = self.config_dir / "assemblies.json"
        self._ensure_config_dir()

    def _get_config_dir(self) -> Path:
        """Get platform-specific config directory."""
        if platform.system() == "Windows":
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
            return Path(base) / "avto_open"
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            return Path(xdg_config) / "avto_open"

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_assemblies(self) -> list[Assembly]:
        """Load all assemblies from config file."""
        if not self.assemblies_file.exists():
            return []

        try:
            with open(self.assemblies_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Assembly.from_dict(a) for a in data.get("assemblies", [])]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading assemblies: {e}")
            return []

    def save_assemblies(self, assemblies: list[Assembly]) -> bool:
        """Save all assemblies to config file."""
        try:
            data = {
                "version": 1,
                "assemblies": [a.to_dict() for a in assemblies]
            }
            with open(self.assemblies_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"Error saving assemblies: {e}")
            return False

    def get_assembly(self, assembly_id: str) -> Assembly | None:
        """Get a specific assembly by ID."""
        assemblies = self.load_assemblies()
        for assembly in assemblies:
            if assembly.assembly_id == assembly_id:
                return assembly
        return None

    def save_assembly(self, assembly: Assembly) -> bool:
        """Save or update a single assembly."""
        assemblies = self.load_assemblies()

        # Find and replace existing, or append new
        found = False
        for i, a in enumerate(assemblies):
            if a.assembly_id == assembly.assembly_id:
                assemblies[i] = assembly
                found = True
                break

        if not found:
            assemblies.append(assembly)

        return self.save_assemblies(assemblies)

    def delete_assembly(self, assembly_id: str) -> bool:
        """Delete an assembly by ID."""
        assemblies = self.load_assemblies()
        new_assemblies = [a for a in assemblies if a.assembly_id != assembly_id]

        if len(new_assemblies) == len(assemblies):
            return False

        return self.save_assemblies(new_assemblies)
