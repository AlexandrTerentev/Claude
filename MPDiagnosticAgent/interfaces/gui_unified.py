#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Intelligent Agent GUI
Natural language chat interface with auto-fix capabilities
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unified_agent import UnifiedAgent, FixAction
from core.config import Config
from core.mavlink_interface import MAVLinkInterface


class UnifiedAgentGUI:
    """
    Unified Intelligent Agent GUI

    Features:
    - Natural language chat interface
    - Real-time log analysis
    - One-click fix buttons
    - Auto-connect to drone
    - Parameter management
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ArduPilot Unified Diagnostic Agent v6.0")
        self.root.geometry("1200x800")

        # Colors (dark theme)
        self.bg_color = '#1e1e1e'
        self.fg_color = '#d4d4d4'
        self.accent_color = '#007acc'
        self.success_color = '#4ec9b0'
        self.warning_color = '#dcdcaa'
        self.error_color = '#f48771'
        self.input_bg = '#252526'
        self.button_bg = '#0e639c'

        self.root.configure(bg=self.bg_color)

        # Initialize agent
        try:
            self.config = Config()
            self.agent = UnifiedAgent(config=self.config)
            self.connected = False
            self.pending_fixes = []
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize agent: {e}")
            sys.exit(1)

        # Create UI
        self.create_ui()

        # Auto-analyze on start
        self.root.after(500, self.auto_analyze)

    def create_ui(self):
        """Create main UI"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top panel - Status
        self.create_status_panel(main_container)

        # Middle panel - Chat + Fixes
        middle_frame = tk.Frame(main_container, bg=self.bg_color)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left: Chat area
        self.create_chat_area(middle_frame)

        # Right: Fixes panel
        self.create_fixes_panel(middle_frame)

        # Bottom panel - Input
        self.create_input_panel(main_container)

    def create_status_panel(self, parent):
        """Create status panel"""
        status_frame = tk.LabelFrame(parent, text="Drone Status",
                                     bg=self.bg_color, fg=self.fg_color,
                                     font=('Liberation Mono', 10, 'bold'))
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # Connection status
        conn_row = tk.Frame(status_frame, bg=self.bg_color)
        conn_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(conn_row, text="Connection:", bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 9)).pack(side=tk.LEFT)

        self.conn_status_label = tk.Label(conn_row, text="⚪ Not Connected",
                                          bg=self.bg_color, fg=self.warning_color,
                                          font=('Liberation Mono', 9, 'bold'))
        self.conn_status_label.pack(side=tk.LEFT, padx=10)

        # Auto-detect ports
        ports = MAVLinkInterface.find_available_ports()

        if ports:
            self.port_var = tk.StringVar(value=ports[0])
            port_combo = ttk.Combobox(conn_row, textvariable=self.port_var,
                                     values=ports, width=15,
                                     font=('Liberation Mono', 9))
            port_combo.pack(side=tk.LEFT, padx=10)
        else:
            self.port_var = tk.StringVar(value="/dev/ttyACM0")
            port_entry = tk.Entry(conn_row, textvariable=self.port_var,
                                 bg=self.input_bg, fg=self.fg_color,
                                 font=('Liberation Mono', 9), width=15)
            port_entry.pack(side=tk.LEFT, padx=10)

        # Connect button
        self.connect_btn = tk.Button(conn_row, text="Connect",
                                     command=self.toggle_connection,
                                     bg=self.button_bg, fg='white',
                                     font=('Liberation Mono', 9, 'bold'),
                                     relief=tk.FLAT, padx=15, pady=3)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # Issues summary
        summary_row = tk.Frame(status_frame, bg=self.bg_color)
        summary_row.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(summary_row, text="Issues:", bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 9)).pack(side=tk.LEFT)

        self.issues_label = tk.Label(summary_row, text="Analyzing...",
                                     bg=self.bg_color, fg=self.warning_color,
                                     font=('Liberation Mono', 9))
        self.issues_label.pack(side=tk.LEFT, padx=10)

    def create_chat_area(self, parent):
        """Create chat area"""
        chat_frame = tk.Frame(parent, bg=self.bg_color)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        tk.Label(chat_frame, text="💬 Ask Me Anything",
                bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 11, 'bold')).pack(anchor='w', pady=(0, 5))

        # Chat display
        self.chat = scrolledtext.ScrolledText(chat_frame,
                                              bg=self.input_bg,
                                              fg=self.fg_color,
                                              font=('Liberation Mono', 10),
                                              wrap=tk.WORD,
                                              state=tk.DISABLED,
                                              relief=tk.FLAT)
        self.chat.pack(fill=tk.BOTH, expand=True)

        # Configure tags
        self.chat.tag_config('user', foreground=self.accent_color, font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('agent', foreground=self.success_color, font=('Liberation Mono', 10, 'bold'))
        self.chat.tag_config('timestamp', foreground='#858585', font=('Liberation Mono', 8))
        self.chat.tag_config('error', foreground=self.error_color)
        self.chat.tag_config('success', foreground=self.success_color)
        self.chat.tag_config('warning', foreground=self.warning_color)

        # Welcome message
        self.add_agent_message(
            "👋 Привет! Я - Интеллектуальный Агент Диагностики ArduPilot.\n\n"
            "Задайте любой вопрос о вашем дроне:\n"
            "• 'Почему дрон не взлетает?'\n"
            "• 'Что означает RC not found?'\n"
            "• 'Как исправить проблемы с батареей?'\n\n"
            "Я проанализирую логи и предложу решения!"
        )

    def create_fixes_panel(self, parent):
        """Create fixes panel"""
        fixes_frame = tk.Frame(parent, bg=self.bg_color, width=400)
        fixes_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        fixes_frame.pack_propagate(False)

        tk.Label(fixes_frame, text="🔧 Available Fixes",
                bg=self.bg_color, fg=self.fg_color,
                font=('Liberation Mono', 11, 'bold')).pack(anchor='w', pady=(0, 5))

        # Scrollable fixes container
        fixes_canvas = tk.Canvas(fixes_frame, bg=self.input_bg,
                                highlightthickness=0)
        scrollbar = ttk.Scrollbar(fixes_frame, orient="vertical",
                                 command=fixes_canvas.yview)
        self.fixes_container = tk.Frame(fixes_canvas, bg=self.input_bg)

        self.fixes_container.bind(
            "<Configure>",
            lambda e: fixes_canvas.configure(scrollregion=fixes_canvas.bbox("all"))
        )

        fixes_canvas.create_window((0, 0), window=self.fixes_container, anchor="nw")
        fixes_canvas.configure(yscrollcommand=scrollbar.set)

        fixes_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.fixes_canvas = fixes_canvas

    def create_input_panel(self, parent):
        """Create input panel"""
        input_frame = tk.Frame(parent, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=(10, 0))

        # Input field
        self.input_var = tk.StringVar()
        input_entry = tk.Entry(input_frame, textvariable=self.input_var,
                              bg=self.input_bg, fg=self.fg_color,
                              font=('Liberation Mono', 11),
                              relief=tk.FLAT, insertbackground=self.fg_color)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        input_entry.bind('<Return>', lambda e: self.send_message())
        input_entry.focus()

        # Send button
        send_btn = tk.Button(input_frame, text="Send ➤",
                            command=self.send_message,
                            bg=self.accent_color, fg='white',
                            font=('Liberation Mono', 10, 'bold'),
                            relief=tk.FLAT, padx=20, pady=8,
                            cursor='hand2')
        send_btn.pack(side=tk.RIGHT)

    def add_user_message(self, text):
        """Add user message to chat"""
        self.chat.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat.insert(tk.END, f'\n[{timestamp}] ', 'timestamp')
        self.chat.insert(tk.END, 'You: ', 'user')
        self.chat.insert(tk.END, f'{text}\n')
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def add_agent_message(self, text):
        """Add agent message to chat"""
        self.chat.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat.insert(tk.END, f'\n[{timestamp}] ', 'timestamp')
        self.chat.insert(tk.END, 'Agent: ', 'agent')

        # Format message with colors
        lines = text.split('\n')
        for line in lines:
            if line.startswith('✓') or line.startswith('✅'):
                self.chat.insert(tk.END, line + '\n', 'success')
            elif line.startswith('⚠') or line.startswith('❌') or line.startswith('✗'):
                self.chat.insert(tk.END, line + '\n', 'error')
            elif line.startswith('🔴') or line.startswith('🟡'):
                self.chat.insert(tk.END, line + '\n', 'warning')
            else:
                self.chat.insert(tk.END, line + '\n')

        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def send_message(self):
        """Send message to agent"""
        message = self.input_var.get().strip()
        if not message:
            return

        self.input_var.set('')
        self.add_user_message(message)

        # Get answer from agent
        try:
            answer = self.agent.answer_question(message)
            self.add_agent_message(answer)

            # Update fixes if needed
            if 'исправлен' in message.lower() or 'fix' in message.lower():
                self.update_fixes()

        except Exception as e:
            self.add_agent_message(f"❌ Error: {e}")

    def auto_analyze(self):
        """Auto-analyze on startup"""
        try:
            report = self.agent.analyze_current_state()

            # Update issues label
            error_count = len(report['prearm_errors'])
            fix_count = len(report['fixable_issues'])

            if error_count == 0:
                self.issues_label.config(text="✅ No issues found",
                                        fg=self.success_color)
            else:
                self.issues_label.config(
                    text=f"🔴 {error_count} errors, {fix_count} fixes available",
                    fg=self.error_color
                )

            # Update fixes panel
            self.pending_fixes = report['fixable_issues']
            self.update_fixes()

            # Show summary in chat
            if error_count > 0:
                self.add_agent_message(
                    f"🔍 Auto-analysis complete:\n"
                    f"• Found {error_count} issues\n"
                    f"• {fix_count} automatic fixes available\n\n"
                    f"Ask me about specific issues or click 'Apply Fix' buttons →"
                )

        except Exception as e:
            self.add_agent_message(f"⚠ Auto-analysis failed: {e}")

    def update_fixes(self):
        """Update fixes panel"""
        # Clear existing fixes
        for widget in self.fixes_container.winfo_children():
            widget.destroy()

        if not self.pending_fixes:
            tk.Label(self.fixes_container, text="✅ No fixes needed!",
                    bg=self.input_bg, fg=self.success_color,
                    font=('Liberation Mono', 10)).pack(pady=20)
            return

        # Add fix cards
        for i, fix in enumerate(self.pending_fixes):
            self.create_fix_card(fix, i)

    def create_fix_card(self, fix: FixAction, index: int):
        """Create a fix card widget"""
        # Severity colors
        severity_colors = {
            'low': '#4ec9b0',
            'medium': '#dcdcaa',
            'high': '#ce9178',
            'critical': '#f48771'
        }
        sev_color = severity_colors.get(fix.severity, self.warning_color)

        # Card frame
        card = tk.Frame(self.fixes_container, bg='#2d2d30',
                       relief=tk.RAISED, borderwidth=1)
        card.pack(fill=tk.X, padx=5, pady=5)

        # Header
        header = tk.Frame(card, bg='#2d2d30')
        header.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(header, text=f"#{index+1}",
                bg='#2d2d30', fg='#858585',
                font=('Liberation Mono', 8)).pack(side=tk.LEFT)

        tk.Label(header, text=fix.severity.upper(),
                bg=sev_color, fg='#1e1e1e',
                font=('Liberation Mono', 7, 'bold'),
                padx=5, pady=1).pack(side=tk.RIGHT)

        # Title
        tk.Label(card, text=fix.title,
                bg='#2d2d30', fg=self.fg_color,
                font=('Liberation Mono', 10, 'bold'),
                wraplength=350, justify=tk.LEFT).pack(anchor='w', padx=10, pady=(0, 5))

        # Description
        tk.Label(card, text=fix.description,
                bg='#2d2d30', fg='#a8a8a8',
                font=('Liberation Mono', 8),
                wraplength=350, justify=tk.LEFT).pack(anchor='w', padx=10, pady=(0, 5))

        # Parameters info
        tk.Label(card, text=f"Will change {len(fix.params)} parameters",
                bg='#2d2d30', fg='#6a9955',
                font=('Liberation Mono', 8, 'italic')).pack(anchor='w', padx=10, pady=(0, 10))

        # Apply button
        if fix.applied:
            btn_text = "✓ Applied"
            btn_bg = self.success_color
            btn_state = tk.DISABLED
        else:
            btn_text = "Apply Fix"
            btn_bg = self.accent_color
            btn_state = tk.NORMAL

        apply_btn = tk.Button(card, text=btn_text,
                             command=lambda f=fix: self.apply_fix_action(f),
                             bg=btn_bg, fg='white',
                             font=('Liberation Mono', 9, 'bold'),
                             relief=tk.FLAT, padx=15, pady=5,
                             state=btn_state, cursor='hand2' if not fix.applied else 'arrow')
        apply_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

    def toggle_connection(self):
        """Toggle drone connection"""
        if self.connected:
            # Disconnect
            if self.agent.mav:
                self.agent.mav.disconnect()
            self.connected = False
            self.conn_status_label.config(text="⚪ Not Connected", fg=self.warning_color)
            self.connect_btn.config(text="Connect")
            self.add_agent_message("🔌 Disconnected from drone")
        else:
            # Connect
            port = self.port_var.get()
            self.add_agent_message(f"🔌 Connecting to {port}...")

            if self.agent.connect_to_drone(port):
                self.connected = True
                self.conn_status_label.config(text="🟢 Connected", fg=self.success_color)
                self.connect_btn.config(text="Disconnect")
                self.add_agent_message("✅ Connected to drone! Auto-fix is now available.")
            else:
                self.add_agent_message("❌ Failed to connect to drone. Check port and permissions.")

    def apply_fix_action(self, fix: FixAction):
        """Apply a fix action"""
        if not self.connected:
            messagebox.showwarning("Not Connected",
                                  "Please connect to drone first!\n\n"
                                  "Click 'Connect' button in status panel.")
            return

        # Confirmation dialog
        params_list = "\n".join([f"• {k} = {v}" for k, v in fix.params.items()])
        confirm = messagebox.askyesno(
            "Confirm Parameter Changes",
            f"{fix.title}\n\n"
            f"{fix.description}\n\n"
            f"Will change these parameters:\n{params_list}\n\n"
            f"Severity: {fix.severity.upper()}\n\n"
            f"Continue?"
        )

        if not confirm:
            return

        self.add_agent_message(f"🔧 Applying: {fix.title}...")

        # Apply fix
        if self.agent.apply_fix(fix):
            self.add_agent_message(f"✅ Fix applied successfully! {len(fix.params)} parameters updated.")
            self.update_fixes()  # Refresh UI
        else:
            self.add_agent_message(f"❌ Fix failed. Check connection and try again.")

    def run(self):
        """Run the GUI"""
        self.root.mainloop()


# Main
if __name__ == '__main__':
    print("🚀 Starting Unified Agent GUI...")
    app = UnifiedAgentGUI()
    app.run()
