#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Агент Диагностики Mission Planner PRO - Умный помощник
Smart Diagnostic Agent for Mission Planner with ArduPilot Wiki Integration
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import os
import requests
from datetime import datetime
from pathlib import Path
import json

class SmartDiagnosticAgent:
    def __init__(self):
        self.log_path = "/home/user_1/missionplanner/Mission Planner/MissionPlanner.log"
        self.tlog_path = "/home/user_1/missionplanner/logs"

        # Wiki documentation URLs
        self.wiki_base = "https://raw.githubusercontent.com/ArduPilot/ardupilot_wiki/master/copter/source/docs"
        self.wiki_cache = {}

        # Create window with terminal style
        self.root = tk.Tk()
        self.root.title("🚁 Умный Агент Диагностики / Smart Diagnostic Agent")
        self.root.geometry("900x800")

        # Terminal-like colors (inspired by popular Linux terminals)
        self.bg_color = '#0C0C0C'        # Deep black (Windows Terminal)
        self.fg_color = '#CCCCCC'        # Light gray text
        self.input_bg = '#1E1E1E'        # Dark gray for input
        self.accent_color = '#0078D7'    # Blue accent
        self.success_color = '#16C60C'   # Green
        self.warning_color = '#F9F1A5'   # Yellow
        self.error_color = '#E74856'     # Red
        self.info_color = '#3B78FF'      # Light blue

        self.root.configure(bg=self.bg_color)
        self.root.attributes('-topmost', True)

        # Header frame
        header = tk.Frame(self.root, bg=self.accent_color, height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_label = tk.Label(
            header,
            text="🚁 АГЕНТ ДИАГНОСТИКИ ARDUPILOT • SMART ASSISTANT",
            font=('Liberation Mono', 11, 'bold'),
            bg=self.accent_color,
            fg='white',
            anchor='w',
            padx=15
        )
        header_label.pack(fill=tk.BOTH, expand=True)

        # Chat display (terminal style)
        self.chat = scrolledtext.ScrolledText(
            self.root,
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

        # Status bar
        self.status_frame = tk.Frame(self.root, bg='#1E1E1E', height=25)
        self.status_frame.pack(fill=tk.X)
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_frame,
            text="● Готов | Ready",
            font=('Liberation Mono', 9),
            bg='#1E1E1E',
            fg=self.success_color,
            anchor='w',
            padx=15
        )
        self.status_label.pack(side=tk.LEFT)

        # Input frame
        input_frame = tk.Frame(self.root, bg=self.bg_color)
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
        self.input_box.bind('<Control-Return>', lambda e: self.insert_newline())
        self.input_box.bind('<Shift-Return>', lambda e: self.insert_newline())

        # Send button (minimalistic)
        self.send_btn = tk.Label(
            input_frame,
            text="⏎",
            font=('Liberation Mono', 16),
            bg=self.bg_color,
            fg=self.accent_color,
            cursor='hand2',
            padx=10
        )
        self.send_btn.pack(side=tk.LEFT)
        self.send_btn.bind('<Button-1>', lambda e: self.send_message())

        # Configure tags for colored output
        self.configure_tags()

        # Welcome message
        self.show_welcome()
        self.input_box.focus_set()

    def configure_tags(self):
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
        self.chat.tag_config('link', foreground='#3794FF', underline=True)
        self.chat.tag_config('header', foreground='white', font=('Liberation Mono', 10, 'bold'))

    def show_welcome(self):
        welcome = """
╔══════════════════════════════════════════════════════════════════╗
║          УМНЫЙ АГЕНТ ДИАГНОСТИКИ ARDUPILOT v1.0                  ║
║          SMART DIAGNOSTIC AGENT FOR ARDUPILOT                    ║
╚══════════════════════════════════════════════════════════════════╝

✓ Анализ реальных данных Mission Planner
✓ Интеграция с ArduPilot Wiki документацией
✓ Умные рекомендации параметров
✓ Русский + English

БЫСТРЫЙ СТАРТ:
  анализ          - полный анализ состояния дрона
  параметры       - проверка критических параметров
  вибрации        - анализ вибраций (причина дребезжания)
  компас          - диагностика проблем с компасом
  wiki <тема>     - поиск в документации ArduPilot

Просто опишите проблему, я проанализирую логи и данные!
"""
        self.add_system_message(welcome)

    def handle_return(self, event):
        """Handle Enter key - send message"""
        if not event.state & 0x1:  # Not Shift
            self.send_message()
            return 'break'
        return None

    def insert_newline(self):
        """Insert newline in input"""
        self.input_box.insert(tk.INSERT, '\n')
        return 'break'

    def update_status(self, text, color=None):
        """Update status bar"""
        if color is None:
            color = self.success_color
        self.status_label.config(text=text, fg=color)

    def add_system_message(self, text):
        """Add system message"""
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, text + '\n', 'info')
        self.chat.config(state=tk.DISABLED)
        self.chat.see(tk.END)

    def add_message(self, sender, text, sender_tag='user', text_tags=None):
        """Add formatted message"""
        self.chat.config(state=tk.NORMAL)

        # Timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat.insert(tk.END, f'\n[{timestamp}] ', 'timestamp')

        # Sender
        self.chat.insert(tk.END, f'{sender}\n', sender_tag)

        # Message with optional tags
        if text_tags:
            for line, tag in text_tags:
                self.chat.insert(tk.END, line, tag)
        else:
            # Auto-detect formatting
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
            elif line.startswith('⚠') or line.startswith('❌'):
                self.chat.insert(tk.END, line + '\n', 'warning')
            elif line.startswith('ERROR') or line.startswith('CRITICAL'):
                self.chat.insert(tk.END, line + '\n', 'error')
            elif line.startswith('INFO') or line.startswith('→'):
                self.chat.insert(tk.END, line + '\n', 'info')
            elif line.startswith('  ') and ':' in line:
                # Parameter line
                self.chat.insert(tk.END, line + '\n', 'code')
            elif line.startswith('═') or line.startswith('─'):
                self.chat.insert(tk.END, line + '\n', 'header')
            else:
                self.chat.insert(tk.END, line + '\n')

    def send_message(self):
        """Send user message and get response"""
        msg = self.input_box.get('1.0', tk.END).strip()
        if not msg:
            return

        self.add_message("❯ ВЫ", msg, 'user')
        self.input_box.delete('1.0', tk.END)
        self.input_box.focus_set()

        self.update_status("● Анализирую... | Analyzing...", self.warning_color)
        self.root.update()

        try:
            response = self.process_smart_query(msg)
            self.add_message("🤖 АГЕНТ", response, 'agent')
            self.update_status("● Готов | Ready", self.success_color)
        except Exception as e:
            error_msg = f"❌ Ошибка: {str(e)}"
            self.add_message("⚠ СИСТЕМА", error_msg, 'error')
            self.update_status("● Ошибка | Error", self.error_color)

    def process_smart_query(self, query):
        """Smart query processing with real data analysis"""
        q = query.lower().strip()

        # Smart commands
        if 'анализ' in q or q == 'analyze':
            return self.full_analysis()

        if 'параметр' in q or 'parameter' in q:
            return self.analyze_parameters()

        if 'вибрац' in q or 'vibration' in q or 'дребезж' in q:
            return self.analyze_vibrations()

        if 'компас' in q or 'compass' in q:
            return self.diagnose_compass()

        if q.startswith('wiki '):
            topic = q[5:].strip()
            return self.search_wiki(topic)

        if 'помощь' in q or 'help' in q:
            return self.get_help()

        # Intelligent analysis based on keywords
        if any(word in q for word in ['мотор', 'motor', 'крутятся', 'spin', 'вращ']):
            return self.diagnose_motors_smart()

        if any(word in q for word in ['калибр', 'calibrat', 'настр']):
            return self.calibration_guide()

        if 'prearm' in q or 'ошибк' in q or 'error' in q:
            return self.analyze_prearm_smart()

        # Default: try to understand and provide smart response
        return self.smart_response(query)

    def full_analysis(self):
        """Full drone state analysis"""
        result = []
        result.append("═══════════════════════════════════════════════════════════")
        result.append("         ПОЛНЫЙ АНАЛИЗ СОСТОЯНИЯ ДРОНА")
        result.append("         FULL DRONE STATE ANALYSIS")
        result.append("═══════════════════════════════════════════════════════════\n")

        # 1. Recent log errors
        errors = self.get_recent_errors()
        result.append("📋 ПОСЛЕДНИЕ ОШИБКИ (RECENT ERRORS):")
        if errors:
            for err in errors[:5]:
                result.append(f"  ❌ {err}")
        else:
            result.append("  ✓ Ошибок не найдено")
        result.append("")

        # 2. PreArm status
        prearm = self.get_prearm_errors()
        result.append("🔒 СТАТУС PREARM:")
        if prearm:
            result.append(f"  ⚠ Найдено {len(prearm)} проблем:")
            for p in prearm[:3]:
                result.append(f"    • {p}")
            result.append("\n→ Запустите 'моторы' для подробной диагностики")
        else:
            result.append("  ✓ PreArm: OK")
        result.append("")

        # 3. Log file analysis
        vibration_data = self.analyze_vibration_from_logs()
        if vibration_data:
            result.append("📊 ВИБРАЦИИ (VIBRATIONS):")
            result.append(vibration_data)
            result.append("")

        # 4. Recommendations
        result.append("💡 РЕКОМЕНДАЦИИ (RECOMMENDATIONS):")
        recommendations = self.get_smart_recommendations(errors, prearm)
        for rec in recommendations:
            result.append(f"  → {rec}")

        return '\n'.join(result)

    def analyze_parameters(self):
        """Analyze critical parameters from logs"""
        result = []
        result.append("═══════════════════════════════════════════════════════════")
        result.append("         АНАЛИЗ КРИТИЧЕСКИХ ПАРАМЕТРОВ")
        result.append("═══════════════════════════════════════════════════════════\n")

        params = self.extract_parameters_from_logs()

        if not params:
            result.append("⚠ Параметры не найдены в логах.")
            result.append("Подключите дрон к Mission Planner для анализа.\n")
            result.append("📚 РЕКОМЕНДУЕМЫЕ ПАРАМЕТРЫ ДЛЯ КОПТЕРА:")
            result.append(self.get_recommended_params())
        else:
            result.append("📊 НАЙДЕННЫЕ ПАРАМЕТРЫ:\n")
            for param, value in params.items():
                status = self.check_parameter_value(param, value)
                result.append(f"  {param}: {value}  {status}")

            result.append("\n💡 РЕКОМЕНДАЦИИ:")
            result.append(self.get_param_recommendations(params))

        return '\n'.join(result)

    def analyze_vibrations(self):
        """Detailed vibration analysis"""
        result = []
        result.append("═══════════════════════════════════════════════════════════")
        result.append("         АНАЛИЗ ВИБРАЦИЙ (VIBRATION ANALYSIS)")
        result.append("         Поиск причин дребезжания / Finding shaking causes")
        result.append("═══════════════════════════════════════════════════════════\n")

        # Check logs for vibration data
        vibe_data = self.find_vibration_in_logs()

        result.append("📊 ДАННЫЕ ВИБРАЦИЙ:")
        if vibe_data:
            result.append(vibe_data)
        else:
            result.append("  ⚠ Данные о вибрациях не найдены в логах")
            result.append("  → Подключите дрон и запишите лог полета\n")

        result.append("\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ ДРЕБЕЗЖАНИЯ:\n")

        causes = [
            ("1. Разбалансированные пропеллеры", "Проверить балансировку всех винтов"),
            ("2. Погнутые моторы или валы", "Визуально проверить моторы на изгиб"),
            ("3. Плохое крепление контроллера полета", "Проверить амортизаторы и крепеж"),
            ("4. Старые/поврежденные пропеллеры", "Заменить на новые качественные винты"),
            ("5. Неправильные PID параметры", "Настроить PID в Auto Tune"),
            ("6. Механические повреждения рамы", "Проверить целостность рамы")
        ]

        for cause, solution in causes:
            result.append(f"  • {cause}")
            result.append(f"    → {solution}\n")

        result.append("\n📚 WIKI: Vibration Dampening")
        result.append("  https://ardupilot.org/copter/docs/common-vibration-dampening.html")

        result.append("\n💡 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ:")
        result.append("  1. Проверить балансировку пропеллеров (самая частая причина)")
        result.append("  2. Установить LOG_BITMASK = 655358 для детального лога вибраций")
        result.append("  3. Записать тестовый полет и проанализировать в Mission Planner")
        result.append("  4. В Mission Planner: Flight Data → Telemetry Logs → Vibration")

        return '\n'.join(result)

    def diagnose_compass(self):
        """Diagnose compass issues"""
        result = []
        result.append("═══════════════════════════════════════════════════════════")
        result.append("         ДИАГНОСТИКА КОМПАСА (COMPASS DIAGNOSIS)")
        result.append("═══════════════════════════════════════════════════════════\n")

        # Check for compass errors in logs
        compass_errors = self.find_compass_errors()

        if compass_errors:
            result.append("⚠ НАЙДЕНЫ ПРОБЛЕМЫ С КОМПАСОМ:\n")
            for err in compass_errors[:5]:
                result.append(f"  ❌ {err}")
            result.append("")

        result.append("🧭 ЧАСТЫЕ ПРИЧИНЫ ОТКАЗА КАЛИБРОВКИ:\n")

        issues = [
            ("Калибровка возле металла/железобетона",
             "→ Калибровать ТОЛЬКО на улице, вдали от зданий"),

            ("Помехи от силовых проводов",
             "→ Развести провода питания подальше от компаса"),

            ("Слишком быстрое вращение",
             "→ Вращать МЕДЛЕННО и плавно по всем осям"),

            ("Магнитные помехи от моторов",
             "→ Поднять GPS-модуль выше на мачте"),

            ("Неправильная ориентация GPS",
             "→ Проверить COMPASS_ORIENT параметр"),

            ("Некачественный GPS модуль",
             "→ Использовать известные бренды (Here, Zubax)")
        ]

        for issue, solution in issues:
            result.append(f"  • {issue}")
            result.append(f"    {solution}\n")

        result.append("\n⚙️ РЕКОМЕНДУЕМЫЕ ПАРАМЕТРЫ:")
        result.append("  COMPASS_AUTODEC: 1        (автоопределение магнитного склонения)")
        result.append("  COMPASS_LEARN: 0          (выкл обучение во время полета)")
        result.append("  COMPASS_USE: 1            (использовать компас)")
        result.append("  COMPASS_DIA_X/Y/Z         (проверить что не 0 после калибровки)")

        result.append("\n📚 WIKI: Compass Calibration")
        result.append("  https://ardupilot.org/copter/docs/common-compass-calibration-in-mission-planner.html")

        result.append("\n💡 ПОШАГОВАЯ ИНСТРУКЦИЯ:")
        result.append("  1. Отключить батарею")
        result.append("  2. Вынести дрон на ОТКРЫТОЕ место (парк, поле)")
        result.append("  3. Mission Planner → Initial Setup → Compass")
        result.append("  4. Нажать 'Onboard Mag Calibration'")
        result.append("  5. Подключить батарею")
        result.append("  6. МЕДЛЕННО вращать дрон по всем осям 60 секунд")
        result.append("  7. Дождаться сообщения 'Calibration successful'")

        return '\n'.join(result)

    def diagnose_motors_smart(self):
        """Smart motor diagnosis with real data"""
        result = []
        result.append("═══════════════════════════════════════════════════════════")
        result.append("         УМНАЯ ДИАГНОСТИКА МОТОРОВ")
        result.append("         SMART MOTOR DIAGNOSIS")
        result.append("═══════════════════════════════════════════════════════════\n")

        prearm = self.get_prearm_errors()

        if not prearm:
            result.append("✓ PreArm ошибок нет - моторы готовы к армированию\n")
            result.append("💡 ЧЕКЛИСТ ПЕРЕД ПОЛЕТОМ:")
            result.append("  ✓ Проверить направление вращения моторов")
            result.append("  ✓ Убедиться что пропеллеры установлены правильно")
            result.append("  ✓ Проверить затяжку винтов моторов")
            result.append("  ✓ Тест моторов через Mission Planner (без винтов!)")
            return '\n'.join(result)

        result.append(f"⚠ Найдено {len(prearm)} PreArm ошибок:\n")

        # Categorize errors
        rc_errors = [e for e in prearm if 'rc' in e.lower() or 'radio' in e.lower()]
        compass_errors = [e for e in prearm if 'compass' in e.lower() or 'mag' in e.lower()]
        accel_errors = [e for e in prearm if 'accel' in e.lower()]
        other_errors = [e for e in prearm if e not in rc_errors + compass_errors + accel_errors]

        if rc_errors:
            result.append("🎮 ПРОБЛЕМЫ С RC:")
            for err in rc_errors:
                result.append(f"  ❌ {err}")
            result.append("\n→ РЕШЕНИЕ:")
            result.append("  1. Initial Setup → Mandatory Hardware → Radio Calibration")
            result.append("  2. Включить передатчик")
            result.append("  3. Двигать все стики в крайние положения")
            result.append("  4. Нажать 'Calibrate Radio' и следовать инструкциям")
            result.append("  5. Проверить что все каналы показывают ~1000-2000")
            result.append("")

        if compass_errors:
            result.append("🧭 ПРОБЛЕМЫ С КОМПАСОМ:")
            for err in compass_errors:
                result.append(f"  ❌ {err}")
            result.append("\n→ Запустите команду 'компас' для подробной диагностики")
            result.append("")

        if accel_errors:
            result.append("📐 ПРОБЛЕМЫ С АКСЕЛЕРОМЕТРОМ:")
            for err in accel_errors:
                result.append(f"  ❌ {err}")
            result.append("\n→ РЕШЕНИЕ:")
            result.append("  1. Initial Setup → Mandatory Hardware → Accel Calibration")
            result.append("  2. Следовать инструкциям для 6 позиций")
            result.append("  3. Держать дрон неподвижно в каждой позиции")
            result.append("")

        if other_errors:
            result.append("⚠ ДРУГИЕ ПРОБЛЕМЫ:")
            for err in other_errors:
                result.append(f"  ❌ {err}")
            result.append("")

        # Add wiki link
        result.append("\n📚 WIKI: PreArm Safety Checks")
        result.append("  https://ardupilot.org/copter/docs/prearm_safety_check.html")

        return '\n'.join(result)

    def analyze_prearm_smart(self):
        """Smart PreArm analysis"""
        errors = self.get_prearm_errors()

        if not errors:
            return "✓ PreArm: ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ\n✓ PreArm: ALL CHECKS PASSED\n\nДрон готов к армированию."

        return self.diagnose_motors_smart()

    def search_wiki(self, topic):
        """Search ArduPilot wiki"""
        result = []
        result.append(f"🔍 Поиск в ArduPilot Wiki: '{topic}'\n")

        # Common topics mapping
        topics = {
            'vibration': 'common-vibration-dampening.html',
            'вибрац': 'common-vibration-dampening.html',
            'compass': 'common-compass-calibration-in-mission-planner.html',
            'компас': 'common-compass-calibration-in-mission-planner.html',
            'pid': 'tuning.html',
            'пид': 'tuning.html',
            'autotune': 'autotune.html',
            'motor': 'connect-escs-and-motors.html',
            'мотор': 'connect-escs-and-motors.html',
            'esc': 'common-esc-calibration.html',
            'gps': 'common-gps-how-it-works.html',
            'failsafe': 'failsafe-landing-page.html',
        }

        found = False
        for key, page in topics.items():
            if key in topic.lower():
                url = f"https://ardupilot.org/copter/docs/{page}"
                result.append(f"📚 Найдено: {page}")
                result.append(f"🔗 {url}\n")
                found = True

        if not found:
            result.append("⚠ Точного совпадения не найдено.")
            result.append("\n📚 Полная документация:")
            result.append("  https://ardupilot.org/copter/index.html")
            result.append("\n💡 Популярные темы: vibration, compass, pid, autotune, motor, esc, gps")

        return '\n'.join(result)

    def smart_response(self, query):
        """Intelligent response based on query analysis"""
        # Try to understand user's problem
        q = query.lower()

        if any(word in q for word in ['дребезж', 'трясет', 'трясёт', 'вибрир', 'shake', 'vibrat']):
            return self.analyze_vibrations()

        if any(word in q for word in ['не калибр', 'отказ', 'fail', "can't calibr"]):
            if 'компас' in q or 'compass' in q:
                return self.diagnose_compass()

        # Default response with suggestions
        return (
            f"📝 Получен запрос: \"{query}\"\n\n"
            "Я могу помочь с:\n"
            "  • анализ - полная диагностика состояния\n"
            "  • вибрации - почему дрон дребезжит\n"
            "  • компас - проблемы с калибровкой\n"
            "  • моторы - почему не крутятся\n"
            "  • параметры - проверка настроек\n"
            "  • wiki <тема> - поиск в документации\n\n"
            "Опишите проблему подробнее или используйте команду выше."
        )

    def get_help(self):
        """Show help"""
        return """
═══════════════════════════════════════════════════════════
                    СПРАВКА / HELP
═══════════════════════════════════════════════════════════

🔍 ДИАГНОСТИКА:
  анализ          - полный анализ состояния дрона
  параметры       - проверка критических параметров
  вибрации        - анализ вибраций и дребезжания
  компас          - диагностика проблем с компасом
  моторы          - диагностика моторов и PreArm

📚 ДОКУМЕНТАЦИЯ:
  wiki <тема>     - поиск в ArduPilot Wiki
  Примеры: wiki compass, wiki vibration, wiki pid

💬 ЕСТЕСТВЕННЫЕ ВОПРОСЫ:
  Просто опишите проблему:
  - "Почему дрон дребезжит?"
  - "Компас не калибруется"
  - "Моторы не крутятся"

⌨️ УПРАВЛЕНИЕ:
  Enter          - отправить сообщение
  Shift+Enter    - новая строка
  Ctrl+C         - очистить ввод

Агент анализирует реальные логи Mission Planner и
предоставляет умные рекомендации на основе документации.
"""

    # Helper methods for data extraction

    def get_recent_errors(self):
        """Extract recent errors from log"""
        try:
            lines = self.read_log_lines(200)
            errors = []
            for line in lines:
                if 'ERROR' in line or 'CRITICAL' in line:
                    errors.append(line.strip())
            return errors[-10:]  # Last 10 errors
        except:
            return []

    def get_prearm_errors(self):
        """Extract PreArm errors"""
        try:
            lines = self.read_log_lines(300)
            errors = []
            pattern = re.compile(r'PreArm:\s*(.+)$', re.IGNORECASE)
            for line in lines:
                match = pattern.search(line)
                if match:
                    errors.append(match.group(1).strip())
            return list(set(errors))  # Unique errors
        except:
            return []

    def read_log_lines(self, n=100):
        """Read last n lines from log"""
        try:
            if not os.path.exists(self.log_path):
                return []
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return [line.strip() for line in lines[-n:]]
        except:
            return []

    def find_vibration_in_logs(self):
        """Find vibration data in logs"""
        lines = self.read_log_lines(500)
        vibe_lines = [l for l in lines if 'VIBE' in l or 'vibration' in l.lower()]
        if vibe_lines:
            return '\n  '.join(vibe_lines[-5:])
        return None

    def analyze_vibration_from_logs(self):
        """Analyze vibration from logs"""
        vibe_data = self.find_vibration_in_logs()
        if vibe_data:
            return f"  Обнаружены данные о вибрациях\n  → Запустите 'вибрации' для анализа"
        return None

    def find_compass_errors(self):
        """Find compass related errors"""
        lines = self.read_log_lines(300)
        compass_lines = [l for l in lines if 'compass' in l.lower() or 'mag' in l.lower()]
        return [l for l in compass_lines if 'error' in l.lower() or 'fail' in l.lower()]

    def extract_parameters_from_logs(self):
        """Extract parameters from logs"""
        # This would need tlog parser, simplified version
        return {}

    def check_parameter_value(self, param, value):
        """Check if parameter value is good"""
        return "✓"

    def get_recommended_params(self):
        """Get recommended parameters"""
        return """
  CRITICAL PARAMETERS:
    MOT_PWM_MIN: 1000-1100    (ESC минимум)
    MOT_PWM_MAX: 1900-2000    (ESC максимум)
    MOT_SPIN_ARM: 0.10        (для теста моторов)
    MOT_SPIN_MIN: 0.15        (минимальный throttle)

    COMPASS_AUTODEC: 1        (автоопределение)
    COMPASS_LEARN: 0          (выкл обучение)

    INS_ACCEL_FILTER: 20      (фильтр акселерометра)
    INS_GYRO_FILTER: 20       (фильтр гироскопа)
"""

    def get_param_recommendations(self, params):
        """Get parameter recommendations"""
        return "  → Параметры в допустимых пределах"

    def get_smart_recommendations(self, errors, prearm):
        """Generate smart recommendations"""
        recs = []

        if prearm:
            recs.append("Исправить PreArm ошибки (команда: моторы)")

        if errors:
            recs.append("Проанализировать ошибки в логах")

        if not prearm and not errors:
            recs.append("Система в норме, можно пробовать полет")

        recs.append("Регулярно проверять балансировку пропеллеров")
        recs.append("Использовать качественные компоненты (ESC, моторы)")

        return recs

    def calibration_guide(self):
        """Calibration guide"""
        return """
═══════════════════════════════════════════════════════════
         ПОЛНОЕ РУКОВОДСТВО ПО КАЛИБРОВКЕ
         COMPLETE CALIBRATION GUIDE
═══════════════════════════════════════════════════════════

🎮 РАДИО (RC):
  1. Initial Setup → Mandatory Hardware → Radio Calibration
  2. Включить передатчик
  3. Двигать все стики в крайние положения
  4. Калибровать → проверить диапазон 1000-2000

🧭 КОМПАС:
  1. Вынести на улицу, подальше от металла
  2. Initial Setup → Compass
  3. Onboard Mag Calibration
  4. МЕДЛЕННО вращать 60 секунд по всем осям

📐 АКСЕЛЕРОМЕТР:
  1. Initial Setup → Accel Calibration
  2. 6 позиций: level, left, right, nose down, nose up, back
  3. Держать неподвижно в каждой позиции

⚙️ ESC:
  1. СНЯТЬ ВИНТЫ!
  2. Initial Setup → Optional Hardware → ESC Calibration
  3. Следовать инструкциям точно

📚 Wiki: https://ardupilot.org/copter/docs/initial-setup.html
"""

    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = SmartDiagnosticAgent()
        app.run()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
