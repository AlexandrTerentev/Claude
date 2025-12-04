import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QLabel,
    QGroupBox, QSplitter, QWidget
)
from PySide6.QtCore import Qt

from core.assembly import Assembly, AppConfig
from ui.action_editor import ActionEditorDialog


class AssemblyEditorDialog(QDialog):
    """Dialog for editing an assembly."""

    def __init__(self, assembly: Assembly, parent=None):
        super().__init__(parent)
        self.assembly = assembly

        self.setWindowTitle("Редактор сборки")
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Assembly info
        info_group = QGroupBox("Информация о сборке")
        info_layout = QFormLayout(info_group)

        self.name_edit = QLineEdit()
        info_layout.addRow("Название:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        info_layout.addRow("Описание:", self.description_edit)

        layout.addWidget(info_group)

        # Apps section
        apps_group = QGroupBox("Приложения")
        apps_layout = QHBoxLayout(apps_group)

        # App list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.app_list = QListWidget()
        self.app_list.itemSelectionChanged.connect(self._on_app_selection_changed)
        self.app_list.itemDoubleClicked.connect(self._edit_app_actions)
        list_layout.addWidget(self.app_list)

        # App buttons
        app_btn_layout = QHBoxLayout()

        self.btn_add_app = QPushButton("Добавить")
        self.btn_add_app.clicked.connect(self._add_app)
        app_btn_layout.addWidget(self.btn_add_app)

        self.btn_remove_app = QPushButton("Удалить")
        self.btn_remove_app.clicked.connect(self._remove_app)
        self.btn_remove_app.setEnabled(False)
        app_btn_layout.addWidget(self.btn_remove_app)

        self.btn_move_up = QPushButton("Вверх")
        self.btn_move_up.clicked.connect(lambda: self._move_app(-1))
        self.btn_move_up.setEnabled(False)
        app_btn_layout.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Вниз")
        self.btn_move_down.clicked.connect(lambda: self._move_app(1))
        self.btn_move_down.setEnabled(False)
        app_btn_layout.addWidget(self.btn_move_down)

        list_layout.addLayout(app_btn_layout)

        apps_layout.addWidget(list_widget)

        # App details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        self.app_details_label = QLabel("Выберите приложение для редактирования")
        self.app_details_label.setWordWrap(True)
        details_layout.addWidget(self.app_details_label)

        self.btn_edit_actions = QPushButton("Редактировать действия")
        self.btn_edit_actions.clicked.connect(self._edit_app_actions)
        self.btn_edit_actions.setEnabled(False)
        details_layout.addWidget(self.btn_edit_actions)

        self.btn_edit_path = QPushButton("Изменить путь")
        self.btn_edit_path.clicked.connect(self._edit_app_path)
        self.btn_edit_path.setEnabled(False)
        details_layout.addWidget(self.btn_edit_path)

        details_layout.addStretch()

        apps_layout.addWidget(details_widget)

        layout.addWidget(apps_group)

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _load_data(self):
        """Load assembly data into UI."""
        self.name_edit.setText(self.assembly.name)
        self.description_edit.setPlainText(self.assembly.description)
        self._refresh_app_list()

    def _refresh_app_list(self):
        """Refresh the app list widget."""
        self.app_list.clear()
        for app in self.assembly.apps:
            actions_count = len(app.actions)
            item_text = f"{app.name} ({actions_count} действий)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, app.app_id)
            item.setToolTip(app.executable_path)
            self.app_list.addItem(item)

    def _get_selected_app(self) -> AppConfig | None:
        """Get currently selected app."""
        items = self.app_list.selectedItems()
        if not items:
            return None

        app_id = items[0].data(Qt.UserRole)
        return self.assembly.get_app(app_id)

    def _on_app_selection_changed(self):
        """Handle app selection change."""
        app = self._get_selected_app()
        has_selection = app is not None

        self.btn_remove_app.setEnabled(has_selection)
        self.btn_move_up.setEnabled(has_selection)
        self.btn_move_down.setEnabled(has_selection)
        self.btn_edit_actions.setEnabled(has_selection)
        self.btn_edit_path.setEnabled(has_selection)

        if app:
            details = f"<b>{app.name}</b><br>"
            details += f"Путь: {app.executable_path}<br>"
            if app.arguments:
                details += f"Аргументы: {app.arguments}<br>"
            details += f"Действий: {len(app.actions)}"
            self.app_details_label.setText(details)
        else:
            self.app_details_label.setText("Выберите приложение для редактирования")

    def _add_app(self):
        """Add a new application."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите приложение",
            "",
            "Исполняемые файлы (*.exe *.sh *.AppImage *);;Все файлы (*)"
        )

        if file_path:
            name = os.path.splitext(os.path.basename(file_path))[0]
            app = AppConfig.create(name, file_path)
            self.assembly.add_app(app)
            self._refresh_app_list()

    def _remove_app(self):
        """Remove selected application."""
        app = self._get_selected_app()
        if not app:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить приложение '{app.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.assembly.remove_app(app.app_id)
            self._refresh_app_list()

    def _move_app(self, direction: int):
        """Move selected app up or down."""
        app = self._get_selected_app()
        if app:
            self.assembly.move_app(app.app_id, direction)
            self._refresh_app_list()

    def _edit_app_actions(self):
        """Edit actions for selected app."""
        app = self._get_selected_app()
        if not app:
            return

        dialog = ActionEditorDialog(app, self)
        if dialog.exec():
            self._refresh_app_list()
            self._on_app_selection_changed()

    def _edit_app_path(self):
        """Change the executable path for selected app."""
        app = self._get_selected_app()
        if not app:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите приложение",
            os.path.dirname(app.executable_path),
            "Исполняемые файлы (*.exe *.sh *.AppImage *);;Все файлы (*)"
        )

        if file_path:
            app.executable_path = file_path
            self._refresh_app_list()
            self._on_app_selection_changed()

    def _save_and_close(self):
        """Save changes and close dialog."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название сборки")
            return

        self.assembly.name = name
        self.assembly.description = self.description_edit.toPlainText().strip()

        self.accept()
