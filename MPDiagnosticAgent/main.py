#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MPDiagnosticAgent - Main Unified Application
All-in-one intelligent diagnostic tool for ArduPilot drones

Features:
- AI-powered natural language assistance
- Automatic problem detection and fixes
- Log download via MAVLink
- Real-time parameter management
- Cross-platform support
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from core.unified_agent import UnifiedAgent, FixAction
from core.config import Config
from core.mavlink_interface import MAVLinkInterface
from core.log_downloader import LogDownloader


class MPDiagnosticApp:
    """
    Unified MPDiagnostic Application

    Combines all features:
    - AI chat assistant
    - Auto-fix with one click
    - Log download
    - Settings management
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚁 ArduPilot Unified Diagnostic Agent v6.0")
        self.root.geometry("1400x900")

        # Theme colors (dark)
        self.bg_color = '#1e1e1e'
        self.fg_color = '#d4d4d4'
        self.accent_color = '#007acc'
        self.success_color = '#4ec9b0'
        self.warning_color = '#dcdcaa'
        self.error_color = '#f48771'
        self.input_bg = '#252526'
        self.button_bg = '#0e639c'
        self.card_bg = '#2d2d30'

        self.root.configure(bg=self.bg_color)

        # Initialize components
        try:
            self.config = Config()
            self.agent = UnifiedAgent(config=self.config)
            self.downloader = None
            self.connected = False
        except Exception as e:
            messagebox.showerror("Init Error", f"Failed to initialize: {e}")
            sys.exit(1)

        # State
        self.pending_fixes = []
        self.current_logs = []

        # Create UI
        self.create_ui()

        # Auto-start analysis
        self.root.after(1000, self.auto_analyze)

    def create_ui(self):
        """Create main UI with tabs"""
        # Header
        self.create_header()

        # Tab control
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Style for tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.card_bg, foreground=self.fg_color,
                       padding=[20, 10], font=('Liberation Mono', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.accent_color)],
                 foreground=[('selected', 'white')])

        # Create tabs
        self.create_ai_assistant_tab()
        self.create_autofix_tab()
        self.create_download_tab()
        self.create_settings_tab()

    def create_header(self):
        """Create header with connection status"""
        header = tk.Frame(self.root, bg=self.accent_color, height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)

        # Title
        title_frame = tk.Frame(header, bg=self.accent_color)
        title_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(title_frame, text="🚁 ArduPilot Diagnostic Agent",
                bg=self.accent_color, fg='white',
                font=('Liberation Mono', 16, 'bold')).pack(anchor='w')

        tk.Label(title_frame, text="v6.0 Unified • AI-Powered",
                bg=self.accent_color, fg='#c0c0c0',
                font=('Liberation Mono', 8)).pack(anchor='w')

        # Connection controls
        conn_frame = tk.Frame(header, bg=self.accent_color)
        conn_frame.pack(side=tk.RIGHT, padx=20)

        # Port selector
        ports = MAVLinkInterface.find_available_ports()
        if ports:
            self.port_var = tk.StringVar(value=ports[0])
            port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var,
                                     values=ports, width=12, font=('Liberation Mono', 9))
            port_combo.pack(side=tk.LEFT, padx=5)
        else:
            self.port_var = tk.StringVar(value=self.config.mavlink_port)
            port_entry = tk.Entry(conn_frame, textvariable=self.port_var,
                                 bg='white', font=('Liberation Mono', 9), width=12)
            port_entry.pack(side=tk.LEFT, padx=5)

        # Connection status
        self.conn_label = tk.Label(conn_frame, text="⚪ Disconnected",
                                   bg=self.accent_color, fg='white',
                                   font=('Liberation Mono', 9, 'bold'))
        self.conn_label.pack(side=tk.LEFT, padx=10)

        # Connect button
        self.conn_btn = tk.Button(conn_frame, text="Connect",
                                  command=self.toggle_connection,
                                  bg='white', fg=self.accent_color,
                                  font=('Liberation Mono', 9, 'bold'),
                                  relief=tk.FLAT, padx=15, pady=5, cursor='hand2')
        self.conn_btn.pack(side=tk.LEFT)

    def create_ai_assistant_tab(self):
        """Tab 1: AI Assistant"""
        tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab, text="💬 AI Assistant")

        # Main container
        container = tk.Frame(tab, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Chat area
        chat_frame = tk.Frame(container, bg=self.bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat = scrolledtext.ScrolledText(chat_frame, bg=self.input_bg,
                                              fg=self.fg_color,
                                              font=('Liberation Mono', 10),
                                              wrap=tk.WORD, state=tk.DISABLED,
                                              relief=tk.FLAT, padx=15, pady=15)
        self.chat.pack(fill=tk.BOTH, expand=True)

        # Tags
        self.chat.tag_config('user', foreground=self.accent_color, font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('agent', foreground=self.success_color, font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('timestamp', foreground='#858585', font=('Liberation Mono', 8))
        self.chat.tag_config('error', foreground=self.error_color)
        self.chat.tag_config('success', foreground=self.success_color)
        self.chat.tag_config('warning', foreground=self.warning_color)

        # Welcome message
        self.add_agent_message(
            "👋 Здравствуйте! Я - Интеллектуальный Агент Диагностики ArduPilot.\n\n"
            "Спросите меня о чём угодно:\n\n"
            "💡 Примеры вопросов:\n"
            "  • 'Почему дрон не взлетает?'\n"
            "  • 'Что означает RC not found?'\n"
            "  • 'Как исправить проблемы с компасом?'\n"
            "  • 'Покажи логи'\n"
            "  • 'Какие ошибки в логах?'\n\n"
            "Я проанализирую ваши логи, объясню проблемы и предложу решения!\n\n"
            "Переключитесь на вкладку '🔧 Auto-Fix' чтобы увидеть автоматические исправления."
        )

        # Input area
        input_frame = tk.Frame(container, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=(15, 0))

        self.input_var = tk.StringVar()
        input_entry = tk.Entry(input_frame, textvariable=self.input_var,
                              bg=self.input_bg, fg=self.fg_color,
                              font=('Liberation Mono', 11), relief=tk.FLAT,
                              insertbackground=self.fg_color)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
        input_entry.bind('<Return>', lambda e: self.send_message())
        input_entry.focus()

        send_btn = tk.Button(input_frame, text="Send ➤",
                            command=self.send_message,
                            bg=self.accent_color, fg='white',
                            font=('Liberation Mono', 10, 'bold'),
                            relief=tk.FLAT, padx=25, pady=10, cursor='hand2')
        send_btn.pack(side=tk.RIGHT)

    def create_autofix_tab(self):
        """Tab 2: Auto-Fix"""
        tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab, text="🔧 Auto-Fix")

        container = tk.Frame(tab, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg=self.bg_color)
        header.pack(fill=tk.X, pady=(0, 15))

        tk.Label(header, text="🔧 Automatic Fixes",
                bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 14, 'bold')).pack(side=tk.LEFT)

        self.fixes_count_label = tk.Label(header, text="Analyzing...",
                                          bg=self.bg_color, fg=self.warning_color,
                                          font=('Liberation Mono', 11))
        self.fixes_count_label.pack(side=tk.LEFT, padx=15)

        # Refresh button
        refresh_btn = tk.Button(header, text="🔄 Refresh",
                               command=self.refresh_fixes,
                               bg=self.button_bg, fg='white',
                               font=('Liberation Mono', 9, 'bold'),
                               relief=tk.FLAT, padx=15, pady=5, cursor='hand2')
        refresh_btn.pack(side=tk.RIGHT)

        # Scrollable fixes
        canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.fixes_container = tk.Frame(canvas, bg=self.bg_color)

        self.fixes_container.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.fixes_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_download_tab(self):
        """Tab 3: Download Logs"""
        tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab, text="📥 Download Logs")

        container = tk.Frame(tab, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Instructions
        info = tk.Label(container,
                       text="Download dataflash logs from drone via MAVLink\n"
                            "Connect to drone first, then click 'List Logs'",
                       bg=self.bg_color, fg=self.fg_color,
                       font=('Liberation Mono', 10), justify=tk.LEFT)
        info.pack(anchor='w', pady=(0, 15))

        # Controls
        ctrl_frame = tk.Frame(container, bg=self.bg_color)
        ctrl_frame.pack(fill=tk.X, pady=(0, 15))

        list_btn = tk.Button(ctrl_frame, text="📋 List Logs",
                            command=self.list_drone_logs,
                            bg=self.button_bg, fg='white',
                            font=('Liberation Mono', 10, 'bold'),
                            relief=tk.FLAT, padx=20, pady=8, cursor='hand2')
        list_btn.pack(side=tk.LEFT, padx=(0, 10))

        download_btn = tk.Button(ctrl_frame, text="⬇️ Download Selected",
                                command=self.download_selected_log,
                                bg=self.success_color, fg='white',
                                font=('Liberation Mono', 10, 'bold'),
                                relief=tk.FLAT, padx=20, pady=8, cursor='hand2')
        download_btn.pack(side=tk.LEFT)

        # Logs list
        list_frame = tk.Frame(container, bg=self.bg_color)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.logs_listbox = tk.Listbox(list_frame, bg=self.input_bg,
                                       fg=self.fg_color,
                                       font=('Liberation Mono', 10),
                                       relief=tk.FLAT, selectmode=tk.SINGLE)
        self.logs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                 command=self.logs_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.logs_listbox.configure(yscrollcommand=scrollbar.set)

        # Progress
        self.download_progress_label = tk.Label(container, text="",
                                                bg=self.bg_color, fg=self.success_color,
                                                font=('Liberation Mono', 9))
        self.download_progress_label.pack(pady=(10, 0))

    def create_settings_tab(self):
        """Tab 4: Settings"""
        tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab, text="⚙️ Settings")

        container = tk.Frame(tab, bg=self.bg_color)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Mission Planner info
        mp_frame = tk.LabelFrame(container, text="Mission Planner Detection",
                                bg=self.bg_color, fg=self.fg_color,
                                font=('Liberation Mono', 11, 'bold'))
        mp_frame.pack(fill=tk.X, pady=(0, 15))

        mp_path = self.config.mission_planner_path
        if mp_path:
            tk.Label(mp_frame, text=f"✓ Found: {mp_path}",
                    bg=self.bg_color, fg=self.success_color,
                    font=('Liberation Mono', 9)).pack(padx=15, pady=10, anchor='w')
        else:
            tk.Label(mp_frame, text="⚠ Not detected",
                    bg=self.bg_color, fg=self.warning_color,
                    font=('Liberation Mono', 9)).pack(padx=15, pady=10, anchor='w')

        # Log paths
        paths_frame = tk.LabelFrame(container, text="Log Locations",
                                   bg=self.bg_color, fg=self.fg_color,
                                   font=('Liberation Mono', 11, 'bold'))
        paths_frame.pack(fill=tk.X, pady=(0, 15))

        paths = self.config.get_log_paths()
        for name, path in paths.items():
            row = tk.Frame(paths_frame, bg=self.bg_color)
            row.pack(fill=tk.X, padx=15, pady=5)

            tk.Label(row, text=f"{name}:", bg=self.bg_color, fg=self.fg_color,
                    font=('Liberation Mono', 9), width=15, anchor='w').pack(side=tk.LEFT)

            exists = path and path.exists()
            color = self.success_color if exists else self.warning_color
            status = "✓" if exists else "✗"

            tk.Label(row, text=f"{status} {path}", bg=self.bg_color, fg=color,
                    font=('Liberation Mono', 8)).pack(side=tk.LEFT, padx=10)

        # MAVLink settings
        mav_frame = tk.LabelFrame(container, text="MAVLink Settings",
                                 bg=self.bg_color, fg=self.fg_color,
                                 font=('Liberation Mono', 11, 'bold'))
        mav_frame.pack(fill=tk.X, pady=(0, 15))

        mav_info = [
            ("Default Port:", self.config.mavlink_port),
            ("Baudrate:", f"{self.config.mavlink_baudrate} bps"),
            ("Timeout:", f"{self.config.mavlink_timeout}s"),
        ]

        for label, value in mav_info:
            row = tk.Frame(mav_frame, bg=self.bg_color)
            row.pack(fill=tk.X, padx=15, pady=5)

            tk.Label(row, text=label, bg=self.bg_color, fg=self.fg_color,
                    font=('Liberation Mono', 9), width=15, anchor='w').pack(side=tk.LEFT)

            tk.Label(row, text=value, bg=self.bg_color, fg=self.success_color,
                    font=('Liberation Mono', 9)).pack(side=tk.LEFT, padx=10)

    # === Event Handlers ===

    def toggle_connection(self):
        """Toggle drone connection"""
        if self.connected:
            # Disconnect
            if self.agent.mav:
                self.agent.mav.disconnect()
            self.connected = False
            self.conn_label.config(text="⚪ Disconnected", fg='white')
            self.conn_btn.config(text="Connect")
            self.add_agent_message("🔌 Disconnected from drone")
        else:
            # Connect
            port = self.port_var.get()
            self.add_agent_message(f"🔌 Connecting to {port}...")

            if self.agent.connect_to_drone(port):
                self.connected = True
                self.conn_label.config(text="🟢 Connected", fg='#4ec9b0')
                self.conn_btn.config(text="Disconnect")
                self.add_agent_message(f"✅ Connected! Auto-fix now available.")

                # Create downloader
                self.downloader = LogDownloader(mavlink_interface=self.agent.mav,
                                               config=self.config)
            else:
                self.add_agent_message("❌ Connection failed. Check port and permissions.")

    def send_message(self):
        """Send message to AI agent"""
        message = self.input_var.get().strip()
        if not message:
            return

        self.input_var.set('')
        self.add_user_message(message)

        try:
            answer = self.agent.answer_question(message)
            self.add_agent_message(answer)

            # Update fixes if relevant
            if 'исправ' in message.lower() or 'fix' in message.lower():
                self.refresh_fixes()

        except Exception as e:
            self.add_agent_message(f"❌ Error: {e}")

    def add_user_message(self, text):
        """Add user message to chat"""
        self.chat.config(state=tk.NORMAL)
        ts = datetime.now().strftime('%H:%M:%S')
        self.chat.insert(tk.END, f'\n[{ts}] ', 'timestamp')
        self.chat.insert(tk.END, 'You: ', 'user')
        self.chat.insert(tk.END, f'{text}\n')
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def add_agent_message(self, text):
        """Add agent message to chat"""
        self.chat.config(state=tk.NORMAL)
        ts = datetime.now().strftime('%H:%M:%S')
        self.chat.insert(tk.END, f'\n[{ts}] ', 'timestamp')
        self.chat.insert(tk.END, 'Agent: ', 'agent')

        for line in text.split('\n'):
            if line.startswith(('✓', '✅')):
                self.chat.insert(tk.END, line + '\n', 'success')
            elif line.startswith(('⚠', '❌', '✗')):
                self.chat.insert(tk.END, line + '\n', 'error')
            elif line.startswith(('🔴', '🟡')):
                self.chat.insert(tk.END, line + '\n', 'warning')
            else:
                self.chat.insert(tk.END, line + '\n')

        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def auto_analyze(self):
        """Auto-analyze on startup"""
        try:
            report = self.agent.analyze_current_state()
            self.pending_fixes = report['fixable_issues']

            error_count = len(report['prearm_errors'])
            fix_count = len(self.pending_fixes)

            if error_count == 0:
                self.add_agent_message("✅ Анализ завершён: проблем не найдено!")
            else:
                self.add_agent_message(
                    f"🔍 Анализ завершён:\n"
                    f"• Найдено {error_count} проблем\n"
                    f"• Доступно {fix_count} автоматических исправлений\n\n"
                    f"Посмотрите вкладку '🔧 Auto-Fix' чтобы применить исправления!"
                )

            self.refresh_fixes()

        except Exception as e:
            self.add_agent_message(f"⚠ Auto-analysis error: {e}")

    def refresh_fixes(self):
        """Refresh auto-fix tab"""
        # Clear
        for widget in self.fixes_container.winfo_children():
            widget.destroy()

        # Re-analyze to get fresh results
        try:
            report = self.agent.analyze_current_state()
            self.pending_fixes = report['fixable_issues']
        except Exception as e:
            tk.Label(self.fixes_container, text=f"❌ Analysis error: {e}",
                    bg=self.bg_color, fg=self.error_color,
                    font=('Liberation Mono', 10)).pack(pady=50)
            self.fixes_count_label.config(text="❌ Error", fg=self.error_color)
            return

        if not self.pending_fixes:
            tk.Label(self.fixes_container, text="✅ No fixes needed!\n\nAll systems normal.",
                    bg=self.bg_color, fg=self.success_color,
                    font=('Liberation Mono', 12, 'bold'), justify=tk.CENTER).pack(pady=50)
            self.fixes_count_label.config(text="✅ No issues", fg=self.success_color)
            return

        self.fixes_count_label.config(
            text=f"Found {len(self.pending_fixes)} fixes",
            fg=self.warning_color
        )

        # Add fix cards
        for i, fix in enumerate(self.pending_fixes):
            self.create_fix_card(fix, i)

    def create_fix_card(self, fix: FixAction, index: int):
        """Create fix card"""
        sev_colors = {
            'low': '#4ec9b0', 'medium': '#dcdcaa',
            'high': '#ce9178', 'critical': '#f48771'
        }

        card = tk.Frame(self.fixes_container, bg=self.card_bg,
                       relief=tk.RAISED, borderwidth=1)
        card.pack(fill=tk.X, pady=8)

        # Header
        header = tk.Frame(card, bg=self.card_bg)
        header.pack(fill=tk.X, padx=15, pady=(12, 5))

        tk.Label(header, text=f"#{index+1}", bg=self.card_bg, fg='#858585',
                font=('Liberation Mono', 8)).pack(side=tk.LEFT)

        tk.Label(header, text=fix.severity.upper(),
                bg=sev_colors.get(fix.severity, '#dcdcaa'), fg='#1e1e1e',
                font=('Liberation Mono', 7, 'bold'),
                padx=6, pady=2).pack(side=tk.RIGHT)

        # Title
        tk.Label(card, text=fix.title, bg=self.card_bg, fg=self.fg_color,
                font=('Liberation Mono', 11, 'bold'),
                wraplength=1200, justify=tk.LEFT).pack(anchor='w', padx=15, pady=(0, 8))

        # Description
        tk.Label(card, text=fix.description, bg=self.card_bg, fg='#a8a8a8',
                font=('Liberation Mono', 9), wraplength=1200,
                justify=tk.LEFT).pack(anchor='w', padx=15, pady=(0, 8))

        # Params
        tk.Label(card, text=f"Will change {len(fix.params)} parameters",
                bg=self.card_bg, fg='#6a9955',
                font=('Liberation Mono', 8, 'italic')).pack(anchor='w', padx=15, pady=(0, 12))

        # Button
        if fix.applied:
            btn = tk.Button(card, text="✓ Applied", bg=self.success_color,
                           fg='white', font=('Liberation Mono', 10, 'bold'),
                           relief=tk.FLAT, padx=20, pady=8, state=tk.DISABLED)
        else:
            btn = tk.Button(card, text="Apply Fix", bg=self.accent_color,
                           fg='white', font=('Liberation Mono', 10, 'bold'),
                           relief=tk.FLAT, padx=20, pady=8, cursor='hand2',
                           command=lambda f=fix: self.apply_fix(f))

        btn.pack(fill=tk.X, padx=15, pady=(0, 12))

    def apply_fix(self, fix: FixAction):
        """Apply a fix"""
        if not self.connected:
            messagebox.showwarning("Not Connected",
                "Please connect to drone first!\nClick 'Connect' in the header.")
            return

        params_list = "\n".join([f"• {k} = {v}" for k, v in fix.params.items()])
        if not messagebox.askyesno("Confirm", f"{fix.title}\n\n{params_list}\n\nContinue?"):
            return

        self.add_agent_message(f"🔧 Applying: {fix.title}...")

        if self.agent.apply_fix(fix):
            self.add_agent_message(f"✅ Successfully applied!")
            self.refresh_fixes()
        else:
            self.add_agent_message(f"❌ Failed. Check connection.")

    def list_drone_logs(self):
        """List logs on drone"""
        if not self.connected or not self.downloader:
            messagebox.showwarning("Not Connected", "Please connect to drone first!")
            return

        self.download_progress_label.config(text="📋 Listing logs...")
        self.logs_listbox.delete(0, tk.END)

        try:
            self.current_logs = self.downloader.list_logs()

            if not self.current_logs:
                self.download_progress_label.config(text="⚠ No logs found on drone")
                return

            for log in self.current_logs:
                size_kb = log.size / 1024
                self.logs_listbox.insert(tk.END,
                    f"Log #{log.id} - {size_kb:.1f} KB")

            self.download_progress_label.config(
                text=f"✓ Found {len(self.current_logs)} logs")

        except Exception as e:
            self.download_progress_label.config(text=f"✗ Error: {e}")

    def download_selected_log(self):
        """Download selected log"""
        selection = self.logs_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a log to download")
            return

        log_index = selection[0]
        log = self.current_logs[log_index]

        self.download_progress_label.config(
            text=f"⬇️ Downloading log {log.id}...")

        def progress_cb(done, total):
            pct = (done / total) * 100
            self.download_progress_label.config(
                text=f"⬇️ Downloading: {pct:.1f}% ({done}/{total} bytes)")
            self.root.update()

        try:
            result = self.downloader.download_log(log.id, progress_callback=progress_cb)

            if result:
                self.download_progress_label.config(
                    text=f"✅ Downloaded: {result.name}")

                # Register log for analysis
                self.agent.add_downloaded_log(result)

                # Show success with analysis prompt
                msg = f"✅ Лог скачан: {result.name}\n\n"
                msg += "🔍 Лог зарегистрирован для анализа!\n\n"
                msg += "Перейдите на вкладку '💬 AI Assistant' и напишите:\n"
                msg += "'проанализируй скачанный лог'\n\n"
                msg += "или перейдите на '🔧 Auto-Fix' и нажмите 'Refresh'"

                messagebox.showinfo("Лог скачан!", msg)

                # Auto-refresh fixes tab
                self.root.after(500, self.refresh_fixes)
            else:
                self.download_progress_label.config(text="✗ Download failed")

        except Exception as e:
            self.download_progress_label.config(text=f"✗ Error: {e}")

    def run(self):
        """Run application"""
        self.root.mainloop()


# Main entry point
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="MPDiagnostic Unified Agent - AI-powered ArduPilot diagnostics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent_ran                 Launch GUI interface
  agent_ran --cli           Launch CLI mode
  agent_ran --version       Show version info

For more information, visit: https://github.com/AlexandrTerentev/Claude/tree/main/MPDiagnosticAgent
        """
    )

    parser.add_argument('--version', action='version', version='MPDiagnosticAgent v6.0')
    parser.add_argument('--cli', action='store_true', help='Use CLI interface instead of GUI')

    args = parser.parse_args()

    if args.cli:
        # Launch CLI instead
        print("🚀 Launching CLI interface...")
        from interfaces.cli import main as cli_main
        cli_main()
    else:
        # Launch GUI (default)
        print("🚀 Starting MPDiagnostic Unified Agent v6.0...")
        app = MPDiagnosticApp()
        app.run()
