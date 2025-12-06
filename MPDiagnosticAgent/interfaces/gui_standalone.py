#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MPDiagnosticAgent - Standalone GUI
Unified graphical interface combining all previous versions with log download capability

Features:
- Chat interface for diagnostics
- Log download from drone via MAVLink
- Settings management
- Multi-language support (Russian/English)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.diagnostic_engine import DiagnosticEngine
from core.log_downloader import LogDownloader
from core.config import Config


class MPDiagnosticGUI:
    """
    Standalone GUI for MPDiagnosticAgent

    Combines:
    - diagnostic_agent.py - Basic GUI
    - diagnostic_agent_pro.py - Advanced features, terminal styling
    + New: Log download tab
    + New: Settings tab
    """

    def __init__(self):
        # Initialize configuration
        self.config = Config()

        # Detect language
        language = self.config.config.get('diagnostics', {}).get('language', 'auto')
        if language == 'auto':
            language = 'ru'  # Default to Russian
        self.language = language

        # Initialize diagnostic engine
        self.engine = DiagnosticEngine(config=self.config, language=self.language)

        # Log downloader (initialized on demand)
        self.downloader: Optional[LogDownloader] = None

        # Create main window
        self.root = tk.Tk()
        if self.language == 'ru':
            self.root.title("🚁 MPDiagnosticAgent - Диагностический Агент")
        else:
            self.root.title("🚁 MPDiagnosticAgent - Diagnostic Agent")

        self.root.geometry("1000x850")

        # Terminal-like color scheme
        self.bg_color = '#0C0C0C'        # Deep black
        self.fg_color = '#CCCCCC'        # Light gray text
        self.input_bg = '#1E1E1E'        # Dark gray for input
        self.accent_color = '#0078D7'    # Blue accent
        self.success_color = '#16C60C'   # Green
        self.warning_color = '#F9F1A5'   # Yellow
        self.error_color = '#E74856'     # Red
        self.info_color = '#3B78FF'      # Light blue

        self.root.configure(bg=self.bg_color)

        # Create UI
        self.create_header()
        self.create_tabs()
        self.create_status_bar()

        # Show welcome message
        self.show_welcome()

    def create_header(self):
        """Create header bar"""
        header = tk.Frame(self.root, bg=self.accent_color, height=45)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        if self.language == 'ru':
            title_text = "🚁 АГЕНТ ДИАГНОСТИКИ ARDUPILOT • MPDIAGNOSTICAGENT v5.0"
        else:
            title_text = "🚁 ARDUPILOT DIAGNOSTIC AGENT • MPDIAGNOSTICAGENT v5.0"

        header_label = tk.Label(
            header,
            text=title_text,
            font=('Liberation Mono', 11, 'bold'),
            bg=self.accent_color,
            fg='white',
            anchor='w',
            padx=15
        )
        header_label.pack(fill=tk.BOTH, expand=True)

    def create_tabs(self):
        """Create tabbed interface"""
        # Create notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.input_bg, foreground=self.fg_color,
                       padding=[20, 10], font=('Liberation Mono', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.accent_color)],
                 foreground=[('selected', 'white')])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Chat interface
        self.chat_frame = tk.Frame(self.notebook, bg=self.bg_color)
        if self.language == 'ru':
            self.notebook.add(self.chat_frame, text='💬 Чат')
        else:
            self.notebook.add(self.chat_frame, text='💬 Chat')
        self.create_chat_tab()

        # Tab 2: Log download
        self.download_frame = tk.Frame(self.notebook, bg=self.bg_color)
        if self.language == 'ru':
            self.notebook.add(self.download_frame, text='📥 Скачать Логи')
        else:
            self.notebook.add(self.download_frame, text='📥 Download Logs')
        self.create_download_tab()

        # Tab 3: Settings
        self.settings_frame = tk.Frame(self.notebook, bg=self.bg_color)
        if self.language == 'ru':
            self.notebook.add(self.settings_frame, text='⚙️ Настройки')
        else:
            self.notebook.add(self.settings_frame, text='⚙️ Settings')
        self.create_settings_tab()

    def create_chat_tab(self):
        """Create chat interface tab"""
        # Chat display (terminal style)
        self.chat = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=('Liberation Mono', 10),
            bg=self.bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground='#264F78',
            selectforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        self.chat.pack(fill=tk.BOTH, expand=True)
        self.chat.config(state=tk.DISABLED)

        # Configure text tags for colored output
        self.configure_chat_tags()

        # Input frame
        input_frame = tk.Frame(self.chat_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Prompt label
        prompt_label = tk.Label(
            input_frame,
            text="❯",
            font=('Liberation Mono', 12, 'bold'),
            bg=self.bg_color,
            fg=self.success_color
        )
        prompt_label.pack(side=tk.LEFT, padx=(0, 5))

        # Input box
        self.input_box = tk.Text(
            input_frame,
            height=2,
            font=('Liberation Mono', 11),
            bg=self.input_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief=tk.FLAT,
            selectbackground='#264F78',
            padx=10,
            pady=5
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_box.bind('<Return>', self.handle_return)
        self.input_box.bind('<Shift-Return>', lambda e: self.insert_newline())

        # Send button
        send_btn = tk.Label(
            input_frame,
            text="⏎",
            font=('Liberation Mono', 16),
            bg=self.bg_color,
            fg=self.accent_color,
            cursor='hand2',
            padx=10
        )
        send_btn.pack(side=tk.LEFT)
        send_btn.bind('<Button-1>', lambda e: self.send_message())

        self.input_box.focus_set()

    def create_download_tab(self):
        """Create log download tab"""
        # Main container
        container = tk.Frame(self.download_frame, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        if self.language == 'ru':
            title = tk.Label(container, text="СКАЧИВАНИЕ ЛОГОВ С ДРОНА",
                           font=('Liberation Mono', 12, 'bold'),
                           bg=self.bg_color, fg=self.fg_color)
        else:
            title = tk.Label(container, text="DOWNLOAD LOGS FROM DRONE",
                           font=('Liberation Mono', 12, 'bold'),
                           bg=self.bg_color, fg=self.fg_color)
        title.pack(pady=(0, 20))

        # Connection section
        conn_frame = tk.LabelFrame(container, text="1. Connection" if self.language == 'en' else "1. Подключение",
                                  bg=self.bg_color, fg=self.fg_color,
                                  font=('Liberation Mono', 10, 'bold'))
        conn_frame.pack(fill=tk.X, pady=10)

        # Port selection
        port_row = tk.Frame(conn_frame, bg=self.bg_color)
        port_row.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(port_row, text="Port:" if self.language == 'en' else "Порт:",
                bg=self.bg_color, fg=self.fg_color, font=('Liberation Mono', 10)).pack(side=tk.LEFT)

        self.port_var = tk.StringVar(value=self.config.mavlink_port)
        port_entry = tk.Entry(port_row, textvariable=self.port_var, bg=self.input_bg,
                             fg=self.fg_color, font=('Liberation Mono', 10), width=20)
        port_entry.pack(side=tk.LEFT, padx=10)

        # Connect button
        self.connect_btn = tk.Button(
            port_row,
            text="Connect" if self.language == 'en' else "Подключить",
            command=self.connect_to_drone,
            bg=self.accent_color,
            fg='white',
            font=('Liberation Mono', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor='hand2'
        )
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        # Connection status
        self.conn_status = tk.Label(conn_frame, text="⚪ Not connected" if self.language == 'en' else "⚪ Не подключено",
                                   bg=self.bg_color, fg=self.warning_color, font=('Liberation Mono', 10))
        self.conn_status.pack(padx=10, pady=5)

        # Log list section
        list_frame = tk.LabelFrame(container, text="2. Available Logs" if self.language == 'en' else "2. Доступные логи",
                                  bg=self.bg_color, fg=self.fg_color,
                                  font=('Liberation Mono', 10, 'bold'))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Log listbox
        list_container = tk.Frame(list_frame, bg=self.bg_color)
        list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_listbox = tk.Listbox(list_container, bg=self.input_bg, fg=self.fg_color,
                                      font=('Liberation Mono', 10), yscrollcommand=scrollbar.set,
                                      selectbackground=self.accent_color)
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_listbox.yview)

        # Buttons
        btn_frame = tk.Frame(list_frame, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.list_btn = tk.Button(
            btn_frame,
            text="List Logs" if self.language == 'en' else "Список логов",
            command=self.list_logs,
            bg=self.input_bg,
            fg=self.fg_color,
            font=('Liberation Mono', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        self.list_btn.pack(side=tk.LEFT, padx=5)

        self.download_btn = tk.Button(
            btn_frame,
            text="Download Selected" if self.language == 'en' else "Скачать выбранный",
            command=self.download_selected_log,
            bg=self.success_color,
            fg='black',
            font=('Liberation Mono', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor='hand2'
        )
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # Progress section
        progress_frame = tk.LabelFrame(container, text="3. Progress" if self.language == 'en' else "3. Прогресс",
                                      bg=self.bg_color, fg=self.fg_color,
                                      font=('Liberation Mono', 10, 'bold'))
        progress_frame.pack(fill=tk.X, pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)

        self.progress_label = tk.Label(progress_frame, text="Ready" if self.language == 'en' else "Готов",
                                      bg=self.bg_color, fg=self.fg_color, font=('Liberation Mono', 10))
        self.progress_label.pack(padx=10, pady=5)

    def create_settings_tab(self):
        """Create settings tab"""
        # Main container
        container = tk.Frame(self.settings_frame, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        if self.language == 'ru':
            title = tk.Label(container, text="НАСТРОЙКИ",
                           font=('Liberation Mono', 12, 'bold'),
                           bg=self.bg_color, fg=self.fg_color)
        else:
            title = tk.Label(container, text="SETTINGS",
                           font=('Liberation Mono', 12, 'bold'),
                           bg=self.bg_color, fg=self.fg_color)
        title.pack(pady=(0, 20))

        # Mission Planner path
        mp_frame = tk.LabelFrame(container, text="Mission Planner",
                                bg=self.bg_color, fg=self.fg_color,
                                font=('Liberation Mono', 10, 'bold'))
        mp_frame.pack(fill=tk.X, pady=10)

        mp_path_label = tk.Label(mp_frame,
                                text=f"Path: {self.config.mission_planner_path}",
                                bg=self.bg_color, fg=self.success_color,
                                font=('Liberation Mono', 9))
        mp_path_label.pack(padx=10, pady=10, anchor='w')

        # MAVLink settings
        mavlink_frame = tk.LabelFrame(container, text="MAVLink Connection",
                                     bg=self.bg_color, fg=self.fg_color,
                                     font=('Liberation Mono', 10, 'bold'))
        mavlink_frame.pack(fill=tk.X, pady=10)

        # Default port
        port_row = tk.Frame(mavlink_frame, bg=self.bg_color)
        port_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(port_row, text="Default Port:",
                bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 10)).pack(side=tk.LEFT)

        tk.Label(port_row, text=self.config.mavlink_port,
                bg=self.bg_color, fg=self.info_color,
                font=('Liberation Mono', 10)).pack(side=tk.LEFT, padx=10)

        # Baudrate
        baud_row = tk.Frame(mavlink_frame, bg=self.bg_color)
        baud_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(baud_row, text="Baudrate:",
                bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 10)).pack(side=tk.LEFT)

        baudrate = self.config.config.get('mavlink', {}).get('baudrate', 921600)
        tk.Label(baud_row, text=str(baudrate),
                bg=self.bg_color, fg=self.info_color,
                font=('Liberation Mono', 10)).pack(side=tk.LEFT, padx=10)

        # Language settings
        lang_frame = tk.LabelFrame(container, text="Language / Язык",
                                  bg=self.bg_color, fg=self.fg_color,
                                  font=('Liberation Mono', 10, 'bold'))
        lang_frame.pack(fill=tk.X, pady=10)

        current_lang = "Русский" if self.language == 'ru' else "English"
        tk.Label(lang_frame, text=f"Current: {current_lang}",
                bg=self.bg_color, fg=self.info_color,
                font=('Liberation Mono', 10)).pack(padx=10, pady=10)

        # Config file location
        info_frame = tk.LabelFrame(container, text="Configuration File",
                                  bg=self.bg_color, fg=self.fg_color,
                                  font=('Liberation Mono', 10, 'bold'))
        info_frame.pack(fill=tk.X, pady=10)

        tk.Label(info_frame, text=str(self.config.config_file),
                bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 9), wraplength=700).pack(padx=10, pady=10, anchor='w')

    def create_status_bar(self):
        """Create bottom status bar"""
        self.status_frame = tk.Frame(self.root, bg='#1E1E1E', height=25)
        self.status_frame.pack(fill=tk.X)
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_frame,
            text="● Ready | Готов",
            font=('Liberation Mono', 9),
            bg='#1E1E1E',
            fg=self.success_color,
            anchor='w',
            padx=15
        )
        self.status_label.pack(side=tk.LEFT)

    def configure_chat_tags(self):
        """Configure text tags for syntax highlighting"""
        self.chat.tag_config('timestamp', foreground='#6A9955')
        self.chat.tag_config('prompt', foreground=self.success_color, font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('user', foreground='#4EC9B0', font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('agent', foreground='#DCDCAA', font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('success', foreground=self.success_color)
        self.chat.tag_config('warning', foreground=self.warning_color)
        self.chat.tag_config('error', foreground=self.error_color)
        self.chat.tag_config('info', foreground=self.info_color)
        self.chat.tag_config('code', foreground='#CE9178', font=('Liberation Mono', 9))
        self.chat.tag_config('header', foreground='white', font=('Liberation Mono', 10, 'bold'))

    def show_welcome(self):
        """Show welcome message in chat"""
        if self.language == 'ru':
            welcome = """
╔══════════════════════════════════════════════════════════════════╗
║          АГЕНТ ДИАГНОСТИКИ ARDUPILOT v5.0                        ║
║          ARDUPILOT DIAGNOSTIC AGENT v5.0                         ║
╚══════════════════════════════════════════════════════════════════╝

✓ Анализ реальных данных Mission Planner
✓ Скачивание логов с дрона через MAVLink
✓ Интеграция с ArduPilot Wiki
✓ Русский + English

БЫСТРЫЙ СТАРТ:
  статус          - полный анализ состояния дрона
  моторы          - диагностика моторов и арминга
  вибрации        - анализ вибраций
  компас          - диагностика компаса
  wiki <тема>     - поиск в документации
  помощь          - показать все команды

Просто опишите проблему, я проанализирую логи и данные!
"""
        else:
            welcome = """
╔══════════════════════════════════════════════════════════════════╗
║          ARDUPILOT DIAGNOSTIC AGENT v5.0                         ║
╚══════════════════════════════════════════════════════════════════╝

✓ Analyze real Mission Planner data
✓ Download logs from drone via MAVLink
✓ ArduPilot Wiki integration
✓ Russian + English support

QUICK START:
  status          - full drone health check
  motors          - diagnose motor/arming issues
  vibrations      - analyze vibrations
  compass         - diagnose compass
  wiki <topic>    - search documentation
  help            - show all commands

Just describe your problem, I'll analyze logs and data!
"""
        self.add_system_message(welcome)

    def add_system_message(self, text):
        """Add system message to chat"""
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, text + '\n', 'info')
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def add_message(self, sender, text, sender_tag='user'):
        """Add formatted message to chat"""
        self.chat.config(state=tk.NORMAL)

        # Timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat.insert(tk.END, f'\n[{timestamp}] ', 'timestamp')

        # Sender
        self.chat.insert(tk.END, f'{sender}\n', sender_tag)

        # Auto-format message
        self.format_message(text)

        self.chat.insert(tk.END, '\n')
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def format_message(self, text):
        """Auto-format message with syntax highlighting"""
        lines = text.split('\n')
        for line in lines:
            if line.startswith('✓') or line.startswith('✅'):
                self.chat.insert(tk.END, line + '\n', 'success')
            elif line.startswith('⚠') or line.startswith('❌') or line.startswith('✗'):
                self.chat.insert(tk.END, line + '\n', 'warning')
            elif 'ERROR' in line or 'CRITICAL' in line:
                self.chat.insert(tk.END, line + '\n', 'error')
            elif line.startswith('═') or line.startswith('─'):
                self.chat.insert(tk.END, line + '\n', 'header')
            elif line.startswith('  ') and ':' in line:
                self.chat.insert(tk.END, line + '\n', 'code')
            else:
                self.chat.insert(tk.END, line + '\n')

    def handle_return(self, event):
        """Handle Enter key"""
        if not event.state & 0x1:  # Not Shift
            self.send_message()
            return 'break'
        return None

    def insert_newline(self):
        """Insert newline in input"""
        self.input_box.insert(tk.INSERT, '\n')
        return 'break'

    def send_message(self):
        """Send user message and get response"""
        msg = self.input_box.get('1.0', tk.END).strip()
        if not msg:
            return

        # Add user message
        if self.language == 'ru':
            self.add_message("❯ ВЫ", msg, 'user')
        else:
            self.add_message("❯ YOU", msg, 'user')

        self.input_box.delete('1.0', tk.END)
        self.input_box.focus_set()

        # Update status
        if self.language == 'ru':
            self.update_status("● Анализирую...", self.warning_color)
        else:
            self.update_status("● Analyzing...", self.warning_color)
        self.root.update()

        try:
            # Process query through diagnostic engine
            response = self.engine.process_query(msg)

            if self.language == 'ru':
                self.add_message("🤖 АГЕНТ", response, 'agent')
                self.update_status("● Готов", self.success_color)
            else:
                self.add_message("🤖 AGENT", response, 'agent')
                self.update_status("● Ready", self.success_color)
        except Exception as e:
            if self.language == 'ru':
                error_msg = f"❌ Ошибка: {str(e)}"
                self.add_message("⚠ СИСТЕМА", error_msg, 'error')
                self.update_status("● Ошибка", self.error_color)
            else:
                error_msg = f"❌ Error: {str(e)}"
                self.add_message("⚠ SYSTEM", error_msg, 'error')
                self.update_status("● Error", self.error_color)

    def update_status(self, text, color=None):
        """Update status bar"""
        if color is None:
            color = self.success_color
        self.status_label.config(text=text, fg=color)

    # Log download functionality
    def connect_to_drone(self):
        """Connect to drone"""
        port = self.port_var.get()

        if self.language == 'ru':
            self.update_status(f"● Подключение к {port}...", self.warning_color)
        else:
            self.update_status(f"● Connecting to {port}...", self.warning_color)
        self.root.update()

        try:
            # Create downloader with specified port
            from core.config import Config
            temp_config = Config()
            temp_config.config['mavlink']['default_port'] = port

            self.downloader = LogDownloader(config=temp_config)

            # Try to connect
            if self.downloader.connect():
                if self.language == 'ru':
                    self.conn_status.config(text="✓ Подключено", fg=self.success_color)
                    self.update_status("● Подключено к дрону", self.success_color)
                else:
                    self.conn_status.config(text="✓ Connected", fg=self.success_color)
                    self.update_status("● Connected to drone", self.success_color)

                self.connect_btn.config(state=tk.DISABLED)
            else:
                raise Exception("Failed to connect")
        except Exception as e:
            if self.language == 'ru':
                self.conn_status.config(text=f"✗ Ошибка: {str(e)}", fg=self.error_color)
                self.update_status("● Ошибка подключения", self.error_color)
                messagebox.showerror("Ошибка", f"Не удалось подключиться к дрону:\n{str(e)}")
            else:
                self.conn_status.config(text=f"✗ Error: {str(e)}", fg=self.error_color)
                self.update_status("● Connection error", self.error_color)
                messagebox.showerror("Error", f"Failed to connect to drone:\n{str(e)}")

    def list_logs(self):
        """List logs on drone"""
        if not self.downloader or not self.downloader.mav.is_connected():
            if self.language == 'ru':
                messagebox.showwarning("Предупреждение", "Сначала подключитесь к дрону")
            else:
                messagebox.showwarning("Warning", "Connect to drone first")
            return

        if self.language == 'ru':
            self.update_status("● Получение списка логов...", self.warning_color)
        else:
            self.update_status("● Fetching log list...", self.warning_color)
        self.root.update()

        try:
            logs = self.downloader.list_logs()

            # Clear listbox
            self.log_listbox.delete(0, tk.END)

            # Add logs to listbox
            for log in logs:
                size_kb = log.size / 1024
                self.log_listbox.insert(tk.END, f"Log {log.id}: {size_kb:.1f} KB")

            # Store log objects
            self.available_logs = logs

            if self.language == 'ru':
                self.update_status(f"● Найдено {len(logs)} логов", self.success_color)
            else:
                self.update_status(f"● Found {len(logs)} logs", self.success_color)
        except Exception as e:
            if self.language == 'ru':
                self.update_status("● Ошибка", self.error_color)
                messagebox.showerror("Ошибка", f"Не удалось получить список логов:\n{str(e)}")
            else:
                self.update_status("● Error", self.error_color)
                messagebox.showerror("Error", f"Failed to list logs:\n{str(e)}")

    def download_selected_log(self):
        """Download selected log"""
        selection = self.log_listbox.curselection()
        if not selection:
            if self.language == 'ru':
                messagebox.showwarning("Предупреждение", "Выберите лог для скачивания")
            else:
                messagebox.showwarning("Warning", "Select a log to download")
            return

        log_index = selection[0]
        log = self.available_logs[log_index]

        # Progress callback
        def progress_callback(bytes_done, total_bytes):
            percent = (bytes_done / total_bytes) * 100
            self.progress_var.set(percent)
            if self.language == 'ru':
                self.progress_label.config(text=f"Скачано: {bytes_done}/{total_bytes} байт ({percent:.1f}%)")
            else:
                self.progress_label.config(text=f"Downloaded: {bytes_done}/{total_bytes} bytes ({percent:.1f}%)")
            self.root.update()

        if self.language == 'ru':
            self.update_status(f"● Скачивание лога {log.id}...", self.warning_color)
        else:
            self.update_status(f"● Downloading log {log.id}...", self.warning_color)

        try:
            log_file = self.downloader.download_log(log.id, progress_callback=progress_callback)

            if log_file:
                if self.language == 'ru':
                    self.update_status("● Скачивание завершено", self.success_color)
                    messagebox.showinfo("Успех", f"Лог скачан:\n{log_file}")
                else:
                    self.update_status("● Download complete", self.success_color)
                    messagebox.showinfo("Success", f"Log downloaded:\n{log_file}")

                self.progress_var.set(0)
                if self.language == 'ru':
                    self.progress_label.config(text="Готов")
                else:
                    self.progress_label.config(text="Ready")
            else:
                raise Exception("Download failed")
        except Exception as e:
            if self.language == 'ru':
                self.update_status("● Ошибка", self.error_color)
                messagebox.showerror("Ошибка", f"Не удалось скачать лог:\n{str(e)}")
            else:
                self.update_status("● Error", self.error_color)
                messagebox.showerror("Error", f"Failed to download log:\n{str(e)}")

            self.progress_var.set(0)
            if self.language == 'ru':
                self.progress_label.config(text="Ошибка")
            else:
                self.progress_label.config(text="Error")

    def run(self):
        """Run the GUI"""
        self.root.mainloop()

    def __del__(self):
        """Cleanup on exit"""
        if self.downloader:
            self.downloader.disconnect()


# Entry point
if __name__ == '__main__':
    app = MPDiagnosticGUI()
    app.run()
