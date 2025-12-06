#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Агент Диагностики Mission Planner - Независимое окно
Diagnostic Agent for Mission Planner - Independent Window
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import os
from datetime import datetime
from pathlib import Path

class DiagnosticAgent:
    def __init__(self):
        self.log_path = "/home/user_1/missionplanner/Mission Planner/MissionPlanner.log"

        # Create window
        self.root = tk.Tk()
        self.root.title("🚁 Агент Диагностики / Diagnostic Agent")
        self.root.geometry("600x700")
        self.root.configure(bg='#2d2d30')

        # Always on top
        self.root.attributes('-topmost', True)

        # Chat display
        self.chat = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='white',
            insertbackground='white'
        )
        self.chat.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat.config(state=tk.DISABLED)

        # Input frame
        input_frame = tk.Frame(self.root, bg='#2d2d30')
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Input box
        self.input_box = tk.Text(
            input_frame,
            height=3,
            font=('Segoe UI', 11),
            bg='#3c3c3c',
            fg='white',
            insertbackground='white'
        )
        self.input_box.pack(fill=tk.X, pady=(0, 5))
        self.input_box.bind('<Control-Return>', lambda e: self.send_message())

        # Send button
        self.send_btn = tk.Button(
            input_frame,
            text="📤 ОТПРАВИТЬ / SEND",
            font=('Segoe UI', 10, 'bold'),
            bg='#007acc',
            fg='white',
            activebackground='#005a9e',
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.send_message
        )
        self.send_btn.pack(fill=tk.X)

        # Welcome message
        self.add_message("🤖 Агент",
            "Привет! Я готов помогать.\n"
            "Hello! I'm ready to help.\n\n"
            "✅ МОЖНО ПИСАТЬ НА РУССКОМ!\n"
            "✅ RUSSIAN INPUT WORKS!\n\n"
            "Команды / Commands:\n"
            "  помощь / help\n"
            "  тест / test\n"
            "  статус / status\n"
            "  моторы / motors\n"
            "  ошибки / errors\n\n"
            "Ctrl+Enter или кнопка для отправки",
            'lime green')

        self.input_box.focus_set()

    def add_message(self, sender, text, color='white'):
        self.chat.config(state=tk.NORMAL)

        # Timestamp
        timestamp = f"\n[{datetime.now().strftime('%H:%M:%S')}] "
        self.chat.insert(tk.END, timestamp, 'timestamp')

        # Sender
        self.chat.insert(tk.END, f"{sender}:\n", sender)

        # Message
        self.chat.insert(tk.END, f"{text}\n", 'message')

        # Configure colors
        self.chat.tag_config('timestamp', foreground='gray')
        self.chat.tag_config(sender, foreground=color, font=('Consolas', 10, 'bold'))
        self.chat.tag_config('message', foreground='white')

        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def send_message(self):
        msg = self.input_box.get('1.0', tk.END).strip()
        if not msg:
            return

        self.add_message("👤 Вы", msg, 'cyan')
        self.input_box.delete('1.0', tk.END)
        self.input_box.focus_set()

        response = self.process_query(msg)
        self.add_message("🤖 Агент", response, 'lime green')

    def process_query(self, query):
        q = query.lower().strip()

        if 'помощь' in q or 'help' in q:
            return self.get_help()

        if 'тест' in q or 'test' in q:
            return (
                "✅ РАБОТАЕТ! / WORKING!\n\n"
                "Русский: ДА ✓\n"
                "Russian: YES ✓\n\n"
                f"Время: {datetime.now().strftime('%H:%M:%S')}"
            )

        if 'статус' in q or 'status' in q:
            return self.get_status()

        if 'мотор' in q or 'motor' in q:
            return self.diagnose_motors()

        if 'ошибк' in q or 'error' in q:
            return self.find_errors()

        if 'лог' in q or 'log' in q:
            return self.show_logs()

        if 'prearm' in q:
            return self.check_prearm()

        return (
            f"Получено: \"{query}\"\n\n"
            "Напишите 'помощь' для списка команд.\n"
            "Type 'help' for command list."
        )

    def get_help(self):
        return (
            "📋 КОМАНДЫ / COMMANDS:\n\n"
            "помощь / help       - эта справка / this help\n"
            "тест / test         - проверка / test\n"
            "статус / status     - статус дрона / drone status\n"
            "моторы / motors     - диагностика / diagnosis\n"
            "ошибки / errors     - найти ошибки / find errors\n"
            "логи / logs         - показать логи / show logs\n"
            "prearm              - проверка PreArm / check PreArm\n\n"
            "Пишите по-русски или по-английски!\n"
            "Write in Russian or English!"
        )

    def get_status(self):
        return (
            "❌ Дрон не подключен / Drone not connected\n\n"
            "Эта версия не имеет прямого доступа к Mission Planner.\n"
            "This version doesn't have direct access to Mission Planner.\n\n"
            "Используйте команды для анализа логов:\n"
            "Use commands to analyze logs:\n"
            "  логи / logs\n"
            "  ошибки / errors\n"
            "  prearm"
        )

    def read_log_lines(self, n=100):
        try:
            if not os.path.exists(self.log_path):
                return []

            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-n:]]
        except:
            return []

    def diagnose_motors(self):
        errors = self.find_prearm_errors()

        if not errors:
            return (
                "✅ PreArm ошибок нет\n"
                "✅ No PreArm errors\n\n"
                "Возможные причины:\n"
                "1. Дрон не подключен\n"
                "2. Нет попыток армирования\n"
                "3. Все системы готовы"
            )

        result = ["⚠️  ОШИБКИ PreArm / PreArm ERRORS:\n"]
        for err in errors[:5]:
            result.append(f"❌ {err}")

        all_errors = ' '.join(errors).lower()
        result.append("\n" + "="*40)
        result.append("РЕКОМЕНДАЦИИ / RECOMMENDATIONS:")
        result.append("="*40 + "\n")

        if 'rc not calibrated' in all_errors or 'rc3_min' in all_errors:
            result.append(
                "🎮 RC НЕ ОТКАЛИБРОВАН\n\n"
                "РЕШЕНИЕ:\n"
                "1. Initial Setup > Mandatory Hardware > Radio Calibration\n"
                "2. Включить передатчик / Turn on transmitter\n"
                "3. Двигать стики / Move sticks\n"
            )

        if 'compass' in all_errors:
            result.append(
                "🧭 КОМПАС НЕ ОТКАЛИБРОВАН\n\n"
                "РЕШЕНИЕ:\n"
                "1. Initial Setup > Mandatory Hardware > Compass\n"
                "2. Onboard Mag Calibration\n"
                "3. Вращать на улице / Rotate outside\n"
            )

        return '\n'.join(result)

    def find_prearm_errors(self):
        lines = self.read_log_lines(300)
        errors = []
        pattern = re.compile(r'PreArm:\s*(.+)$', re.IGNORECASE)

        for line in lines:
            match = pattern.search(line)
            if match:
                errors.append(match.group(1).strip())

        return list(set(errors))  # unique

    def find_errors(self):
        lines = self.read_log_lines(300)
        errors = [line for line in lines if 'ERROR' in line or 'CRITICAL' in line]

        if not errors:
            return "✅ Ошибок нет / No errors"

        result = [f"⚠️  Найдено ошибок: {len(errors)}\n"]
        for err in errors[:10]:
            result.append(f"❌ {err}")

        return '\n'.join(result)

    def show_logs(self):
        lines = self.read_log_lines(15)

        if not lines:
            return f"❌ Файл лога не найден / Log file not found\n\nПуть: {self.log_path}"

        result = ["📋 ПОСЛЕДНИЕ ЛОГИ / RECENT LOGS:\n"]
        result.extend(lines)

        return '\n'.join(result)

    def check_prearm(self):
        errors = self.find_prearm_errors()

        if not errors:
            return "✅ PreArm: OK\n\nНет ошибок / No errors"

        result = [f"⚠️  PreArm ошибки: {len(errors)}\n"]
        for err in errors[:10]:
            result.append(f"❌ {err}")

        return '\n'.join(result)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = DiagnosticAgent()
        app.run()
    except Exception as e:
        print(f"Ошибка: {e}")
        messagebox.showerror("Ошибка", str(e))
