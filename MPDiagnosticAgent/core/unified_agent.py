#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Intelligent Diagnostic Agent
Combines log analysis, natural language Q&A, and auto-fix capabilities
"""

import re
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime

# Handle imports
try:
    from .config import Config
    from .log_analyzer import LogAnalyzer
    from .knowledge_base import KnowledgeBase
    from .mavlink_interface import MAVLinkInterface
    from .github_dataset import GitHubDataset
except ImportError:
    from config import Config
    from log_analyzer import LogAnalyzer
    from knowledge_base import KnowledgeBase
    from mavlink_interface import MAVLinkInterface
    from github_dataset import GitHubDataset


class FixAction:
    """Represents a fixable action"""
    def __init__(self, title: str, description: str, params: Dict[str, Any],
                 severity: str = "medium"):
        self.title = title
        self.description = description
        self.params = params  # {param_name: value}
        self.severity = severity  # low, medium, high, critical
        self.applied = False

    def __repr__(self):
        return f"<FixAction: {self.title} ({len(self.params)} params)>"


class UnifiedAgent:
    """
    Unified Intelligent Diagnostic Agent

    Features:
    - Natural language understanding of log issues
    - Contextual Q&A about drone problems
    - Automatic fix suggestions with one-click apply
    - Full diagnostic reports
    - Parameter management via MAVLink
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the unified agent"""
        self.config = config if config else Config()

        # Core components
        self.log_analyzer = LogAnalyzer(config=self.config)
        self.knowledge_base = KnowledgeBase()
        self.github_dataset = GitHubDataset()

        # MAVLink interface (for auto-fix)
        self.mav = None

        # Session state
        self.current_issues = []
        self.pending_fixes = []
        self.conversation_context = []

    def analyze_current_state(self) -> Dict[str, Any]:
        """
        Analyze current drone state from all available sources

        Returns:
            Comprehensive diagnostic report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'prearm_errors': [],
            'warnings': [],
            'suggestions': [],
            'fixable_issues': [],
            'info': {}
        }

        # Analyze Mission Planner log
        if self.config.mp_log_path and self.config.mp_log_path.exists():
            prearm_errors = self.log_analyzer.find_prearm_errors()

            for error_entry in prearm_errors:
                # Extract error text from dict
                error_text = error_entry.get('text', str(error_entry))

                issue = self._analyze_error(error_text)
                report['prearm_errors'].append(issue)

                # Check if this is fixable
                fixes = self._suggest_fixes(issue)
                if fixes:
                    report['fixable_issues'].extend(fixes)

        return report

    def _analyze_error(self, error_text: str) -> Dict[str, Any]:
        """
        Deep analysis of a single error

        Args:
            error_text: Error message text

        Returns:
            Analysis result with explanation and context
        """
        issue = {
            'error': error_text,
            'type': self._classify_error(error_text),
            'explanation': '',
            'causes': [],
            'solutions': [],
            'severity': 'medium',
            'wiki_link': None
        }

        # Pattern matching for common issues
        patterns = {
            'battery': r'battery|batt|voltage|cell',
            'rc': r'rc not|receiver|transmitter|radio',
            'gps': r'gps|satellite|hdop|fix',
            'compass': r'compass|mag|heading',
            'gyro': r'gyro|imu|accel|calibrat',
            'mode': r'mode|loiter|auto|guided',
            'ekf': r'ekf|navekf|variance',
            'vibration': r'vibr|high noise',
        }

        error_lower = error_text.lower()

        # Classify and provide detailed explanation
        for issue_type, pattern in patterns.items():
            if re.search(pattern, error_lower, re.IGNORECASE):
                issue['type'] = issue_type
                issue.update(self._get_detailed_explanation(issue_type, error_text))
                break

        return issue

    def _classify_error(self, error: str) -> str:
        """Classify error type"""
        error_lower = error.lower()

        if 'battery' in error_lower or 'batt' in error_lower:
            return 'battery'
        elif 'rc' in error_lower or 'radio' in error_lower:
            return 'rc'
        elif 'gps' in error_lower:
            return 'gps'
        elif 'compass' in error_lower or 'mag' in error_lower:
            return 'compass'
        elif 'gyro' in error_lower or 'imu' in error_lower:
            return 'gyro'
        elif 'ekf' in error_lower:
            return 'ekf'
        else:
            return 'general'

    def _get_detailed_explanation(self, issue_type: str, error_text: str) -> Dict[str, Any]:
        """
        Get detailed explanation for issue type

        Returns:
            Dictionary with explanation, causes, solutions
        """
        explanations = {
            'battery': {
                'explanation': 'Система мониторинга батареи обнаружила проблему с питанием. Это может быть низкое напряжение, неправильная калибровка сенсора, или проблема с подключением.',
                'causes': [
                    'Батарея разряжена или повреждена',
                    'Не настроен Battery Monitor',
                    'Неправильные параметры BATT_*',
                    'Плохой контакт разъёма батареи',
                    'Неверное количество ячеек (cells)'
                ],
                'solutions': [
                    'Зарядите батарею полностью',
                    'Проверьте напряжение мультиметром (должно быть >3.7V на ячейку)',
                    'Настройте: Initial Setup → Optional Hardware → Battery Monitor',
                    'Установите правильный тип сенсора (Analog Voltage and Current)',
                    'Проверьте параметры: BATT_MONITOR=4, BATT_CAPACITY, BATT_VOLT_PIN, BATT_CURR_PIN'
                ],
                'severity': 'high',
                'wiki_link': 'https://ardupilot.org/copter/docs/common-powermodule-landingpage.html'
            },
            'rc': {
                'explanation': 'RC приёмник не обнаружен или не передаёт сигнал. Дрон не может взлететь без связи с пультом управления.',
                'causes': [
                    'RC приёмник не подключен к автопилоту',
                    'Передатчик (пульт) выключен',
                    'Нет binding между передатчиком и приёмником',
                    'Неправильный протокол (PPM/SBUS/DSM)',
                    'Плохой контакт проводов'
                ],
                'solutions': [
                    'Включите передатчик (пульт управления)',
                    'Проверьте подключение RC приёмника к автопилоту',
                    'Сделайте binding приёмника с передатчиком (см. инструкцию к RC)',
                    'Настройте: Initial Setup → Mandatory Hardware → Radio Calibration',
                    'Проверьте параметр RSSI_TYPE и RC_PROTOCOLS'
                ],
                'severity': 'critical',
                'wiki_link': 'https://ardupilot.org/copter/docs/common-rc-systems.html'
            },
            'gps': {
                'explanation': 'GPS модуль не получает достаточно спутников или качество сигнала низкое. Необходимо для режимов LOITER, AUTO, RTL.',
                'causes': [
                    'GPS модуль не подключен',
                    'Плохие условия приёма (в помещении, плохая погода)',
                    'Недостаточно времени для lock (cold start занимает ~1 минуту)',
                    'Металлические препятствия рядом',
                    'Неисправный GPS модуль'
                ],
                'solutions': [
                    'Выйдите на открытое пространство (не в помещении)',
                    'Подождите 1-2 минуты для получения fix',
                    'Используйте STABILIZE режим (не требует GPS)',
                    'Проверьте подключение GPS к автопилоту',
                    'Проверьте параметры: GPS_TYPE, GPS_AUTO_SWITCH'
                ],
                'severity': 'medium',
                'wiki_link': 'https://ardupilot.org/copter/docs/common-gps-how-it-works.html'
            },
            'compass': {
                'explanation': 'Компас (магнитометр) показывает некорректные данные или не откалиброван. Критично для полётов с GPS.',
                'causes': [
                    'Компас не откалиброван',
                    'Магнитные помехи от силовых проводов/моторов',
                    'Неправильная ориентация компаса',
                    'Внешний компас установлен неправильно',
                    'Металлические предметы рядом с дроном'
                ],
                'solutions': [
                    'Калибровка: Initial Setup → Mandatory Hardware → Compass',
                    'Отодвиньте GPS/компас от силовых проводов',
                    'Проверьте параметр COMPASS_ORIENT',
                    'Убедитесь что компас направлен правильно (стрелка вперёд)',
                    'Если используется внешний компас - установите COMPASS_EXTERNAL=1'
                ],
                'severity': 'high',
                'wiki_link': 'https://ardupilot.org/copter/docs/common-compass-calibration-in-mission-planner.html'
            },
            'gyro': {
                'explanation': 'Гироскоп/акселерометр требует калибровки или обнаружены проблемы с IMU (Inertial Measurement Unit).',
                'causes': [
                    'IMU не откалиброван',
                    'Высокие вибрации',
                    'Автопилот установлен под углом',
                    'Температурный дрифт',
                    'Неисправный IMU'
                ],
                'solutions': [
                    'Калибровка акселерометра: Initial Setup → Mandatory Hardware → Accel Calibration',
                    'Убедитесь что дрон стоит на ровной поверхности',
                    'Уменьшите вибрации (проверьте баланс винтов, крепления моторов)',
                    'Проверьте параметры: INS_ACCEL_FILTER, INS_GYRO_FILTER',
                    'Не калибруйте в движущемся транспорте'
                ],
                'severity': 'high',
                'wiki_link': 'https://ardupilot.org/copter/docs/common-accelerometer-calibration.html'
            },
            'ekf': {
                'explanation': 'Extended Kalman Filter обнаружил несоответствия в данных сенсоров. EKF объединяет данные GPS, IMU, барометра.',
                'causes': [
                    'Высокие вибрации',
                    'Плохой GPS сигнал',
                    'Некалиброванные сенсоры',
                    'Магнитные помехи',
                    'Резкие изменения положения дрона'
                ],
                'solutions': [
                    'Откалибруйте все сенсоры (компас, акселерометр)',
                    'Уменьшите вибрации',
                    'Улучшите GPS приём',
                    'Проверьте параметры: EKF_CHECK_THRESH, EKF_POSNE_M_NSE',
                    'Не запускайте дрон с ошибками EKF!'
                ],
                'severity': 'critical',
                'wiki_link': 'https://ardupilot.org/copter/docs/common-ekf-failsafe.html'
            },
            'mode': {
                'explanation': 'Текущий режим полёта требует сенсоры/условия которые не выполнены.',
                'causes': [
                    'LOITER/AUTO требует GPS fix',
                    'ALT_HOLD требует барометр',
                    'Переключатель режимов на пульте в неправильном положении',
                    'Не настроены Flight Modes'
                ],
                'solutions': [
                    'Переключитесь в STABILIZE режим (самый базовый)',
                    'Получите GPS lock перед использованием LOITER/AUTO',
                    'Настройте: Initial Setup → Mandatory Hardware → Flight Modes',
                    'Проверьте параметры: FLTMODE1-6'
                ],
                'severity': 'medium',
                'wiki_link': 'https://ardupilot.org/copter/docs/flight-modes.html'
            }
        }

        return explanations.get(issue_type, {
            'explanation': f'Обнаружена ошибка: {error_text}',
            'causes': ['Требуется дополнительная диагностика'],
            'solutions': ['Проверьте логи Mission Planner и ArduPilot Wiki'],
            'severity': 'medium',
            'wiki_link': 'https://ardupilot.org/copter/docs/common-diagnosing-problems-using-logs.html'
        })

    def _suggest_fixes(self, issue: Dict[str, Any]) -> List[FixAction]:
        """
        Suggest automatic fixes for an issue

        Returns:
            List of FixAction objects
        """
        fixes = []
        issue_type = issue['type']

        # Battery fixes
        if issue_type == 'battery':
            if 'not configured' in issue['error'].lower():
                fixes.append(FixAction(
                    title="Настроить Battery Monitor",
                    description="Включить мониторинг батареи с аналоговым сенсором",
                    params={
                        'BATT_MONITOR': 4,  # Analog Voltage and Current
                        'BATT_CAPACITY': 5200,  # mAh (примерное значение)
                        'BATT_VOLT_PIN': 2,
                        'BATT_CURR_PIN': 3,
                        'BATT_VOLT_MULT': 10.1,
                        'BATT_AMP_PERVLT': 17.0
                    },
                    severity="high"
                ))

            if 'below minimum' in issue['error'].lower():
                fixes.append(FixAction(
                    title="Снизить минимальное напряжение",
                    description="Временно снизить порог для тестирования (ВНИМАНИЕ: не летайте с низкой батареей!)",
                    params={
                        'BATT_LOW_VOLT': 10.5,  # Для 3S: 3.5V/cell
                        'BATT_CRT_VOLT': 9.9    # Для 3S: 3.3V/cell
                    },
                    severity="medium"
                ))

        # RC fixes
        elif issue_type == 'rc':
            fixes.append(FixAction(
                title="Настроить RC протокол",
                description="Разрешить все распространённые RC протоколы",
                params={
                    'RC_PROTOCOLS': 1,  # All protocols enabled
                    'RSSI_TYPE': 0      # Disabled (если нет RSSI)
                },
                severity="high"
            ))

        # GPS fixes
        elif issue_type == 'gps':
            fixes.append(FixAction(
                title="Оптимизировать GPS",
                description="Включить auto-switch и SBAS для лучшего приёма",
                params={
                    'GPS_TYPE': 1,          # Auto
                    'GPS_AUTO_SWITCH': 1,   # Enable auto-switch
                    'GPS_GNSS_MODE': 0,     # Default (GPS+GLONASS)
                },
                severity="medium"
            ))

        # Compass fixes
        elif issue_type == 'compass':
            if 'not calibrated' in issue['error'].lower() or 'calibrat' in issue['error'].lower():
                fixes.append(FixAction(
                    title="⚠ Калибровка компаса",
                    description="ВНИМАНИЕ: Это действие запустит процесс калибровки. Вращайте дрон по всем осям.",
                    params={
                        'COMPASS_LEARN': 3,  # Enable learning
                    },
                    severity="high"
                ))

        # Mode fixes
        elif issue_type == 'mode':
            fixes.append(FixAction(
                title="Установить безопасные режимы",
                description="Настроить STABILIZE как основной режим",
                params={
                    'FLTMODE1': 0,  # STABILIZE
                    'FLTMODE2': 0,  # STABILIZE
                    'FLTMODE3': 2,  # ALT_HOLD
                    'FLTMODE4': 5,  # LOITER
                    'FLTMODE5': 6,  # RTL
                    'FLTMODE6': 0,  # STABILIZE
                },
                severity="low"
            ))

        return fixes

    def _get_relevant_docs(self, report: Dict[str, Any], query: str) -> str:
        """
        Get relevant documentation based on report and query

        Args:
            report: Analysis report
            query: User question

        Returns:
            Relevant documentation context
        """
        docs = []

        # Get docs for errors in report
        if report['prearm_errors']:
            # Extract error types
            error_types = set()
            for error in report['prearm_errors'][:3]:
                error_text = error['error'].lower()
                if 'battery' in error_text or 'batt' in error_text:
                    error_types.add('battery')
                if 'rc' in error_text:
                    error_types.add('rc')
                if 'gps' in error_text:
                    error_types.add('gps')
                if 'compass' in error_text or 'mag' in error_text:
                    error_types.add('compass')
                if 'ekf' in error_text:
                    error_types.add('ekf')

            # Get quick context for each type
            for error_type in list(error_types)[:2]:  # Max 2 types
                doc = self.github_dataset.get_quick_context(error_type)
                docs.append(doc)

        # Also check query for keywords
        query_lower = query.lower()
        for keyword in ['battery', 'rc', 'gps', 'compass', 'ekf', 'calibration']:
            if keyword in query_lower and len(docs) < 2:
                doc = self.github_dataset.get_quick_context(keyword)
                if doc not in docs:
                    docs.append(doc)

        if not docs:
            # Return general docs
            docs.append(self.github_dataset.get_doc_links('prearm'))

        return "\n\n".join(docs[:2])  # Max 2 doc sections

    def ask_claude_api(self, query: str, context: str = "") -> str:
        """
        Ask Claude AI with full drone context (REAL AI!)

        Uses Claude CLI to get intelligent responses
        """
        try:
            # Gather full drone context
            report = self.analyze_current_state()

            # Build comprehensive context
            full_context = f"""Ты эксперт по диагностике дронов ArduPilot/Mission Planner.

ВАЖНО: Если не можешь найти решение - ЧЕСТНО скажи "Я не знаю какого хрена не работает, по докам должно работать".

СТАТУС ДРОНА:
{"✅ Подключен к MAVLink" if self.mav and self.mav.is_connected() else "❌ Не подключен"}

PREARM ОШИБКИ ({len(report['prearm_errors'])}):
{chr(10).join([e['error'] for e in report['prearm_errors'][:10]]) if report['prearm_errors'] else "Нет"}

НАЙДЕНО ПРОБЛЕМ: {len(report['prearm_errors'])}
Fixable: {len(report['fixable_issues'])}

ДОСТУПНЫЕ AUTO-FIX:
{chr(10).join([f"- {fix.title} (severity: {fix.severity})" for fix in report['fixable_issues'][:5]]) if report['fixable_issues'] else "Нет"}

{context}

ДОКУМЕНТАЦИЯ ARDUPILOT:
{self._get_relevant_docs(report, query)}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{query}

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Проанализируй ВСЕ данные: статус дрона, логи, ошибки
2. Проверь документацию ArduPilot если нужно
3. Дай КОНКРЕТНОЕ решение с шагами
4. Если это про полёт - посмотри на логи и параметры PID/настройки
5. ЕСЛИ НЕ ЗНАЕШЬ - так и скажи: "Я не знаю какого хрена не работает"
6. Форматируй с маркерами ✓/✗/⚠️ для читаемости
7. Ответ на русском"""

            # Call Claude CLI
            result = subprocess.run(
                ["claude", full_context],
                capture_output=True,
                text=True,
                timeout=90
            )

            if result.stdout:
                return result.stdout.strip()
            else:
                return "❌ Claude не вернул ответа (попробуйте переформулировать вопрос)"

        except FileNotFoundError:
            return (
                "❌ Claude CLI не установлен\n\n"
                "Установите:\n"
                "npm install -g @anthropics/claude-cli\n"
                "claude auth login\n\n"
                "Используется fallback режим (pattern matching)"
            )
        except subprocess.TimeoutExpired:
            return "❌ Таймаут Claude (>90 сек) - попробуйте упростить вопрос"
        except Exception as e:
            return f"❌ Ошибка Claude API: {e}\n\nИспользуется fallback режим"

    def answer_question(self, question: str) -> str:
        """
        Answer natural language questions about logs/issues

        Args:
            question: User question in natural language

        Returns:
            Answer with explanation and suggestions
        """
        question_lower = question.lower()

        # Add to conversation context
        self.conversation_context.append({
            'question': question,
            'timestamp': datetime.now().isoformat()
        })

        # Pattern matching for common questions
        if 'почему' in question_lower and ('не взлет' in question_lower or 'не арм' in question_lower):
            report = self.analyze_current_state()
            if report['prearm_errors']:
                answer = "🔴 Дрон не может взлететь по следующим причинам:\n\n"
                for i, error in enumerate(report['prearm_errors'][:3], 1):
                    answer += f"{i}. {error['error']}\n"
                    answer += f"   Причина: {error['explanation']}\n\n"

                if report['fixable_issues']:
                    answer += f"\n✅ Доступно {len(report['fixable_issues'])} автоматических исправлений. "
                    answer += "Используйте команду 'показать исправления' чтобы увидеть их."

                return answer
            else:
                return "✅ PreArm ошибок не найдено. Дрон готов к взлёту!"

        elif 'что означает' in question_lower or 'что значит' in question_lower:
            # Extract error text from question
            error_match = re.search(r'["\']([^"\']+)["\']|означает\s+(.+)|значит\s+(.+)', question_lower)
            if error_match:
                error_text = error_match.group(1) or error_match.group(2) or error_match.group(3)
                error_text = error_text.strip()

                analysis = self._analyze_error(error_text)

                answer = f"📖 {error_text.upper()}\n\n"
                answer += f"**Объяснение:**\n{analysis['explanation']}\n\n"
                answer += f"**Возможные причины:**\n"
                for cause in analysis['causes'][:3]:
                    answer += f"• {cause}\n"
                answer += f"\n**Как исправить:**\n"
                for solution in analysis['solutions'][:3]:
                    answer += f"✓ {solution}\n"

                if analysis['wiki_link']:
                    answer += f"\n📚 Подробнее: {analysis['wiki_link']}"

                return answer
            else:
                return "Пожалуйста, укажите ошибку в кавычках. Например: Что означает 'RC not found'?"

        elif 'как исправить' in question_lower or 'как решить' in question_lower:
            report = self.analyze_current_state()
            if report['fixable_issues']:
                answer = f"🔧 Найдено {len(report['fixable_issues'])} автоматических исправлений:\n\n"
                for i, fix in enumerate(report['fixable_issues'][:5], 1):
                    answer += f"{i}. {fix.title}\n"
                    answer += f"   {fix.description}\n"
                    answer += f"   Изменит {len(fix.params)} параметров\n\n"
                answer += "\nИспользуйте GUI или команду 'применить исправление X' для применения."
                return answer
            else:
                return "✅ Автоматических исправлений не требуется."

        elif 'показать' in question_lower or 'покажи' in question_lower or 'показат' in question_lower or 'поанализ' in question_lower or 'анализ' in question_lower:
            # Show logs or analyze
            if 'лог' in question_lower or 'log' in question_lower:
                # Show log entries
                prearm_errors = self.log_analyzer.find_prearm_errors()
                if prearm_errors:
                    # Extract text from error entries
                    error_texts = []
                    for error in prearm_errors[:10]:
                        if isinstance(error, dict):
                            error_texts.append(error.get('text', str(error)))
                        else:
                            error_texts.append(str(error))
                    return f"📋 Найдено {len(prearm_errors)} PreArm ошибок:\n\n" + "\n".join(error_texts)
                else:
                    return "✅ PreArm ошибок не найдено в логах."
            else:
                # Show analysis results
                report = self.analyze_current_state()
                answer = "🔍 Результаты анализа:\n\n"

                if report['prearm_errors']:
                    answer += f"❌ PreArm ошибки ({len(report['prearm_errors'])}):\n"
                    for i, error in enumerate(report['prearm_errors'][:5], 1):
                        answer += f"  {i}. {error['error']}\n"
                    answer += "\n"

                if report['fixable_issues']:
                    answer += f"🔧 Доступно исправлений: {len(report['fixable_issues'])}\n"
                    for i, fix in enumerate(report['fixable_issues'][:3], 1):
                        answer += f"  {i}. {fix.title} ({fix.severity})\n"
                    answer += "\n"

                if report['status'] == 'healthy':
                    answer += "✅ Система в норме!"

                return answer

        else:
            # Try Claude AI for intelligent response (even if no logs!)
            try:
                print("🧠 Спрашиваю Claude AI...")
                ai_response = self.ask_claude_api(question)

                # Check if it's an error message (fallback failed)
                if ai_response.startswith("❌"):
                    # Fallback to pattern matching help
                    return (
                        "Я могу помочь с:\n"
                        "• 'Почему дрон не взлетает?' - анализ PreArm ошибок\n"
                        "• 'Что означает \"RC not found\"?' - объяснение ошибок\n"
                        "• 'Как исправить?' - показать автоматические исправления\n"
                        "• 'Как настроить GPS/компас/RC?' - инструкции по настройке\n\n"
                        f"{ai_response}\n\n"
                        "Задайте конкретный вопрос!"
                    )
                else:
                    return ai_response
            except Exception as e:
                return (
                    f"❌ Ошибка AI: {e}\n\n"
                    "Я могу помочь с:\n"
                    "• 'Почему дрон не взлетает?' - анализ PreArm ошибок\n"
                    "• 'Что означает \"RC not found\"?' - объяснение ошибок\n"
                    "• 'Как исправить?' - показать автоматические исправления\n"
                    "• 'Как настроить GPS/компас/RC?' - инструкции по настройке\n\n"
                    "Задайте конкретный вопрос!"
                )

    def connect_to_drone(self, port: Optional[str] = None) -> bool:
        """Connect to drone for auto-fix"""
        if port is None:
            # Auto-detect
            ports = MAVLinkInterface.find_available_ports()
            if not ports:
                return False
            port = ports[0]

        self.mav = MAVLinkInterface(connection_string=port, config=self.config)
        return self.mav.connect(verbose=True)

    def apply_fix(self, fix: FixAction) -> bool:
        """
        Apply a fix by writing parameters to drone

        Args:
            fix: FixAction to apply

        Returns:
            True if successful
        """
        if not self.mav or not self.mav.is_connected():
            print("✗ Not connected to drone. Connect first.")
            return False

        print(f"\n🔧 Applying fix: {fix.title}")
        print(f"   {fix.description}")
        print(f"\n   Will change {len(fix.params)} parameters:")

        for param, value in fix.params.items():
            print(f"   • {param} = {value}")

        # Confirmation
        print(f"\n⚠ Severity: {fix.severity.upper()}")

        success_count = 0
        for param_name, param_value in fix.params.items():
            print(f"\nSetting {param_name} = {param_value}...", end=' ')

            # Determine param type (most are float)
            param_type = 9  # MAV_PARAM_TYPE_REAL32

            if self.mav.set_parameter(param_name, param_value, param_type):
                success_count += 1
            else:
                print("FAILED")

        if success_count == len(fix.params):
            print(f"\n✓ All {success_count} parameters applied successfully!")
            fix.applied = True
            return True
        else:
            print(f"\n⚠ Only {success_count}/{len(fix.params)} parameters applied")
            return False


# Testing
if __name__ == '__main__':
    print("Testing Unified Agent...\n")

    agent = UnifiedAgent()

    # Test analysis
    print("="*60)
    print("Full Diagnostic Report:")
    print("="*60)
    report = agent.analyze_current_state()

    print(f"\nFound {len(report['prearm_errors'])} PreArm errors")
    print(f"Found {len(report['fixable_issues'])} fixable issues")

    # Test Q&A
    print("\n" + "="*60)
    print("Natural Language Q&A:")
    print("="*60)

    questions = [
        "Почему дрон не взлетает?",
        "Что означает 'RC not found'?",
        "Как исправить проблемы?",
    ]

    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {agent.answer_question(q)}")
        print("-"*60)
