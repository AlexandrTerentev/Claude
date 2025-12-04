import time
from pynput import mouse, keyboard
from pynput.keyboard import Key
from typing import Callable

from core.action import Action


class ActionRecorder:
    """Records user actions (mouse clicks, key presses) for playback."""

    def __init__(self):
        self.actions: list[Action] = []
        self.is_recording = False
        self.last_action_time = 0.0
        self.mouse_listener = None
        self.keyboard_listener = None
        self.on_stop_callback: Callable[[], None] | None = None
        self.min_delay = 0.1  # Minimum delay to record

    def start_recording(self, on_stop: Callable[[], None] | None = None):
        """Start recording user actions."""
        self.actions = []
        self.is_recording = True
        self.last_action_time = time.time()
        self.on_stop_callback = on_stop

        print("[Recorder] Starting recording...")

        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_click
        )
        self.mouse_listener.start()
        print(f"[Recorder] Mouse listener started: {self.mouse_listener.is_alive()}")

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()
        print(f"[Recorder] Keyboard listener started: {self.keyboard_listener.is_alive()}")

    def stop_recording(self) -> list[Action]:
        """Stop recording and return recorded actions."""
        self.is_recording = False

        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None

        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

        return self.actions

    def _add_delay(self):
        """Add delay action based on time since last action."""
        current_time = time.time()
        delay = current_time - self.last_action_time

        if delay >= self.min_delay:
            # Round to 1 decimal place
            delay = round(delay, 1)
            self.actions.append(Action.delay(delay))

        self.last_action_time = current_time

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if not self.is_recording or not pressed:
            return

        # Add delay before this action
        self._add_delay()

        # Determine button name
        button_name = "left"
        if button == mouse.Button.right:
            button_name = "right"
        elif button == mouse.Button.middle:
            button_name = "middle"

        # Add click action
        self.actions.append(Action.click(int(x), int(y), button_name, 1))

    def _on_key_press(self, key):
        """Handle keyboard press events."""
        if not self.is_recording:
            return

        print(f"[Recorder] Key pressed: {key}")  # Debug output

        # Check for stop key (Enter)
        is_stop = False
        try:
            if key == Key.enter:
                is_stop = True
                print("[Recorder] Enter detected - stopping")
        except Exception as e:
            print(f"[Recorder] Error checking key: {e}")

        if is_stop:
            self.is_recording = False
            print("[Recorder] Calling stop callback...")
            if self.on_stop_callback:
                try:
                    self.on_stop_callback()
                    print("[Recorder] Stop callback called successfully")
                except Exception as e:
                    print(f"[Recorder] Error in stop callback: {e}")
            return False  # Stop listener

        # Add delay before this action
        self._add_delay()

        # Handle special keys
        if hasattr(key, 'char') and key.char:
            # Regular character key - add as text input
            self.actions.append(Action.type_text(key.char))
        else:
            # Special key - add as hotkey
            key_name = self._get_key_name(key)
            if key_name:
                self.actions.append(Action.hotkey(key_name))

    def _get_key_name(self, key) -> str | None:
        """Convert pynput key to pyautogui key name."""
        key_map = {
            Key.enter: "enter",
            Key.tab: "tab",
            Key.space: "space",
            Key.backspace: "backspace",
            Key.delete: "delete",
            Key.up: "up",
            Key.down: "down",
            Key.left: "left",
            Key.right: "right",
            Key.home: "home",
            Key.end: "end",
            Key.page_up: "pageup",
            Key.page_down: "pagedown",
            Key.f1: "f1",
            Key.f2: "f2",
            Key.f3: "f3",
            Key.f4: "f4",
            Key.f5: "f5",
            Key.f6: "f6",
            Key.f7: "f7",
            Key.f8: "f8",
            Key.f9: "f9",
            Key.f10: "f10",
            Key.f11: "f11",
            Key.f12: "f12",
        }

        return key_map.get(key)

    def get_recorded_actions(self) -> list[Action]:
        """Get the list of recorded actions."""
        return self.actions.copy()
