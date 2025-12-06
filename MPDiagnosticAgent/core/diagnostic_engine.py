# -*- coding: utf-8 -*-
"""
Unified Diagnostic Engine for MPDiagnosticAgent
Combines all diagnostic logic from previous versions with enhanced Wiki integration
"""

import re
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Handle imports for both module and standalone usage
try:
    from .config import Config
    from .knowledge_base import KnowledgeBase
    from .log_analyzer import LogAnalyzer
    from .mavlink_interface import MAVLinkInterface
    from .log_downloader import LogDownloader
except ImportError:
    from config import Config
    from knowledge_base import KnowledgeBase
    from log_analyzer import LogAnalyzer
    from mavlink_interface import MAVLinkInterface
    from log_downloader import LogDownloader


class DiagnosticEngine:
    """
    Unified diagnostic engine

    Combines functionality from:
    - engine/agent_core.py - Basic query processing
    - diagnostic_agent_pro.py - Wiki integration, smart analysis
    - DiagnosticAgent_MultiTab.cs - PreArm categorization, localization
    """

    # ArduPilot Wiki URLs
    WIKI_BASE = "https://raw.githubusercontent.com/ArduPilot/ardupilot_wiki/master/copter/source/docs"

    def __init__(self, config: Optional[Config] = None, language: str = 'auto'):
        """
        Initialize diagnostic engine

        Args:
            config: Configuration object (or None to create new)
            language: Preferred language ('ru', 'en', or 'auto')
        """
        self.config = config if config else Config()

        # Detect language
        if language == 'auto':
            self.language = self.config.config.get('diagnostics', {}).get('language', 'en')
            if self.language == 'auto':
                self.language = 'en'  # Default to English
        else:
            self.language = language

        # Initialize components
        self.kb = KnowledgeBase()
        self.log_analyzer = LogAnalyzer(config=self.config)

        # Wiki cache
        self.wiki_cache = {}

    def process_query(self, user_input: str) -> str:
        """
        Process user query and return diagnostic response

        Args:
            user_input: User's question or command

        Returns:
            Diagnostic response string
        """
        query = user_input.lower().strip()

        # Command detection (multi-language)
        if query in ['help', '?', 'помощь', 'справка']:
            return self.show_help()

        elif query in ['status', 'summary', 'статус', 'сводка', 'анализ']:
            return self.get_full_status()

        elif 'motor' in query or 'spin' in query or 'arm' in query or 'propeller' in query or \
             'мотор' in query or 'крут' in query or 'винт' in query or 'пропеллер' in query:
            return self.diagnose_motors()

        elif 'vibrat' in query or 'vibr' in query or 'вибра' in query or 'дребезж' in query:
            return self.analyze_vibrations()

        elif 'compass' in query or 'компас' in query or 'магнит' in query:
            return self.diagnose_compass()

        elif 'calibrat' in query or 'калибр' in query:
            return self.show_calibration_info()

        elif query.startswith('wiki ') or query.startswith('вики '):
            topic = query.split(' ', 1)[1] if ' ' in query else ''
            return self.search_wiki(topic)

        elif 'param' in query or 'параметр' in query:
            return self.check_critical_parameters()

        elif 'log' in query and ('show' in query or 'recent' in query or 'check' in query or \
                                  'покаж' in query or 'последн' in query):
            return self.show_recent_logs()

        elif 'error' in query or 'problem' in query or 'issue' in query or \
             'ошибк' in query or 'проблем' in query:
            return self.check_errors()

        elif 'prearm' in query or 'преарм' in query:
            return self.check_prearm()

        else:
            return self.smart_response(query)

    def show_help(self) -> str:
        """Show help message in appropriate language"""
        if self.language == 'ru':
            return """ДОСТУПНЫЕ КОМАНДЫ:

ДИАГНОСТИКА:
  анализ / статус     - Полный анализ состояния дрона
  моторы              - Диагностика моторов и арминга
  вибрации            - Анализ вибраций
  компас              - Диагностика компаса
  параметры           - Проверка критических параметров
  prearm              - Проверка PreArm ошибок

ЛОГИ:
  показать логи       - Последние записи в логах
  проверить ошибки    - Найти ошибки в логах

СПРАВКА:
  калибровка          - Инструкции по калибровке
  wiki <тема>         - Поиск в ArduPilot Wiki
  помощь              - Эта справка

Просто опишите проблему естественным языком!"""
        else:
            return """AVAILABLE COMMANDS:

DIAGNOSTICS:
  status / summary    - Full drone health check
  motors              - Diagnose motor/arming issues
  vibrations          - Analyze vibrations
  compass             - Diagnose compass problems
  parameters          - Check critical parameters
  prearm              - Check PreArm errors

LOGS:
  show logs           - Recent log entries
  check errors        - Find errors in logs

HELP:
  calibration         - Calibration instructions
  wiki <topic>        - Search ArduPilot Wiki
  help                - This help message

Just describe your problem in natural language!"""

    def get_full_status(self) -> str:
        """Get comprehensive system status"""
        sections = []

        # Header
        header = "═" * 60
        if self.language == 'ru':
            sections.append(f"{header}\nПОЛНЫЙ АНАЛИЗ СОСТОЯНИЯ ДРОНА\n{header}\n")
        else:
            sections.append(f"{header}\nFULL DRONE STATUS ANALYSIS\n{header}\n")

        # 1. PreArm status
        prearm_result = self.check_prearm(brief=True)
        sections.append(prearm_result)

        # 2. Recent errors
        errors_result = self.check_errors(brief=True)
        sections.append(errors_result)

        # 3. Log summary
        summary = self.log_analyzer.summarize_issues()
        sections.append(summary)

        # 4. Recommendations
        if self.language == 'ru':
            sections.append("\n" + "─" * 60)
            sections.append("РЕКОМЕНДАЦИИ:")
            sections.append("─" * 60)
        else:
            sections.append("\n" + "─" * 60)
            sections.append("RECOMMENDATIONS:")
            sections.append("─" * 60)

        recommendations = self._generate_recommendations()
        sections.append(recommendations)

        return '\n'.join(sections)

    def diagnose_motors(self) -> str:
        """
        Diagnose motor/arming issues with knowledge base integration
        Enhanced version combining agent_core.py logic + KB recommendations
        """
        # Check for PreArm errors
        prearm_errors = self.log_analyzer.find_prearm_errors(num_lines=300)

        if not prearm_errors:
            if self.language == 'ru':
                return """✓ PreArm ошибки не найдены в последних логах.

ВОЗМОЖНЫЕ ПРИЧИНЫ:
1. Дрон не подключён к Mission Planner
2. Попытки армирования не зафиксированы
3. Все системы готовы (попробуйте заармить)

Попробуйте: 'показать логи' для просмотра активности"""
            else:
                return """✓ No PreArm errors found in recent logs.

POSSIBLE CAUSES:
1. Drone not connected to Mission Planner
2. No arming attempts logged recently
3. All systems ready (try arming)

Try: 'show logs' to see recent activity"""

        # Build response
        response = []
        sep = "═" * 60

        if self.language == 'ru':
            response.append(f"{sep}\nДИАГНОСТИКА МОТОРОВ И АРМИНГА\n{sep}\n")
            response.append(f"Найдено {len(prearm_errors)} PreArm ошибок:\n")
        else:
            response.append(f"{sep}\nMOTOR/ARMING DIAGNOSIS\n{sep}\n")
            response.append(f"Found {len(prearm_errors)} PreArm error(s):\n")

        # Show unique errors with timestamps
        unique_errors = {}
        for err in prearm_errors:
            msg = err['message']
            if msg not in unique_errors:
                unique_errors[msg] = err

        for msg, err in list(unique_errors.items())[-5:]:  # Last 5 unique errors
            time_only = err['timestamp'].split()[1] if ' ' in err['timestamp'] else err['timestamp']
            response.append(f"  [{time_only}] ✗ {msg}")

        response.append("\n" + "─" * 60)
        if self.language == 'ru':
            response.append("РЕКОМЕНДАЦИИ:")
        else:
            response.append("RECOMMENDATIONS:")
        response.append("─" * 60 + "\n")

        # Search knowledge base for solutions
        all_errors_text = ' '.join([e['message'] for e in prearm_errors]).lower()

        # Extract keywords
        keywords = re.findall(r'\b\w{4,}\b', all_errors_text)

        # Get recommendations from KB
        kb_results = self.kb.search_motor_issues(keywords)

        if kb_results:
            for issue in kb_results[:3]:  # Top 3 matches
                solution = self.kb.format_solution(issue, language=self.language)
                response.append(solution)
                response.append("")
        else:
            # Fallback to pattern matching (from agent_core.py)
            if 'rc not calibrated' in all_errors_text or 'rc3_min' in all_errors_text:
                if self.language == 'ru':
                    response.append("""! ПУЛЬТ НЕ ОТКАЛИБРОВАН

РЕШЕНИЕ:
1. Перейдите: Initial Setup > Mandatory Hardware > Radio Calibration
2. Включите RC передатчик
3. Подвигайте все стики в крайние положения
4. Нажмите 'Calibrate Radio'
5. Убедитесь что все каналы показывают ЗЕЛЁНЫЕ полосы
6. Нажмите 'Click when Done'
""")
                else:
                    response.append("""! RC CONTROLLER NOT CALIBRATED

SOLUTION:
1. Go to: Initial Setup > Mandatory Hardware > Radio Calibration
2. Turn on your RC transmitter
3. Move all sticks to their extreme positions
4. Click 'Calibrate Radio' button
5. Verify all channels show GREEN bars
6. Click 'Click when Done'
""")

            if 'compass' in all_errors_text and ('calibrat' in all_errors_text or 'inconsistent' in all_errors_text):
                if self.language == 'ru':
                    response.append("""! ТРЕБУЕТСЯ КАЛИБРОВКА КОМПАСА

РЕШЕНИЕ:
1. Перейдите: Initial Setup > Mandatory Hardware > Compass
2. Нажмите 'Onboard Mag Calibration'
3. Вынесите дрон на улицу (подальше от металла/магнитов)
4. Медленно вращайте по всем осям
5. Дождитесь сообщения 'Calibration successful'
""")
                else:
                    response.append("""! COMPASS CALIBRATION NEEDED

SOLUTION:
1. Go to: Initial Setup > Mandatory Hardware > Compass
2. Click 'Onboard Mag Calibration'
3. Take drone outside (away from metal/magnets)
4. Slowly rotate on all axes
5. Wait for 'Calibration successful' message
""")

        # Add Wiki link
        if self.language == 'ru':
            response.append("\n💡 Для дополнительной информации используйте: 'wiki prearm'")
        else:
            response.append("\n💡 For more information use: 'wiki prearm'")

        return '\n'.join(response)

    def analyze_vibrations(self) -> str:
        """
        Analyze vibrations (placeholder - needs .bin log parsing)
        """
        if self.language == 'ru':
            return """АНАЛИЗ ВИБРАЦИЙ

⚠ Для полного анализа вибраций нужны .bin логи с дрона

БЫСТРАЯ ДИАГНОСТИКА:
• Дребезжание при наборе высоты → несбалансированные винты
• Колебания при зависании → плохое крепление моторов
• Вибрация на высоких оборотах → погнутые валы моторов

РЕШЕНИЯ:
1. Проверьте балансировку пропеллеров
2. Затяните все крепления моторов
3. Убедитесь что винты целые (без трещин)
4. Проверьте мягкость антивибрационных амортизаторов

ПАРАМЕТРЫ ДЛЯ ПРОВЕРКИ:
  INS_ACCEL_FILTER  - должен быть 10-20 Hz
  INS_GYRO_FILTER   - должен быть 20-40 Hz

Используйте: 'wiki vibration' для подробной информации"""
        else:
            return """VIBRATION ANALYSIS

⚠ Full vibration analysis requires .bin logs from drone

QUICK DIAGNOSTICS:
• Jittering during climb → unbalanced propellers
• Oscillations in hover → loose motor mounts
• High RPM vibration → bent motor shafts

SOLUTIONS:
1. Check propeller balance
2. Tighten all motor mounts
3. Ensure props are intact (no cracks)
4. Check anti-vibration dampeners

PARAMETERS TO CHECK:
  INS_ACCEL_FILTER  - should be 10-20 Hz
  INS_GYRO_FILTER   - should be 20-40 Hz

Use: 'wiki vibration' for detailed information"""

    def diagnose_compass(self) -> str:
        """Diagnose compass issues"""
        # Check logs for compass errors
        prearm_errors = self.log_analyzer.find_prearm_errors(num_lines=200)
        compass_errors = [e for e in prearm_errors if 'compass' in e['message'].lower()]

        response = []
        sep = "═" * 60

        if self.language == 'ru':
            response.append(f"{sep}\nДИАГНОСТИКА КОМПАСА\n{sep}\n")
        else:
            response.append(f"{sep}\nCOMPASS DIAGNOSTICS\n{sep}\n")

        if compass_errors:
            if self.language == 'ru':
                response.append(f"Найдено {len(compass_errors)} ошибок компаса:\n")
            else:
                response.append(f"Found {len(compass_errors)} compass error(s):\n")

            for err in compass_errors[-3:]:  # Last 3
                response.append(f"  ✗ {err['message']}")
            response.append("")

        # Search KB for compass solutions
        compass_solutions = self.kb.search_motor_issues(['compass', 'магнит', 'calibration'])

        if compass_solutions:
            for solution in compass_solutions[:2]:
                formatted = self.kb.format_solution(solution, language=self.language)
                response.append(formatted)
        else:
            # Generic compass guidance
            if self.language == 'ru':
                response.append("""ОБЩИЕ РЕКОМЕНДАЦИИ:

1. КАЛИБРОВКА:
   - Выполните калибровку на открытом воздухе
   - Держитесь подальше от металла, проводов, магнитов
   - Медленно вращайте дрон по всем осям

2. ПРОВЕРЬТЕ ИНТЕРФЕРЕНЦИЮ:
   - Удалите дрон от источников помех
   - Проверьте расположение GPS/компаса
   - Убедитесь в отсутствии магнитов рядом

3. ПАРАМЕТРЫ:
   COMPASS_LEARN = 3 (включить обучение)
   COMPASS_USE = 1 (основной компас)

Используйте: 'wiki compass' для деталей""")
            else:
                response.append("""GENERAL RECOMMENDATIONS:

1. CALIBRATION:
   - Perform calibration outdoors
   - Stay away from metal, wires, magnets
   - Slowly rotate drone on all axes

2. CHECK INTERFERENCE:
   - Move drone away from interference sources
   - Check GPS/compass placement
   - Ensure no magnets nearby

3. PARAMETERS:
   COMPASS_LEARN = 3 (enable learning)
   COMPASS_USE = 1 (primary compass)

Use: 'wiki compass' for details""")

        return '\n'.join(response)

    def check_critical_parameters(self) -> str:
        """Check critical parameters (requires MAVLink connection)"""
        if self.language == 'ru':
            return """ПРОВЕРКА КРИТИЧЕСКИХ ПАРАМЕТРОВ

⚠ Требуется подключение к дрону через MAVLink

Для проверки параметров:
1. Подключите дрон через USB
2. Используйте функцию скачивания логов
3. Параметры будут получены автоматически

КРИТИЧЕСКИЕ ПАРАМЕТРЫ ДЛЯ COPTER:
  FRAME_CLASS       - Тип рамы (2 = Quad)
  FRAME_TYPE        - Конфигурация (1 = X)
  ARMING_CHECK      - Проверки арминга (1 = включено)
  BATT_CAPACITY     - Ёмкость батареи (mAh)
  RC3_MIN/MAX       - Диапазон газа

Используйте: 'wiki parameters' для полного списка"""
        else:
            return """CRITICAL PARAMETERS CHECK

⚠ Requires MAVLink connection to drone

To check parameters:
1. Connect drone via USB
2. Use log download function
3. Parameters will be fetched automatically

CRITICAL PARAMETERS FOR COPTER:
  FRAME_CLASS       - Frame type (2 = Quad)
  FRAME_TYPE        - Configuration (1 = X)
  ARMING_CHECK      - Arming checks (1 = enabled)
  BATT_CAPACITY     - Battery capacity (mAh)
  RC3_MIN/MAX       - Throttle range

Use: 'wiki parameters' for complete list"""

    def check_prearm(self, brief: bool = False) -> str:
        """Check for PreArm errors"""
        prearm_errors = self.log_analyzer.find_prearm_errors()

        if not prearm_errors:
            if self.language == 'ru':
                return "✓ PreArm ошибки не найдены в последних логах"
            else:
                return "✓ No PreArm errors found in recent logs"

        if brief:
            # Brief version for status summary
            unique_count = len(set(e['message'] for e in prearm_errors))
            if self.language == 'ru':
                return f"⚠ PreArm: {unique_count} уникальных ошибок ({len(prearm_errors)} всего)"
            else:
                return f"⚠ PreArm: {unique_count} unique error(s) ({len(prearm_errors)} total)"

        # Full version
        response = []
        if self.language == 'ru':
            response.append(f"Найдено {len(prearm_errors)} PreArm ошибок:\n")
        else:
            response.append(f"Found {len(prearm_errors)} PreArm error(s):\n")

        # Show last 5 unique errors with timestamps
        unique_errors = {}
        for err in prearm_errors:
            msg = err['message']
            unique_errors[msg] = err

        for msg, err in list(unique_errors.items())[-5:]:
            time_only = err['timestamp'].split()[1] if ' ' in err['timestamp'] else err['timestamp']
            response.append(f"  [{time_only}] {msg}")

        if self.language == 'ru':
            response.append("\n💡 Используйте 'моторы' для детальной диагностики")
        else:
            response.append("\n💡 Use 'motors' for detailed diagnostics")

        return '\n'.join(response)

    def check_errors(self, brief: bool = False) -> str:
        """Check for ERROR and CRITICAL messages"""
        errors = self.log_analyzer.find_errors(num_lines=300)

        if not errors:
            if self.language == 'ru':
                return "✓ Критические ошибки не найдены в последних логах"
            else:
                return "✓ No critical errors found in recent logs"

        if brief:
            # Brief version
            if self.language == 'ru':
                return f"⚠ Ошибки: {len(errors)} в последних логах"
            else:
                return f"⚠ Errors: {len(errors)} in recent logs"

        # Full version
        response = []
        if self.language == 'ru':
            response.append(f"Найдено {len(errors)} ошибок:\n")
        else:
            response.append(f"Found {len(errors)} error(s):\n")

        for err in errors[-5:]:  # Last 5 errors
            time_only = err['timestamp'].split()[1] if ' ' in err['timestamp'] else err['timestamp']
            response.append(f"  [{time_only}] {err['level']}: {err['message']}")

        return '\n'.join(response)

    def show_recent_logs(self) -> str:
        """Show recent log entries"""
        logs = self.log_analyzer.get_recent_logs(num_lines=15)

        if self.language == 'ru':
            return f"ПОСЛЕДНИЕ ЗАПИСИ В ЛОГАХ:\n\n{logs}"
        else:
            return f"RECENT LOG ENTRIES:\n\n{logs}"

    def show_calibration_info(self) -> str:
        """Show calibration guidance"""
        if self.language == 'ru':
            return """РУКОВОДСТВО ПО КАЛИБРОВКЕ:

КОМПАС:
  Initial Setup > Mandatory Hardware > Compass
  - Нажмите 'Onboard Mag Calibration'
  - Вынесите дрон на улицу, медленно вращайте по всем осям

ПУЛЬТ (RC):
  Initial Setup > Mandatory Hardware > Radio Calibration
  - Подвигайте все стики в крайние положения
  - Убедитесь в ЗЕЛЁНЫХ полосах на всех каналах

АКСЕЛЕРОМЕТР:
  Initial Setup > Mandatory Hardware > Accel Calibration
  - Следуйте инструкциям на экране
  - Размещайте дрон в каждой ориентации

ESC:
  Initial Setup > Optional Hardware > ESC Calibration
  - ОСТОРОЖНО: Моторы будут вращаться!
  - Точно следуйте инструкциям

Спросите: "wiki калибровка" для подробностей"""
        else:
            return """CALIBRATION GUIDE:

COMPASS:
  Initial Setup > Mandatory Hardware > Compass
  - Click 'Onboard Mag Calibration'
  - Take drone outside, rotate slowly on all axes

RADIO (RC):
  Initial Setup > Mandatory Hardware > Radio Calibration
  - Move all sticks to extremes
  - Verify GREEN bars on all channels

ACCELEROMETER:
  Initial Setup > Mandatory Hardware > Accel Calibration
  - Follow on-screen instructions
  - Place drone in each orientation

ESC:
  Initial Setup > Optional Hardware > ESC Calibration
  - CAREFUL: Motors will spin!
  - Follow instructions exactly

Ask: "wiki calibration" for details"""

    def search_wiki(self, topic: str) -> str:
        """
        Search ArduPilot Wiki (from diagnostic_agent_pro.py)

        Args:
            topic: Topic to search

        Returns:
            Wiki information or error message
        """
        if not topic:
            if self.language == 'ru':
                return "Укажите тему для поиска. Пример: 'wiki prearm'"
            else:
                return "Specify a topic to search. Example: 'wiki prearm'"

        # Check cache
        if topic in self.wiki_cache:
            return self.wiki_cache[topic]

        # Try to fetch from Wiki
        wiki_topics = {
            'prearm': 'prearm-safety-check.rst',
            'calibration': 'common-compass-calibration-in-mission-planner.rst',
            'compass': 'common-compass-setup-advanced.rst',
            'vibration': 'common-vibration-damping.rst',
            'parameters': 'parameters.rst',
            'motors': 'connect-escs-and-motors.rst',
        }

        wiki_file = wiki_topics.get(topic.lower())

        if not wiki_file:
            if self.language == 'ru':
                return f"Тема '{topic}' не найдена. Доступные темы: {', '.join(wiki_topics.keys())}"
            else:
                return f"Topic '{topic}' not found. Available topics: {', '.join(wiki_topics.keys())}"

        try:
            url = f"{self.WIKI_BASE}/{wiki_file}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # Extract first few paragraphs
                content = response.text
                lines = content.split('\n')

                # Find meaningful content (skip RST headers)
                meaningful_lines = []
                for line in lines[10:50]:  # Skip header, take middle content
                    if line.strip() and not line.startswith('..') and not line.startswith('==='):
                        meaningful_lines.append(line.strip())

                result = '\n'.join(meaningful_lines[:15])  # First 15 lines

                if self.language == 'ru':
                    result = f"📖 ИНФОРМАЦИЯ ИЗ ARDUPILOT WIKI:\n\n{result}\n\n🔗 Полная версия: https://ardupilot.org/copter/docs/{wiki_file.replace('.rst', '.html')}"
                else:
                    result = f"📖 ARDUPILOT WIKI INFORMATION:\n\n{result}\n\n🔗 Full version: https://ardupilot.org/copter/docs/{wiki_file.replace('.rst', '.html')}"

                # Cache result
                self.wiki_cache[topic] = result
                return result
            else:
                if self.language == 'ru':
                    return f"⚠ Не удалось загрузить Wiki страницу (код {response.status_code})"
                else:
                    return f"⚠ Failed to load Wiki page (code {response.status_code})"

        except Exception as e:
            if self.language == 'ru':
                return f"⚠ Ошибка при загрузке Wiki: {e}"
            else:
                return f"⚠ Error loading Wiki: {e}"

    def smart_response(self, query: str) -> str:
        """
        Smart response using knowledge base and pattern matching

        Args:
            query: User's query

        Returns:
            Intelligent response
        """
        # Extract keywords
        keywords = re.findall(r'\b\w{4,}\b', query.lower())

        # Search knowledge base
        kb_results = self.kb.search_motor_issues(keywords)

        if kb_results:
            # Found relevant KB articles
            response = []
            if self.language == 'ru':
                response.append(f"Нашёл {len(kb_results)} релевантных решений:\n")
            else:
                response.append(f"Found {len(kb_results)} relevant solution(s):\n")

            for issue in kb_results[:2]:  # Top 2
                formatted = self.kb.format_solution(issue, language=self.language)
                response.append(formatted)

            return '\n'.join(response)
        else:
            # Generic response with help
            if self.language == 'ru':
                return f"""Понял ваш запрос: "{query}"

Пока я учусь! Я могу помочь с:
• Проблемами моторов (спросите: "почему не крутятся моторы?")
• Калибровкой
• Анализом логов
• Проверкой ошибок

Попробуйте: 'помощь' для списка команд"""
            else:
                return f"""I understand your query: "{query}"

I'm still learning! I can help with:
• Motor issues (ask: "why won't motors spin?")
• Calibration guidance
• Log analysis
• Error checking

Try: 'help' to see all commands"""

    def _generate_recommendations(self) -> str:
        """Generate recommendations based on log analysis"""
        recommendations = []

        # Check for recent PreArm errors
        prearm_errors = self.log_analyzer.find_prearm_errors(num_lines=100)

        if prearm_errors:
            if self.language == 'ru':
                recommendations.append("• Устраните PreArm ошибки перед полётом")
            else:
                recommendations.append("• Fix PreArm errors before flight")

        # Check for general errors
        errors = self.log_analyzer.find_errors(num_lines=100)

        if errors:
            if self.language == 'ru':
                recommendations.append("• Проверьте и устраните недавние ошибки")
            else:
                recommendations.append("• Review and fix recent errors")

        if not recommendations:
            if self.language == 'ru':
                recommendations.append("• Всё выглядит хорошо! Проверьте настройки перед полётом")
            else:
                recommendations.append("• Everything looks good! Review settings before flight")

        return '\n'.join(recommendations)


# Global function for C# plugin and standalone usage
def process_query(user_input: str, language: str = 'auto') -> str:
    """
    Main entry point for query processing

    Args:
        user_input: User's question or command
        language: Preferred language ('ru', 'en', or 'auto')

    Returns:
        Response string
    """
    try:
        engine = DiagnosticEngine(language=language)
        return engine.process_query(user_input)
    except Exception as e:
        if language == 'ru':
            return f"⚠ Ошибка при обработке запроса: {str(e)}\n\nПроверьте доступность файлов логов."
        else:
            return f"⚠ Error processing query: {str(e)}\n\nPlease check that log files are accessible."


# Testing
if __name__ == '__main__':
    print("Testing DiagnosticEngine...\n")
    print("=" * 60)

    # Create engine
    engine = DiagnosticEngine(language='ru')

    # Test queries
    test_queries = [
        "помощь",
        "почему не крутятся моторы?",
        "статус",
        "prearm",
    ]

    for query in test_queries:
        print(f"\n📝 Запрос: {query}")
        print("─" * 60)
        response = engine.process_query(query)
        print(response)
        print()
