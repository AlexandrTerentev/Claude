import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel,
    QMessageBox, QTextEdit, QSplitter, QFrame, QFileDialog,
    QInputDialog, QDialog, QLineEdit, QFormLayout, QCheckBox,
    QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer


class AppSelectDialog(QDialog):
    """Dialog for selecting applications to record."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор приложений")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Info label
        info = QLabel("Введите команды через запятую:")
        layout.addWidget(info)

        # Command input
        form = QFormLayout()
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("discord, obs, firefox")
        form.addRow("Команды:", self.command_edit)
        layout.addLayout(form)

        # Browse button
        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.clicked.connect(self._browse_file)
        layout.addWidget(self.btn_browse)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_ok.setDefault(True)
        btn_layout.addWidget(self.btn_ok)

        layout.addLayout(btn_layout)

    def _browse_file(self):
        """Open file dialog to select executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите приложение",
            "",
            "Все файлы (*)"
        )
        if file_path:
            # Append to existing commands
            current = self.command_edit.text().strip()
            if current:
                self.command_edit.setText(f"{current}, {file_path}")
            else:
                self.command_edit.setText(file_path)

    def get_commands(self) -> list[str]:
        """Get list of entered commands."""
        text = self.command_edit.text().strip()
        if not text:
            return []
        # Split by comma and clean up
        commands = [cmd.strip() for cmd in text.split(",")]
        return [cmd for cmd in commands if cmd]

from core.assembly import Assembly, AppConfig
from core.executor import AssemblyExecutor
from core.recorder import ActionRecorder
from core.network_monitor import NetworkMonitor
from storage.config import ConfigManager
from ui.assembly_editor import AssemblyEditorDialog


class ExecutorThread(QThread):
    """Thread for running assembly execution."""
    progress = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, executor: AssemblyExecutor, assembly: Assembly):
        super().__init__()
        self.executor = executor
        self.assembly = assembly

    def run(self):
        success = self.executor.execute_assembly(
            self.assembly,
            progress_callback=self.progress.emit
        )
        self.finished_signal.emit(success)


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals for cross-thread communication
    recording_stopped = Signal()
    internet_reconnected = Signal()

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.executor = AssemblyExecutor()
        self.recorder = ActionRecorder()
        self.network_monitor = NetworkMonitor(check_interval=5.0)
        self.assemblies: list[Assembly] = []
        self.executor_thread: ExecutorThread | None = None
        self.recording_commands: list[str] = []
        self.auto_run_assembly_id: str | None = None

        # Connect signals
        self.recording_stopped.connect(self._finish_recording)
        self.internet_reconnected.connect(self._on_internet_reconnected)

        self.setWindowTitle("AvtoOpen - Лаунчер сборок")
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._load_assemblies()

    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left panel - assembly list
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("Сборки:"))

        self.assembly_list = QListWidget()
        self.assembly_list.itemDoubleClicked.connect(self._on_assembly_double_clicked)
        self.assembly_list.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.assembly_list)

        # Assembly buttons
        btn_layout = QHBoxLayout()

        self.btn_new = QPushButton("Создать")
        self.btn_new.clicked.connect(self._create_assembly)
        btn_layout.addWidget(self.btn_new)

        self.btn_record = QPushButton("Записать")
        self.btn_record.clicked.connect(self._start_record_assembly)
        self.btn_record.setToolTip("Записать новую сборку")
        btn_layout.addWidget(self.btn_record)

        self.btn_edit = QPushButton("Редактировать")
        self.btn_edit.clicked.connect(self._edit_assembly)
        self.btn_edit.setEnabled(False)
        btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Удалить")
        self.btn_delete.clicked.connect(self._delete_assembly)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)

        left_layout.addLayout(btn_layout)

        # Run button
        self.btn_run = QPushButton("Запустить сборку")
        self.btn_run.clicked.connect(self._run_assembly)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("QPushButton { padding: 10px; font-weight: bold; }")
        left_layout.addWidget(self.btn_run)

        # Auto-run on reconnect group
        auto_group = QGroupBox("Авто-запуск при восстановлении интернета")
        auto_layout = QVBoxLayout(auto_group)

        self.chk_auto_run = QCheckBox("Включить авто-запуск")
        self.chk_auto_run.stateChanged.connect(self._toggle_auto_run)
        auto_layout.addWidget(self.chk_auto_run)

        self.lbl_auto_status = QLabel("Статус: выключено")
        self.lbl_auto_status.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
        auto_layout.addWidget(self.lbl_auto_status)

        left_layout.addWidget(auto_group)

        # Right panel - log output
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("Лог выполнения:"))

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        right_layout.addWidget(self.log_output)

        self.btn_clear_log = QPushButton("Очистить лог")
        self.btn_clear_log.clicked.connect(self.log_output.clear)
        right_layout.addWidget(self.btn_clear_log)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])

        main_layout.addWidget(splitter)

    def _load_assemblies(self):
        """Load assemblies from config."""
        self.assemblies = self.config_manager.load_assemblies()
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the assembly list widget."""
        self.assembly_list.clear()
        for assembly in self.assemblies:
            item = QListWidgetItem(assembly.name)
            item.setData(Qt.UserRole, assembly.assembly_id)
            if assembly.description:
                item.setToolTip(assembly.description)
            self.assembly_list.addItem(item)

    def _get_selected_assembly(self) -> Assembly | None:
        """Get currently selected assembly."""
        items = self.assembly_list.selectedItems()
        if not items:
            return None

        assembly_id = items[0].data(Qt.UserRole)
        for assembly in self.assemblies:
            if assembly.assembly_id == assembly_id:
                return assembly
        return None

    def _on_selection_changed(self):
        """Handle selection change in assembly list."""
        has_selection = len(self.assembly_list.selectedItems()) > 0
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_run.setEnabled(has_selection)

    def _on_assembly_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on assembly item."""
        self._edit_assembly()

    def _create_assembly(self):
        """Create a new assembly."""
        assembly = Assembly.create("Новая сборка")
        dialog = AssemblyEditorDialog(assembly, self)

        if dialog.exec():
            self.assemblies.append(assembly)
            self.config_manager.save_assemblies(self.assemblies)
            self._refresh_list()
            self._log(f"Создана сборка: {assembly.name}")

    def _edit_assembly(self):
        """Edit selected assembly."""
        assembly = self._get_selected_assembly()
        if not assembly:
            return

        dialog = AssemblyEditorDialog(assembly, self)

        if dialog.exec():
            self.config_manager.save_assemblies(self.assemblies)
            self._refresh_list()
            self._log(f"Обновлена сборка: {assembly.name}")

    def _delete_assembly(self):
        """Delete selected assembly."""
        assembly = self._get_selected_assembly()
        if not assembly:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить сборку '{assembly.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.assemblies = [a for a in self.assemblies if a.assembly_id != assembly.assembly_id]
            self.config_manager.save_assemblies(self.assemblies)
            self._refresh_list()
            self._log(f"Удалена сборка: {assembly.name}")

    def _run_assembly(self):
        """Run selected assembly."""
        assembly = self._get_selected_assembly()
        if not assembly:
            return

        if self.executor_thread and self.executor_thread.isRunning():
            QMessageBox.warning(self, "Внимание", "Уже выполняется другая сборка")
            return

        self._log(f"\n{'='*40}")
        self._log(f"Запуск сборки: {assembly.name}")

        self.executor_thread = ExecutorThread(self.executor, assembly)
        self.executor_thread.progress.connect(self._log)
        self.executor_thread.finished_signal.connect(self._on_execution_finished)

        self.btn_run.setEnabled(False)
        self.btn_run.setText("Выполняется...")

        self.executor_thread.start()

    def _on_execution_finished(self, success: bool):
        """Handle execution completion."""
        status = "успешно" if success else "с ошибками"
        self._log(f"Выполнение завершено {status}")
        self._log(f"{'='*40}\n")

        self.btn_run.setEnabled(True)
        self.btn_run.setText("Запустить сборку")

    def _log(self, message: str):
        """Add message to log output."""
        self.log_output.append(message)

    def _start_record_assembly(self):
        """Start recording a new assembly from main screen."""
        # Show app selection dialog
        dialog = AppSelectDialog(self)
        if not dialog.exec():
            return

        commands = dialog.get_commands()
        if not commands:
            QMessageBox.warning(self, "Ошибка", "Введите команды или выберите файлы")
            return

        self.recording_commands = commands

        # Get app names from commands
        app_names = []
        for cmd in commands:
            name = os.path.basename(cmd) if '/' in cmd else cmd
            app_names.append(name)

        self._log(f"Запись сборки для: {', '.join(app_names)}")
        self._log("Нажмите Enter для остановки записи")

        # Disable buttons during recording
        self.btn_record.setEnabled(False)
        self.btn_record.setText("Запись...")
        self.btn_new.setEnabled(False)

        # Minimize window and start recording
        self.showMinimized()

        # Start recording with callback
        self.recorder.start_recording(on_stop=self._on_recording_stopped)

    def _on_recording_stopped(self):
        """Callback when recording is stopped via Enter key."""
        # Emit signal to safely update UI from another thread
        print("[MainWindow] Recording stopped callback - emitting signal")
        self.recording_stopped.emit()

    def _finish_recording(self):
        """Finish recording and create new assembly."""
        print("[MainWindow] _finish_recording called")
        recorded = self.recorder.stop_recording()
        print(f"[MainWindow] Got {len(recorded)} recorded actions")

        # Restore window
        self.showNormal()
        self.activateWindow()
        self.raise_()

        # Re-enable buttons
        self.btn_record.setEnabled(True)
        self.btn_record.setText("Записать")
        self.btn_new.setEnabled(True)

        if not recorded:
            self._log("Запись отменена - нет действий")
            return

        # Get app names for default assembly name
        app_names = []
        for cmd in self.recording_commands:
            name = os.path.basename(cmd) if '/' in cmd else cmd
            app_names.append(name)

        default_name = ", ".join(app_names)

        name, ok = QInputDialog.getText(
            self,
            "Название сборки",
            "Введите название для новой сборки:",
            text=f"Сборка {default_name}"
        )

        if not ok or not name:
            self._log("Запись отменена пользователем")
            return

        # Create assembly
        assembly = Assembly.create(name)

        # Create app config for each command
        for cmd in self.recording_commands:
            app_name = os.path.basename(cmd) if '/' in cmd else cmd
            app_config = AppConfig.create(
                name=app_name,
                executable_path=cmd
            )
            assembly.apps.append(app_config)

        # Add recorded actions to first app
        if assembly.apps:
            assembly.apps[0].actions = recorded

        # Save assembly
        self.assemblies.append(assembly)
        self.config_manager.save_assemblies(self.assemblies)
        self._refresh_list()

        self._log(f"Создана сборка '{name}' с {len(self.recording_commands)} приложениями и {len(recorded)} действиями")

    def _toggle_auto_run(self, state):
        """Toggle auto-run on internet reconnect."""
        print(f"[MainWindow] _toggle_auto_run called with state={state}", flush=True)

        # state is 2 when checked, 0 when unchecked
        if state == 2:  # Qt.CheckState.Checked
            print("[MainWindow] Checkbox is checked", flush=True)

            # Get selected assembly
            assembly = self._get_selected_assembly()
            print(f"[MainWindow] Selected assembly: {assembly}", flush=True)

            if not assembly:
                QMessageBox.warning(
                    self,
                    "Внимание",
                    "Сначала выберите сборку для авто-запуска"
                )
                self.chk_auto_run.setChecked(False)
                return

            self.auto_run_assembly_id = assembly.assembly_id
            print(f"[MainWindow] Starting network monitor for: {assembly.name}", flush=True)

            # Start monitoring
            self.network_monitor.start_monitoring(
                on_reconnect=self._emit_reconnect_signal
            )

            self.lbl_auto_status.setText(f"Ожидание: {assembly.name}")
            self.lbl_auto_status.setStyleSheet("QLabel { color: green; font-size: 10px; }")
            self._log(f"Авто-запуск включён для: {assembly.name}")
            print("[MainWindow] Auto-run enabled", flush=True)

        else:
            # Stop monitoring
            self.network_monitor.stop_monitoring()
            self.auto_run_assembly_id = None

            self.lbl_auto_status.setText("Статус: выключено")
            self.lbl_auto_status.setStyleSheet("QLabel { color: gray; font-size: 10px; }")
            self._log("Авто-запуск выключен")

    def _emit_reconnect_signal(self):
        """Emit signal when internet reconnects (called from monitor thread)."""
        self.internet_reconnected.emit()

    def _on_internet_reconnected(self):
        """Handle internet reconnection - run the selected assembly."""
        if not self.auto_run_assembly_id:
            return

        # Find assembly by ID
        assembly = None
        for a in self.assemblies:
            if a.assembly_id == self.auto_run_assembly_id:
                assembly = a
                break

        if not assembly:
            self._log("Ошибка: сборка для авто-запуска не найдена")
            return

        self._log(f"Интернет восстановлен! Запуск сборки: {assembly.name}")

        # Run the assembly
        if self.executor_thread and self.executor_thread.isRunning():
            self._log("Предыдущая сборка ещё выполняется, пропуск")
            return

        self.executor_thread = ExecutorThread(self.executor, assembly)
        self.executor_thread.progress.connect(self._log)
        self.executor_thread.finished_signal.connect(self._on_execution_finished)
        self.executor_thread.start()

    def closeEvent(self, event):
        """Handle window close."""
        if self.executor_thread and self.executor_thread.isRunning():
            self.executor.stop()
            self.executor_thread.wait()

        # Stop recording if active
        if self.recorder.is_recording:
            self.recorder.stop_recording()

        # Stop network monitoring
        self.network_monitor.stop_monitoring()

        event.accept()
