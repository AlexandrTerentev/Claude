from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QListWidget, QListWidgetItem, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QLineEdit, QLabel,
    QGroupBox, QStackedWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
import pyautogui

from core.assembly import AppConfig
from core.action import Action, ActionType
from core.recorder import ActionRecorder


class ActionEditorDialog(QDialog):
    """Dialog for editing actions of an app."""

    def __init__(self, app: AppConfig, parent=None):
        super().__init__(parent)
        self.app = app
        self.actions = list(app.actions)  # Work with a copy
        self.recorder = ActionRecorder()

        self.setWindowTitle(f"Действия - {app.name}")
        self.setMinimumSize(600, 500)

        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QHBoxLayout(self)

        # Left panel - action list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Последовательность действий:"))

        self.action_list = QListWidget()
        self.action_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.action_list)

        # List buttons
        list_btn_layout = QHBoxLayout()

        self.btn_move_up = QPushButton("↑")
        self.btn_move_up.setMaximumWidth(40)
        self.btn_move_up.clicked.connect(lambda: self._move_action(-1))
        self.btn_move_up.setEnabled(False)
        list_btn_layout.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("↓")
        self.btn_move_down.setMaximumWidth(40)
        self.btn_move_down.clicked.connect(lambda: self._move_action(1))
        self.btn_move_down.setEnabled(False)
        list_btn_layout.addWidget(self.btn_move_down)

        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.clicked.connect(self._delete_action)
        self.btn_delete.setEnabled(False)
        list_btn_layout.addWidget(self.btn_delete)

        left_layout.addLayout(list_btn_layout)

        layout.addWidget(left_panel)

        # Right panel - action creation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Action type selector
        type_group = QGroupBox("Добавить действие")
        type_layout = QVBoxLayout(type_group)

        type_form = QFormLayout()
        self.action_type_combo = QComboBox()
        self.action_type_combo.addItem("Задержка", ActionType.DELAY)
        self.action_type_combo.addItem("Клик мыши", ActionType.CLICK)
        self.action_type_combo.addItem("Ввод текста", ActionType.TYPE_TEXT)
        self.action_type_combo.addItem("Горячая клавиша", ActionType.HOTKEY)
        self.action_type_combo.addItem("Переместить мышь", ActionType.MOVE_MOUSE)
        self.action_type_combo.addItem("Прокрутка", ActionType.SCROLL)
        self.action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        type_form.addRow("Тип:", self.action_type_combo)
        type_layout.addLayout(type_form)

        # Stacked widget for action parameters
        self.params_stack = QStackedWidget()
        self._create_param_widgets()
        type_layout.addWidget(self.params_stack)

        self.btn_add = QPushButton("Добавить действие")
        self.btn_add.clicked.connect(self._add_action)
        type_layout.addWidget(self.btn_add)

        right_layout.addWidget(type_group)

        # Record actions group
        record_group = QGroupBox("Запись действий")
        record_layout = QVBoxLayout(record_group)

        self.record_status = QLabel("Нажмите для записи действий")
        record_layout.addWidget(self.record_status)

        self.btn_record = QPushButton("Начать запись")
        self.btn_record.clicked.connect(self._toggle_recording)
        self.btn_record.setStyleSheet("QPushButton { font-weight: bold; }")
        record_layout.addWidget(self.btn_record)

        record_info = QLabel("Нажмите Escape для остановки записи")
        record_info.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
        record_layout.addWidget(record_info)

        right_layout.addWidget(record_group)

        # Mouse position helper
        pos_group = QGroupBox("Помощник координат")
        pos_layout = QVBoxLayout(pos_group)

        self.pos_label = QLabel("X: 0, Y: 0")
        pos_layout.addWidget(self.pos_label)

        self.btn_capture = QPushButton("Захватить позицию (3 сек)")
        self.btn_capture.clicked.connect(self._start_capture)
        pos_layout.addWidget(self.btn_capture)

        right_layout.addWidget(pos_group)

        right_layout.addStretch()

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.btn_save)

        right_layout.addLayout(btn_layout)

        layout.addWidget(right_panel)

    def _create_param_widgets(self):
        """Create parameter widgets for each action type."""
        # Delay
        delay_widget = QWidget()
        delay_layout = QFormLayout(delay_widget)
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.1, 300)
        self.delay_spin.setValue(1.0)
        self.delay_spin.setSuffix(" сек")
        delay_layout.addRow("Время:", self.delay_spin)
        self.params_stack.addWidget(delay_widget)

        # Click
        click_widget = QWidget()
        click_layout = QFormLayout(click_widget)
        self.click_x = QSpinBox()
        self.click_x.setRange(0, 10000)
        click_layout.addRow("X:", self.click_x)
        self.click_y = QSpinBox()
        self.click_y.setRange(0, 10000)
        click_layout.addRow("Y:", self.click_y)
        self.click_button = QComboBox()
        self.click_button.addItems(["left", "right", "middle"])
        click_layout.addRow("Кнопка:", self.click_button)
        self.click_count = QSpinBox()
        self.click_count.setRange(1, 5)
        click_layout.addRow("Кликов:", self.click_count)
        self.params_stack.addWidget(click_widget)

        # Type text
        text_widget = QWidget()
        text_layout = QFormLayout(text_widget)
        self.type_text = QLineEdit()
        text_layout.addRow("Текст:", self.type_text)
        self.type_interval = QDoubleSpinBox()
        self.type_interval.setRange(0, 1)
        self.type_interval.setValue(0)
        self.type_interval.setSingleStep(0.01)
        text_layout.addRow("Интервал:", self.type_interval)
        self.params_stack.addWidget(text_widget)

        # Hotkey
        hotkey_widget = QWidget()
        hotkey_layout = QFormLayout(hotkey_widget)
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("ctrl+shift+s")
        hotkey_layout.addRow("Клавиши:", self.hotkey_edit)
        self.params_stack.addWidget(hotkey_widget)

        # Move mouse
        move_widget = QWidget()
        move_layout = QFormLayout(move_widget)
        self.move_x = QSpinBox()
        self.move_x.setRange(0, 10000)
        move_layout.addRow("X:", self.move_x)
        self.move_y = QSpinBox()
        self.move_y.setRange(0, 10000)
        move_layout.addRow("Y:", self.move_y)
        self.move_duration = QDoubleSpinBox()
        self.move_duration.setRange(0, 10)
        self.move_duration.setSuffix(" сек")
        move_layout.addRow("Длительность:", self.move_duration)
        self.params_stack.addWidget(move_widget)

        # Scroll
        scroll_widget = QWidget()
        scroll_layout = QFormLayout(scroll_widget)
        self.scroll_clicks = QSpinBox()
        self.scroll_clicks.setRange(-100, 100)
        self.scroll_clicks.setValue(3)
        scroll_layout.addRow("Кликов (+ вверх):", self.scroll_clicks)
        self.params_stack.addWidget(scroll_widget)

    def _on_action_type_changed(self, index: int):
        """Handle action type change."""
        self.params_stack.setCurrentIndex(index)

    def _refresh_list(self):
        """Refresh the action list."""
        self.action_list.clear()
        for i, action in enumerate(self.actions):
            item = QListWidgetItem(f"{i+1}. {action.get_description()}")
            item.setData(Qt.UserRole, i)
            self.action_list.addItem(item)

    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.action_list.selectedItems()) > 0
        self.btn_move_up.setEnabled(has_selection)
        self.btn_move_down.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def _get_selected_index(self) -> int | None:
        """Get selected action index."""
        items = self.action_list.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.UserRole)

    def _add_action(self):
        """Add a new action based on current parameters."""
        action_type = self.action_type_combo.currentData()

        match action_type:
            case ActionType.DELAY:
                action = Action.delay(self.delay_spin.value())

            case ActionType.CLICK:
                action = Action.click(
                    self.click_x.value(),
                    self.click_y.value(),
                    self.click_button.currentText(),
                    self.click_count.value()
                )

            case ActionType.TYPE_TEXT:
                text = self.type_text.text()
                if not text:
                    QMessageBox.warning(self, "Ошибка", "Введите текст")
                    return
                action = Action.type_text(text, self.type_interval.value())

            case ActionType.HOTKEY:
                keys_str = self.hotkey_edit.text().strip()
                if not keys_str:
                    QMessageBox.warning(self, "Ошибка", "Введите клавиши")
                    return
                keys = [k.strip() for k in keys_str.split("+")]
                action = Action.hotkey(*keys)

            case ActionType.MOVE_MOUSE:
                action = Action.move_mouse(
                    self.move_x.value(),
                    self.move_y.value(),
                    self.move_duration.value()
                )

            case ActionType.SCROLL:
                action = Action.scroll(self.scroll_clicks.value())

            case _:
                return

        self.actions.append(action)
        self._refresh_list()

    def _delete_action(self):
        """Delete selected action."""
        index = self._get_selected_index()
        if index is not None:
            self.actions.pop(index)
            self._refresh_list()

    def _move_action(self, direction: int):
        """Move selected action up or down."""
        index = self._get_selected_index()
        if index is None:
            return

        new_index = index + direction
        if 0 <= new_index < len(self.actions):
            self.actions[index], self.actions[new_index] = self.actions[new_index], self.actions[index]
            self._refresh_list()
            # Reselect the moved item
            self.action_list.setCurrentRow(new_index)

    def _start_capture(self):
        """Start mouse position capture countdown."""
        self.btn_capture.setEnabled(False)
        self.btn_capture.setText("3...")

        QTimer.singleShot(1000, lambda: self.btn_capture.setText("2..."))
        QTimer.singleShot(2000, lambda: self.btn_capture.setText("1..."))
        QTimer.singleShot(3000, self._capture_position)

    def _capture_position(self):
        """Capture current mouse position."""
        x, y = pyautogui.position()
        self.pos_label.setText(f"X: {x}, Y: {y}")

        # Auto-fill click/move coordinates
        self.click_x.setValue(x)
        self.click_y.setValue(y)
        self.move_x.setValue(x)
        self.move_y.setValue(y)

        self.btn_capture.setText("Захватить позицию (3 сек)")
        self.btn_capture.setEnabled(True)

    def _toggle_recording(self):
        """Start or stop recording actions."""
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start recording user actions."""
        self.btn_record.setText("Остановить запись")
        self.btn_record.setStyleSheet("QPushButton { font-weight: bold; background-color: #ff6b6b; }")
        self.record_status.setText("Запись... (Escape для остановки)")
        self.record_status.setStyleSheet("QLabel { color: red; font-weight: bold; }")

        # Minimize window so user can interact with other apps
        self.showMinimized()

        # Start recording with callback
        self.recorder.start_recording(on_stop=self._on_recording_stopped)

    def _stop_recording(self):
        """Stop recording and add recorded actions."""
        recorded = self.recorder.stop_recording()

        self.btn_record.setText("Начать запись")
        self.btn_record.setStyleSheet("QPushButton { font-weight: bold; }")
        self.record_status.setText(f"Записано {len(recorded)} действий")
        self.record_status.setStyleSheet("QLabel { color: green; }")

        # Add recorded actions to the list
        if recorded:
            self.actions.extend(recorded)
            self._refresh_list()

        # Restore window
        self.showNormal()
        self.activateWindow()

    def _on_recording_stopped(self):
        """Callback when recording is stopped via Escape key."""
        # Use QTimer to safely update UI from another thread
        QTimer.singleShot(0, self._stop_recording)

    def _save_and_close(self):
        """Save actions and close dialog."""
        # Stop recording if active
        if self.recorder.is_recording:
            self.recorder.stop_recording()

        self.app.actions = self.actions
        self.accept()
