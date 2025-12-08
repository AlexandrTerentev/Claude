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
    from .bin_log_parser import BinLogParser
except ImportError:
    from config import Config
    from log_analyzer import LogAnalyzer
    from knowledge_base import KnowledgeBase
    from mavlink_interface import MAVLinkInterface
    from github_dataset import GitHubDataset
    from bin_log_parser import BinLogParser


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
        self.bin_parser = BinLogParser()

        # MAVLink interface (for auto-fix)
        self.mav = None

        # Session state
        self.current_issues = []
        self.pending_fixes = []
        self.chat_history = []  # Store Q&A history
        self.conversation_context = []

        # Downloaded logs tracking
        self.downloaded_logs = []  # List of paths to analyze

    def add_downloaded_log(self, log_path: Path) -> None:
        """
        Register a downloaded log file for analysis

        Args:
            log_path: Path to downloaded .bin file
        """
        if log_path.exists() and log_path not in self.downloaded_logs:
            self.downloaded_logs.append(log_path)
            print(f"✓ Registered log for analysis: {log_path.name}")

    def analyze_current_state(self) -> Dict[str, Any]:
        """
        Analyze current drone state from all available sources
        INCLUDING downloaded logs!

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

        # AUTO-SCAN: Find all downloaded logs in download directory
        download_dir = Path.home() / "missionplanner" / "logs"
        if download_dir.exists():
            # Find all .bin files from last 7 days
            import time
            week_ago = time.time() - (7 * 24 * 60 * 60)

            for bin_file in download_dir.rglob("*.bin"):
                if bin_file.stat().st_mtime > week_ago and bin_file.stat().st_size > 0:
                    if bin_file not in self.downloaded_logs:
                        self.downloaded_logs.append(bin_file)

        # Analyze Mission Planner log (.log file)
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

        # PRIORITY: Analyze downloaded logs (from Download Logs tab)
        if self.downloaded_logs:
            print(f"🔍 Analyzing {len(self.downloaded_logs)} downloaded log(s)...")
            # Sort by modification time (newest first)
            sorted_logs = sorted(self.downloaded_logs, key=lambda x: x.stat().st_mtime, reverse=True)

            for log_path in sorted_logs[:5]:  # Analyze only 5 most recent logs
                try:
                    print(f"  📄 Parsing: {log_path.name} ({log_path.stat().st_size / 1024:.1f} KB)")
                    parsed = self.bin_parser.parse_log(log_path)

                    if parsed and parsed.get('prearm_errors'):
                        print(f"    ✓ Found {len(parsed['prearm_errors'])} PreArm errors in {log_path.name}")
                        for prearm_entry in parsed['prearm_errors']:
                            error_text = prearm_entry.get('text', '')

                            # Avoid duplicates
                            if any(error_text in e.get('error', '') for e in report['prearm_errors']):
                                continue

                            issue = self._analyze_error(error_text)
                            issue['source'] = f"downloaded:{log_path.name}"
                            report['prearm_errors'].append(issue)

                            # Check if fixable
                            fixes = self._suggest_fixes(issue)
                            if fixes:
                                report['fixable_issues'].extend(fixes)
                    else:
                        print(f"    ✓ No PreArm errors in {log_path.name}")
                except Exception as e:
                    print(f"⚠️ Error parsing downloaded log {log_path.name}: {e}")

        # ALSO analyze .bin dataflash logs from Mission Planner directory
        bin_dir = Path.home() / ".local/share/Mission Planner/logs/QUADROTOR/1"
        if bin_dir.exists():
            try:
                bin_prearms = self.bin_parser.extract_prearm_from_directory(bin_dir, max_logs=2)

                for prearm_entry in bin_prearms:
                    error_text = prearm_entry.get('text', '')

                    # Avoid duplicates
                    if any(error_text in e.get('error', '') for e in report['prearm_errors']):
                        continue

                    issue = self._analyze_error(error_text)
                    issue['source'] = f"bin:{prearm_entry.get('source_file', 'unknown')}"
                    report['prearm_errors'].append(issue)

                    # Check if fixable
                    fixes = self._suggest_fixes(issue)
                    if fixes:
                        report['fixable_issues'].extend(fixes)

            except Exception as e:
                print(f"⚠️ Error parsing .bin logs: {e}")

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

    def _deep_technical_analysis(self) -> str:
        """
        Deep technical analysis of logs - vibrations, PID, motors, etc.
        SKIPS basic PreArm errors, focuses on tuning and performance
        """
        # Scan for downloaded logs
        download_dir = Path.home() / "missionplanner" / "logs"
        if download_dir.exists():
            import time
            week_ago = time.time() - (7 * 24 * 60 * 60)
            for bin_file in download_dir.rglob("*.bin"):
                if bin_file.stat().st_mtime > week_ago and bin_file.stat().st_size > 0:
                    if bin_file not in self.downloaded_logs:
                        self.downloaded_logs.append(bin_file)

        if not self.downloaded_logs:
            return "❌ Не найдено скачанных .bin логов для анализа.\n\nСкачайте логи через вкладку '📥 Download Logs'"

        # Get most recent log with decent size (>100KB = actual flight)
        valid_logs = [log for log in self.downloaded_logs if log.stat().st_size > 100_000]
        if not valid_logs:
            return "❌ Найдены только маленькие логи (<100KB).\n\nСкачайте лог с реального полёта/теста моторов."

        # Sort by modification time
        latest_log = sorted(valid_logs, key=lambda x: x.stat().st_mtime, reverse=True)[0]

        print(f"🔬 Глубокий анализ: {latest_log.name} ({latest_log.stat().st_size / 1024:.1f} KB)")

        # Parse the log
        try:
            parsed = self.bin_parser.parse_log(latest_log)
        except Exception as e:
            return f"❌ Ошибка парсинга лога: {e}"

        # Extract technical metrics from log
        tech_data = self._extract_technical_metrics(parsed)

        # Get GitHub docs context for tuning
        docs_context = self._get_tuning_docs_context()

        # Ask Claude for TECHNICAL analysis (not PreArm!)
        tech_prompt = f"""Ты эксперт по настройке ArduPilot. Проанализируй ТЕХНИЧЕСКИЕ параметры лога.

ДАННЫЕ ИЗ ЛОГА "{latest_log.name}":
{tech_data}

GITHUB ДОКУМЕНТАЦИЯ:
{docs_context}

ЗАДАЧА:
Проанализируй настройки и производительность дрона. ИГНОРИРУЙ PreArm ошибки (RC/battery).
Сосредоточься на:
- Вибрации (IMU noise)
- Настройки PID
- Эффективность моторов
- Качество GPS/EKF
- Рекомендации по улучшению

ФОРМАТ ОТВЕТА:
## 🔧 Технический Аудит

**Вибрации:** [оценка + норма из GitHub]
**PID настройки:** [текущие значения + рекомендации]
**Моторы:** [баланс, эффективность]
**GPS/EKF:** [качество]

**Рекомендации:**
1. [конкретное действие]
2. [конкретное действие]

Будь кратким, конкретным, с цифрами."""

        try:
            result = subprocess.run(
                ["claude", tech_prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60
            )

            if result.stdout:
                return f"🔬 ТЕХНИЧЕСКИЙ АНАЛИЗ: {latest_log.name}\n\n{result.stdout.strip()}"
            else:
                return "❌ Claude не вернул ответа"

        except FileNotFoundError:
            # Fallback: basic analysis without AI
            return f"🔬 ТЕХНИЧЕСКИЙ АНАЛИЗ: {latest_log.name}\n\n{tech_data}\n\n⚠️ Claude CLI не установлен для умного анализа"
        except Exception as e:
            return f"❌ Ошибка AI: {e}"

    def _extract_technical_metrics(self, parsed: Dict[str, Any]) -> str:
        """
        Extract technical metrics from parsed log
        Focus on tuning-relevant data
        """
        metrics = []

        # Message type stats
        if 'stats' in parsed and 'message_types' in parsed['stats']:
            msg_types = parsed['stats']['message_types']
            metrics.append(f"📊 Сообщений: {parsed['stats']['total_messages']}")
            important = ['VIBE', 'RCOU', 'GPS', 'ATT', 'IMU', 'BARO']
            for mtype in important:
                if mtype in msg_types:
                    metrics.append(f"  • {mtype}: {msg_types[mtype]}")

        # VIBRATIONS
        if 'technical' in parsed and parsed['technical']['vibrations']:
            vibes = parsed['technical']['vibrations']
            # Calculate average vibrations
            avg_x = sum(v['VibeX'] for v in vibes) / len(vibes)
            avg_y = sum(v['VibeY'] for v in vibes) / len(vibes)
            avg_z = sum(v['VibeZ'] for v in vibes) / len(vibes)
            max_clips = max(max(v['Clip0'], v['Clip1'], v['Clip2']) for v in vibes)

            metrics.append(f"\n🔊 ВИБРАЦИИ (средние):")
            metrics.append(f"  • X: {avg_x:.2f} m/s² (норма <30)")
            metrics.append(f"  • Y: {avg_y:.2f} m/s² (норма <30)")
            metrics.append(f"  • Z: {avg_z:.2f} m/s² (норма <30)")
            metrics.append(f"  • Clipping: {max_clips} (норма 0)")

            # Warning if bad
            if max(avg_x, avg_y, avg_z) > 30:
                metrics.append(f"  ⚠️ ВЫСОКИЕ ВИБРАЦИИ!")
            if max_clips > 0:
                metrics.append(f"  ⚠️ ACCELEROMETER CLIPPING!")

        # MOTORS
        if 'technical' in parsed and parsed['technical']['motors']:
            motors = parsed['technical']['motors']
            # Sample 10% of data to reduce processing
            sample = motors[::max(1, len(motors) // 100)]

            if sample:
                avg_m1 = sum(m['C1'] for m in sample) / len(sample)
                avg_m2 = sum(m['C2'] for m in sample) / len(sample)
                avg_m3 = sum(m['C3'] for m in sample) / len(sample)
                avg_m4 = sum(m['C4'] for m in sample) / len(sample)

                avg_all = (avg_m1 + avg_m2 + avg_m3 + avg_m4) / 4

                metrics.append(f"\n🚁 МОТОРЫ (PWM средние):")
                metrics.append(f"  • M1: {avg_m1:.0f}")
                metrics.append(f"  • M2: {avg_m2:.0f}")
                metrics.append(f"  • M3: {avg_m3:.0f}")
                metrics.append(f"  • M4: {avg_m4:.0f}")
                metrics.append(f"  • Средний: {avg_all:.0f}")

                # Check balance (motors should be within 10% of each other)
                max_diff = max(abs(avg_m1 - avg_all), abs(avg_m2 - avg_all),
                              abs(avg_m3 - avg_all), abs(avg_m4 - avg_all))
                balance_pct = (max_diff / avg_all) * 100 if avg_all > 0 else 0

                metrics.append(f"  • Баланс: ±{balance_pct:.1f}% (норма <10%)")
                if balance_pct > 10:
                    metrics.append(f"  ⚠️ ДИСБАЛАНС МОТОРОВ!")

        # GPS
        if 'technical' in parsed and parsed['technical']['gps']:
            gps_data = parsed['technical']['gps']
            # Get last GPS status
            last_gps = gps_data[-1]

            metrics.append(f"\n🛰️ GPS:")
            metrics.append(f"  • Satellites: {last_gps['NSats']} (норма >10)")
            metrics.append(f"  • HDOP: {last_gps['HDop']:.2f} (норма <2.0)")
            metrics.append(f"  • Status: {last_gps['Status']}")

            if last_gps['NSats'] < 10:
                metrics.append(f"  ⚠️ Мало спутников")
            if last_gps['HDop'] > 2.0:
                metrics.append(f"  ⚠️ Плохая точность GPS")

        # PARAMETERS (PID values)
        if 'parameters' in parsed:
            params = parsed['parameters']
            pid_params = {}

            # Look for PID values
            for key in ['ATC_RAT_PIT_P', 'ATC_RAT_PIT_I', 'ATC_RAT_PIT_D',
                       'ATC_RAT_RLL_P', 'ATC_RAT_RLL_I', 'ATC_RAT_RLL_D',
                       'ATC_RAT_YAW_P', 'ATC_RAT_YAW_I']:
                if key in params:
                    pid_params[key] = params[key]

            if pid_params:
                metrics.append(f"\n⚙️ PID НАСТРОЙКИ:")
                metrics.append(f"  • Roll P: {pid_params.get('ATC_RAT_RLL_P', 'N/A')}")
                metrics.append(f"  • Roll I: {pid_params.get('ATC_RAT_RLL_I', 'N/A')}")
                metrics.append(f"  • Roll D: {pid_params.get('ATC_RAT_RLL_D', 'N/A')}")
                metrics.append(f"  • Pitch P: {pid_params.get('ATC_RAT_PIT_P', 'N/A')}")
                metrics.append(f"  • Yaw P: {pid_params.get('ATC_RAT_YAW_P', 'N/A')}")

        if not metrics:
            metrics.append("⚠️ Недостаточно технических данных")
            metrics.append(f"Всего сообщений: {parsed.get('stats', {}).get('total_messages', 0)}")

        return "\n".join(metrics)

    def _get_tuning_docs_context(self) -> str:
        """
        Get GitHub documentation context for tuning
        """
        # Get tuning-related docs from GitHub dataset
        topics = ['vibration', 'pid', 'motor', 'tuning']
        docs = []

        for topic in topics:
            doc = self.github_dataset.get_quick_context(topic)
            if doc:
                docs.append(doc)

        if not docs:
            docs.append("""
БАЗОВЫЕ НОРМЫ (из ArduPilot Wiki):
- Вибрации: AccX/Y/Z < 30 m/s², Clip count = 0
- PID: начальные значения зависят от размера дрона
- Моторы: баланс ±10%, throttle hover ~50%
- GPS: HDOP < 2.0, satellites > 10
            """)

        return "\n\n".join(docs[:2])  # Max 2 doc sections

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

            # Build CONCISE context (reduce timeout issues)
            # Only include relevant errors and docs
            error_summary = ""
            if report['prearm_errors']:
                # Group similar errors
                unique_errors = []
                seen = set()
                for e in report['prearm_errors'][:5]:  # Max 5 errors
                    err_type = e.get('type', 'unknown')
                    if err_type not in seen:
                        unique_errors.append(e['error'][:80])  # Truncate long errors
                        seen.add(err_type)
                error_summary = chr(10).join([f"• {e}" for e in unique_errors])
            else:
                error_summary = "Нет ошибок"

            full_context = f"""Ты эксперт ArduPilot. Дрон: {"✅ подключен" if self.mav and self.mav.is_connected() else "❌ не подключен"}

ОШИБКИ ({len(report['prearm_errors'])}):
{error_summary}

ИСПРАВЛЕНИЯ: {len(report['fixable_issues'])} доступно

ВОПРОС: {query}

ОТВЕТ (кратко, по делу, с маркерами ✓/✗):"""

            # Call Claude CLI with UTF-8 encoding and SHORTER timeout
            result = subprocess.run(
                ["claude", full_context],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60  # Reduced from 90 to 60 seconds
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
            return "❌ Таймаут Claude API (>60 сек)\n\nПопробуйте:\n• Упростить вопрос\n• Спросить конкретнее\n• Использовать pattern matching (встроенный анализ)"
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

        elif 'техническ' in question_lower or 'настройк' in question_lower or 'вибрац' in question_lower or 'pid' in question_lower or 'гироскоп' in question_lower or 'мотор' in question_lower or 'двигател' in question_lower:
            # DEEP TECHNICAL ANALYSIS - skip PreArm, focus on tuning
            return self._deep_technical_analysis()

        elif 'показать' in question_lower or 'покажи' in question_lower or 'показат' in question_lower or 'поанализ' in question_lower or 'анализ' in question_lower or 'скачал' in question_lower or 'вывод' in question_lower:
            # Analyze and make conclusions
            report = self.analyze_current_state()

            # Ask Claude for smart analysis with conclusions
            try:
                print("🧠 Анализирую через Claude AI...")

                # Build concise error summary
                error_types = {}
                for err in report['prearm_errors']:
                    etype = err.get('type', 'unknown')
                    error_types[etype] = error_types.get(etype, 0) + 1

                error_type_summary = ", ".join([f"{k}:{v}" for k, v in list(error_types.items())[:5]])

                analysis_prompt = f"""Дрон: {len(report['prearm_errors'])} ошибок ({error_type_summary})

Примеры: {chr(10).join([f"- {err['error'][:60]}" for err in report['prearm_errors'][:3]])}

ВЫВОД (2-3 предложения): главная проблема, можно ли взлетать, что делать?"""
                # Use ask_claude_api for analysis
                ai_analysis = self.ask_claude_api(analysis_prompt)

                # Format response with workflow
                answer = f"🔍 АНАЛИЗ ЗАВЕРШЁН\n\n"
                answer += f"📊 Статистика:\n"
                answer += f"• Найдено ошибок: {len(report['prearm_errors'])}\n"
                answer += f"• Доступно исправлений: {len(report['fixable_issues'])}\n"

                # Show sources with details
                if self.downloaded_logs:
                    answer += f"• Проанализировано скачанных логов: {len(self.downloaded_logs)}\n"
                    # Show top 3 most recent logs
                    recent_logs = sorted(self.downloaded_logs, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                    for log in recent_logs:
                        size_kb = log.stat().st_size / 1024
                        answer += f"  - {log.name} ({size_kb:.1f} KB)\n"

                answer += f"\n💡 ВЫВОД:\n{ai_analysis}\n\n"

                # Next steps workflow
                if report['fixable_issues']:
                    answer += "═══════════════════════════════════════\n"
                    answer += "📋 СЛЕДУЮЩИЕ ШАГИ:\n\n"
                    answer += f"1️⃣ Посмотрите вкладку '🔧 Auto-Fix' - найдено {len(report['fixable_issues'])} исправлений\n\n"

                    if not self.mav or not self.mav.is_connected():
                        answer += "2️⃣ ⚠️ ПОДКЛЮЧИТЕ ДРОН для применения исправлений:\n"
                        answer += "   • Выберите порт в верхней панели\n"
                        answer += "   • Нажмите 'Connect'\n\n"
                        answer += "3️⃣ После подключения - нажмите 'Apply Fix' на нужном исправлении\n"
                    else:
                        answer += "2️⃣ ✅ Дрон подключен! Можете применять исправления\n"
                        answer += "3️⃣ Нажмите 'Apply Fix' на нужном исправлении\n"

                    answer += "\n═══════════════════════════════════════"

                return answer

            except Exception as e:
                # Fallback to simple analysis
                answer = "🔍 Результаты анализа:\n\n"

                if report['prearm_errors']:
                    # Group errors by type
                    error_types = {}
                    for err in report['prearm_errors']:
                        etype = err.get('type', 'unknown')
                        error_types[etype] = error_types.get(etype, 0) + 1

                    answer += f"❌ Найдено {len(report['prearm_errors'])} PreArm ошибок:\n"
                    for etype, count in error_types.items():
                        answer += f"  • {etype}: {count} шт.\n"
                    answer += "\n"

                    answer += "💡 ВЫВОД:\n"
                    main_issue = max(error_types.items(), key=lambda x: x[1])
                    answer += f"Основная проблема: {main_issue[0]} ({main_issue[1]} ошибок)\n\n"

                if report['fixable_issues']:
                    answer += f"🔧 Доступно {len(report['fixable_issues'])} автоматических исправлений\n\n"

                    if not self.mav or not self.mav.is_connected():
                        answer += "⚠️ ПОДКЛЮЧИТЕ ДРОН для применения исправлений!\n"
                    else:
                        answer += "✅ Дрон подключен - можете применять исправления\n"

                    answer += "Перейдите на вкладку 'Auto-Fix' для применения.\n"

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

    def save_chat_history(self, filename: Optional[Path] = None) -> bool:
        """
        Save chat history to file

        Args:
            filename: Output file (auto-generated if None)

        Returns:
            True if successful
        """
        if not self.chat_history:
            return False

        try:
            if filename is None:
                history_dir = Path.home() / ".mpdiag" / "chat_history"
                history_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = history_dir / f"chat_{timestamp}.json"

            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.chat_history, f, indent=2, ensure_ascii=False)

            print(f"✓ Chat history saved to {filename}")
            return True

        except Exception as e:
            print(f"✗ Error saving chat history: {e}")
            return False

    def load_chat_history(self, filename: Path) -> bool:
        """Load chat history from file"""
        try:
            import json
            with open(filename, 'r', encoding='utf-8') as f:
                self.chat_history = json.load(f)
            print(f"✓ Loaded {len(self.chat_history)} messages")
            return True
        except Exception as e:
            print(f"✗ Error loading history: {e}")
            return False

    def export_report(self, filename: Optional[Path] = None, format: str = "markdown") -> bool:
        """
        Export diagnostic report with solutions

        Args:
            filename: Output file
            format: "markdown" or "json"

        Returns:
            True if successful
        """
        try:
            report = self.analyze_current_state()

            if filename is None:
                export_dir = Path.home() / ".mpdiag" / "reports"
                export_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                ext = "md" if format == "markdown" else "json"
                filename = export_dir / f"diagnostic_report_{timestamp}.{ext}"

            if format == "markdown":
                content = self._generate_markdown_report(report)
            else:
                import json
                content = json.dumps(report, indent=2, ensure_ascii=False, default=str)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✓ Report exported to {filename}")
            return True

        except Exception as e:
            print(f"✗ Error exporting report: {e}")
            return False

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown format report"""
        md = f"""# MPDiagnosticAgent Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Summary

- **PreArm Errors:** {len(report['prearm_errors'])}
- **Fixable Issues:** {len(report['fixable_issues'])}
- **Warnings:** {len(report['warnings'])}

---

## PreArm Errors

"""
        if report['prearm_errors']:
            for i, error in enumerate(report['prearm_errors'], 1):
                md += f"\n### {i}. {error['error']}\n\n"
                md += f"**Type:** {error['type']}\n\n"
                md += f"**Severity:** {error['severity']}\n\n"
                if error.get('explanation'):
                    md += f"**Explanation:** {error['explanation']}\n\n"
                if error.get('causes'):
                    md += "**Possible Causes:**\n"
                    for cause in error['causes'][:3]:
                        md += f"- {cause}\n"
                    md += "\n"
                if error.get('solutions'):
                    md += "**Solutions:**\n"
                    for sol in error['solutions'][:3]:
                        md += f"- {sol}\n"
                    md += "\n"
                if error.get('wiki_link'):
                    md += f"**Documentation:** {error['wiki_link']}\n\n"
                md += "---\n"
        else:
            md += "✅ No PreArm errors found\n\n"

        md += "\n## Auto-Fix Solutions\n\n"

        if report['fixable_issues']:
            for i, fix in enumerate(report['fixable_issues'], 1):
                md += f"\n### Fix {i}: {fix.title} [{fix.severity}]\n\n"
                md += f"{fix.description}\n\n"
                md += "**Parameters to change:**\n"
                for param, value in fix.params.items():
                    md += f"- `{param}` = `{value}`\n"
                md += "\n---\n"
        else:
            md += "✅ No fixes needed\n\n"

        md += f"\n## Generated by MPDiagnosticAgent v6.0\n"
        md += f"🧠 Powered by Claude AI\n"

        return md

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
