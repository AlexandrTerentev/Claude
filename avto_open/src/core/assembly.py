from dataclasses import dataclass, field
from typing import Any
import uuid

from .action import Action


@dataclass
class AppConfig:
    """Configuration for a single application in an assembly."""

    app_id: str
    name: str
    executable_path: str
    actions: list[Action] = field(default_factory=list)
    working_directory: str = ""
    arguments: str = ""

    def to_dict(self) -> dict:
        return {
            "app_id": self.app_id,
            "name": self.name,
            "executable_path": self.executable_path,
            "actions": [action.to_dict() for action in self.actions],
            "working_directory": self.working_directory,
            "arguments": self.arguments
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        return cls(
            app_id=data.get("app_id", str(uuid.uuid4())),
            name=data["name"],
            executable_path=data["executable_path"],
            actions=[Action.from_dict(a) for a in data.get("actions", [])],
            working_directory=data.get("working_directory", ""),
            arguments=data.get("arguments", "")
        )

    @classmethod
    def create(cls, name: str, executable_path: str) -> "AppConfig":
        """Create a new app config with a unique ID."""
        return cls(
            app_id=str(uuid.uuid4()),
            name=name,
            executable_path=executable_path
        )


@dataclass
class Assembly:
    """Represents a collection of apps to launch together with their actions."""

    assembly_id: str
    name: str
    description: str = ""
    apps: list[AppConfig] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "assembly_id": self.assembly_id,
            "name": self.name,
            "description": self.description,
            "apps": [app.to_dict() for app in self.apps]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Assembly":
        return cls(
            assembly_id=data.get("assembly_id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description", ""),
            apps=[AppConfig.from_dict(a) for a in data.get("apps", [])]
        )

    @classmethod
    def create(cls, name: str, description: str = "") -> "Assembly":
        """Create a new assembly with a unique ID."""
        return cls(
            assembly_id=str(uuid.uuid4()),
            name=name,
            description=description
        )

    def add_app(self, app: AppConfig) -> None:
        """Add an application to the assembly."""
        self.apps.append(app)

    def remove_app(self, app_id: str) -> bool:
        """Remove an application by its ID. Returns True if removed."""
        for i, app in enumerate(self.apps):
            if app.app_id == app_id:
                self.apps.pop(i)
                return True
        return False

    def get_app(self, app_id: str) -> AppConfig | None:
        """Get an application by its ID."""
        for app in self.apps:
            if app.app_id == app_id:
                return app
        return None

    def move_app(self, app_id: str, direction: int) -> bool:
        """Move an app up (direction=-1) or down (direction=1)."""
        for i, app in enumerate(self.apps):
            if app.app_id == app_id:
                new_index = i + direction
                if 0 <= new_index < len(self.apps):
                    self.apps[i], self.apps[new_index] = self.apps[new_index], self.apps[i]
                    return True
                return False
        return False
