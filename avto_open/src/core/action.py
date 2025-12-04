from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(Enum):
    DELAY = "delay"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    HOTKEY = "hotkey"
    MOVE_MOUSE = "move_mouse"
    SCROLL = "scroll"


@dataclass
class Action:
    """Represents a single automation action."""

    action_type: ActionType
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type.value,
            "params": self.params
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Action":
        return cls(
            action_type=ActionType(data["action_type"]),
            params=data.get("params", {})
        )

    @classmethod
    def delay(cls, seconds: float) -> "Action":
        """Create a delay action."""
        return cls(ActionType.DELAY, {"seconds": seconds})

    @classmethod
    def click(cls, x: int, y: int, button: str = "left", clicks: int = 1) -> "Action":
        """Create a click action."""
        return cls(ActionType.CLICK, {
            "x": x,
            "y": y,
            "button": button,
            "clicks": clicks
        })

    @classmethod
    def type_text(cls, text: str, interval: float = 0.0) -> "Action":
        """Create a type text action."""
        return cls(ActionType.TYPE_TEXT, {
            "text": text,
            "interval": interval
        })

    @classmethod
    def hotkey(cls, *keys: str) -> "Action":
        """Create a hotkey action."""
        return cls(ActionType.HOTKEY, {"keys": list(keys)})

    @classmethod
    def move_mouse(cls, x: int, y: int, duration: float = 0.0) -> "Action":
        """Create a move mouse action."""
        return cls(ActionType.MOVE_MOUSE, {
            "x": x,
            "y": y,
            "duration": duration
        })

    @classmethod
    def scroll(cls, clicks: int, x: int | None = None, y: int | None = None) -> "Action":
        """Create a scroll action."""
        return cls(ActionType.SCROLL, {
            "clicks": clicks,
            "x": x,
            "y": y
        })

    def get_description(self) -> str:
        """Get human-readable description of the action."""
        match self.action_type:
            case ActionType.DELAY:
                return f"Задержка {self.params.get('seconds', 0)} сек"
            case ActionType.CLICK:
                btn = self.params.get('button', 'left')
                clicks = self.params.get('clicks', 1)
                x, y = self.params.get('x', 0), self.params.get('y', 0)
                return f"Клик ({btn}, {clicks}x) в ({x}, {y})"
            case ActionType.TYPE_TEXT:
                text = self.params.get('text', '')
                preview = text[:20] + "..." if len(text) > 20 else text
                return f"Ввод текста: \"{preview}\""
            case ActionType.HOTKEY:
                keys = self.params.get('keys', [])
                return f"Горячая клавиша: {'+'.join(keys)}"
            case ActionType.MOVE_MOUSE:
                x, y = self.params.get('x', 0), self.params.get('y', 0)
                return f"Переместить мышь в ({x}, {y})"
            case ActionType.SCROLL:
                clicks = self.params.get('clicks', 0)
                direction = "вверх" if clicks > 0 else "вниз"
                return f"Прокрутка {direction} ({abs(clicks)})"
            case _:
                return str(self.action_type.value)
