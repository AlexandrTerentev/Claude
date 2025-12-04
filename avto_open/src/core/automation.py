import time
import pyautogui

from .action import Action, ActionType


# Disable PyAutoGUI fail-safe only if needed
# pyautogui.FAILSAFE = False


class AutomationEngine:
    """Executes automation actions using PyAutoGUI."""

    def __init__(self):
        # Set default pause between actions
        pyautogui.PAUSE = 0.1

    def execute_action(self, action: Action) -> bool:
        """Execute a single action. Returns True if successful."""
        try:
            match action.action_type:
                case ActionType.DELAY:
                    seconds = action.params.get("seconds", 1.0)
                    time.sleep(seconds)

                case ActionType.CLICK:
                    x = action.params.get("x", 0)
                    y = action.params.get("y", 0)
                    button = action.params.get("button", "left")
                    clicks = action.params.get("clicks", 1)
                    pyautogui.click(x, y, clicks=clicks, button=button)

                case ActionType.TYPE_TEXT:
                    text = action.params.get("text", "")
                    interval = action.params.get("interval", 0.0)
                    pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)

                case ActionType.HOTKEY:
                    keys = action.params.get("keys", [])
                    if keys:
                        pyautogui.hotkey(*keys)

                case ActionType.MOVE_MOUSE:
                    x = action.params.get("x", 0)
                    y = action.params.get("y", 0)
                    duration = action.params.get("duration", 0.0)
                    pyautogui.moveTo(x, y, duration=duration)

                case ActionType.SCROLL:
                    clicks = action.params.get("clicks", 0)
                    x = action.params.get("x")
                    y = action.params.get("y")
                    pyautogui.scroll(clicks, x, y)

                case _:
                    print(f"Unknown action type: {action.action_type}")
                    return False

            return True

        except Exception as e:
            print(f"Error executing action {action.action_type}: {e}")
            return False

    def execute_actions(self, actions: list[Action], stop_on_error: bool = True) -> tuple[int, int]:
        """
        Execute a list of actions.

        Args:
            actions: List of actions to execute
            stop_on_error: If True, stop on first error

        Returns:
            Tuple of (successful_count, total_count)
        """
        successful = 0
        for action in actions:
            if self.execute_action(action):
                successful += 1
            elif stop_on_error:
                break

        return successful, len(actions)

    @staticmethod
    def get_mouse_position() -> tuple[int, int]:
        """Get current mouse position."""
        return pyautogui.position()

    @staticmethod
    def get_screen_size() -> tuple[int, int]:
        """Get screen size."""
        return pyautogui.size()
