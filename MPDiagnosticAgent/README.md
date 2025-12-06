# MPDiagnosticAgent v5.0

**Unified diagnostic tool for ArduPilot drones with MAVLink log download**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![ArduPilot](https://img.shields.io/badge/ArduPilot-compatible-green.svg)](https://ardupilot.org)

🚁 Smart diagnostic assistant for Mission Planner and ArduPilot drones
📥 Download logs from drone via MAVLink
🔍 Analyze logs, diagnose issues, get solutions
🌐 Russian + English support

---

## ✨ Features

### Core Functionality
- ✅ **Smart Diagnostics** - AI-powered analysis of drone issues
- ✅ **Log Download** - Download `.bin` dataflash logs from drone via MAVLink
- ✅ **Log Analysis** - Parse Mission Planner, telemetry, and dataflash logs
- ✅ **PreArm Diagnostics** - Identify and solve arming issues
- ✅ **Motor Troubleshooting** - Step-by-step motor diagnostic guidance
- ✅ **Wiki Integration** - Search ArduPilot Wiki directly from the tool
- ✅ **Knowledge Base** - 9+ diagnostic rules with solutions
- ✅ **Multi-Language** - Full Russian and English support

### Three User Interfaces
1. **🖥️ Standalone GUI** - Graphical interface with log download tab
2. **⌨️ CLI Tool** - Command-line interface for scripts/automation
3. **🔌 Mission Planner Plugin** - C# plugin (in development)

### Tested & Working
- ✅ Tested with real ArduPilot Quadcopter
- ✅ Successfully downloaded logs via USB (`/dev/ttyACM0`)
- ✅ Cross-platform (Linux/Windows)
- ✅ No hardcoded paths - fully configurable

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/MPDiagnosticAgent.git
cd MPDiagnosticAgent

# Install dependencies
pip3 install -r requirements.txt

# Test installation
python3 -m interfaces.cli config
```

### Usage

**GUI:**
```bash
python3 -m interfaces.gui_standalone
```

**CLI:**
```bash
python3 -m interfaces.cli status
python3 -m interfaces.cli download --latest --port /dev/ttyACM0
python3 -m interfaces.cli motors
```

---

## 📖 Documentation

- 📘 [Installation Guide](docs/installation.md) - Detailed installation for Linux/Windows
- 📗 [User Guide](docs/user_guide.md) - Complete feature documentation
- 📕 [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

---

## 🎯 Use Cases

### 1. Pre-Flight Check
```bash
python3 -m interfaces.cli status
```
Get comprehensive drone health report before flying.

### 2. Download Flight Logs
```bash
python3 -m interfaces.cli download --latest
```
Download latest `.bin` log from drone after flight.

### 3. Diagnose Motor Issues
```bash
python3 -m interfaces.cli motors
```
Get step-by-step troubleshooting for motor/arming problems.

### 4. Search Documentation
```bash
python3 -m interfaces.cli wiki prearm
```
Search ArduPilot Wiki for solutions.

### 5. Interactive Diagnostics
```bash
python3 -m interfaces.gui_standalone
```
Use chat interface to ask questions in natural language.

---

## 🏗️ Architecture

```
MPDiagnosticAgent/
├── core/                    # Core diagnostic engine
│   ├── config.py           # Configuration management
│   ├── diagnostic_engine.py # Unified diagnostic logic
│   ├── knowledge_base.py   # Diagnostic rules loader
│   ├── log_analyzer.py     # Log parsing
│   ├── mavlink_interface.py # MAVLink connection
│   └── log_downloader.py   # Log download via MAVLink
│
├── interfaces/              # User interfaces
│   ├── gui_standalone.py   # Tkinter GUI (3 tabs)
│   └── cli.py              # Command-line interface
│
├── config/
│   └── config.yaml         # User configuration
│
├── knowledge/
│   └── motor_issues.json   # Diagnostic rules
│
├── docs/                   # Documentation
│   ├── installation.md
│   ├── user_guide.md
│   └── troubleshooting.md
│
└── tests/
    └── test_with_real_drone.py  # Real drone tests
```

---

## 💻 Requirements

- **Python 3.8+**
- **pymavlink** - MAVLink protocol
- **pyyaml** - Configuration
- **requests** - Wiki integration
- **tkinter** - GUI (usually pre-installed)

**Platform Support:**
- ✅ Linux (Ubuntu, Debian, Fedora, Arch)
- ✅ Windows 10/11
- ✅ macOS (untested but should work)

---

## 🔧 Configuration

Edit `config/config.yaml`:

```yaml
mission_planner:
  auto_detect: true
  manual_path: /home/user/missionplanner  # Override if needed

mavlink:
  default_port: /dev/ttyACM0  # Linux
  # default_port: COM3          # Windows
  baudrate: 921600
  timeout: 300

diagnostics:
  language: auto  # 'ru', 'en', or 'auto'
  log_lines_to_analyze: 300
  wiki_integration: true
```

---

## 📸 Screenshots

### GUI - Chat Tab
```
╔══════════════════════════════════════════════════════════╗
║   АГЕНТ ДИАГНОСТИКИ ARDUPILOT • MPDIAGNOSTICAGENT v5.0   ║
╚══════════════════════════════════════════════════════════╝

[20:15:23] ❯ ВЫ
почему не крутятся моторы?

[20:15:24] 🤖 АГЕНТ
ДИАГНОСТИКА МОТОРОВ И АРМИНГА
══════════════════════════════

Найдено 1 PreArm ошибок:
  ✗ RC not found

РЕКОМЕНДАЦИИ:
• Подключите RC пульт...
```

### GUI - Download Tab
```
╔══════════════════════════════════════════╗
║ СКАЧИВАНИЕ ЛОГОВ С ДРОНА                 ║
╚══════════════════════════════════════════╝

1. Подключение
   Port: /dev/ttyACM0  [Подключить]
   ✓ Подключено

2. Доступные логи
   - Log 0: 45.2 KB
   - Log 1: 123.4 KB

3. Прогресс
   [████████████████░░░░] 87.3%
   Скачано: 45678/52341 байт
```

### CLI - Status Check
```bash
$ python3 -m interfaces.cli status

FULL DRONE STATUS ANALYSIS
══════════════════════════════════════════════════════

✓ PreArm: No errors found
⚠ Errors: 2 in recent logs

RECOMMENDATIONS:
  → Check recent errors before flight
```

---

## 🧪 Testing

### Test with real drone:

```bash
# Run full test suite
python3 tests/test_with_real_drone.py --all

# Test connection only
python3 tests/test_with_real_drone.py

# Download latest log
python3 tests/test_with_real_drone.py --download-latest
```

**Test Results (Pixhawk 4, ArduCopter 4.3):**
- ✅ Connection: PASSED
- ✅ List logs: PASSED (1 log found)
- ✅ Download: PASSED (log_0_20251206_203941.bin)

---

## 🌟 What's New in v5.0

### Major Changes
- 🔥 **Unified architecture** - All versions merged into one system
- 🔥 **MAVLink log download** - Download logs directly from drone
- 🔥 **Three interfaces** - GUI, CLI, and Plugin (C# in dev)
- 🔥 **No hardcoded paths** - Full configuration system
- 🔥 **Cross-platform** - Linux and Windows support
- 🔥 **Tested with real drone** - Verified with Pixhawk 4

### New Features
- ✨ Download logs via MAVLink protocol
- ✨ Progress bar for downloads
- ✨ Standalone GUI with 3 tabs
- ✨ Comprehensive CLI with 13 commands
- ✨ Auto-detection of Mission Planner
- ✨ Wiki search integration
- ✨ Smart recommendations engine
- ✨ Bilingual support (RU/EN)

### Replaced
- ❌ 5 scattered versions → 1 unified system
- ❌ Hardcoded paths → config.yaml
- ❌ engine/ folder → core/ module
- ❌ Manual log copying → Direct MAVLink download

---

## 📊 Diagnostic Capabilities

### Motor Issues
- RC not calibrated
- ESC not responding
- Battery failsafe
- Safety switch
- Power issues

### Compass Problems
- Calibration failures
- Interference detection
- Parameter recommendations
- Placement guidance

### PreArm Errors
- All standard ArduPilot PreArm checks
- Categorized by type
- Solutions with step-by-step instructions

### Log Analysis
- Mission Planner `.log` files
- Telemetry `.tlog` files
- Dataflash `.bin` files (basic)
- Error detection
- Recent activity summary

---

## 🛠️ Development

### Adding New Diagnostic Rules

Edit `knowledge/motor_issues.json`:

```json
{
  "motor_diagnostic_rules": [
    {
      "issue_id": "new_issue",
      "title_en": "New Issue",
      "title_ru": "Новая проблема",
      "keywords": ["keyword1", "keyword2"],
      "diagnosis_en": "Description...",
      "diagnosis_ru": "Описание...",
      "solution_steps_en": [...],
      "solution_steps_ru": [...],
      "parameters_to_check": [...],
      "wiki_links": [...]
    }
  ]
}
```

### Extending Functionality

**Add new command:**
1. Add to `core/diagnostic_engine.py`
2. Expose in `interfaces/cli.py`
3. Add to GUI chat processing

**Add new interface:**
1. Import from `core/` modules
2. Implement UI
3. Call `DiagnosticEngine.process_query()`

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Full `.bin` log analysis (vibrations, PID)
- [ ] Mission Planner C# plugin completion
- [ ] Parameter comparison/validation
- [ ] Real-time telemetry monitoring
- [ ] Flight log visualization
- [ ] Cloud log storage
- [ ] More diagnostic rules
- [ ] Unit tests

**How to contribute:**
1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## 📝 Changelog

### v5.0.0 (2025-12-06)
- 🎉 Initial unified release
- ✅ MAVLink log download working
- ✅ GUI with 3 tabs
- ✅ CLI with 13 commands
- ✅ Tested with real drone
- ✅ Full documentation

### Previous Versions
- v4.x - Fixed version (scattered files)
- v3.0 - Python-enhanced
- v2.0 - Pure C# version
- v1.0 - Original plugin

---

## 🐛 Troubleshooting

**Common issues:**

| Problem | Solution |
|---------|----------|
| Module not found | `pip3 install -r requirements.txt` |
| Permission denied | `sudo usermod -a -G dialout $USER` |
| Can't connect to drone | Check port with `ls /dev/tty*` |
| No logs found | Drone hasn't flown yet |
| GUI won't start | `sudo apt-get install python3-tk` |

See [Troubleshooting Guide](docs/troubleshooting.md) for details.

---

## 📄 License

MIT License - Free for personal and educational use.

---

## 🙏 Credits

**Project:** MPDiagnosticAgent
**Version:** 5.0.0
**Author:** Claude (Anthropic) + User
**Platform:** Python 3.8+, MAVLink, ArduPilot
**Tested on:** Pixhawk 4, ArduCopter 4.3

**Special thanks:**
- ArduPilot community
- Mission Planner developers
- MAVLink protocol developers

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/MPDiagnosticAgent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/YOUR_USERNAME/MPDiagnosticAgent/discussions)
- **ArduPilot Forum:** [discuss.ardupilot.org](https://discuss.ardupilot.org/)
- **Wiki:** [ardupilot.org](https://ardupilot.org/copter/)

---

## 🎓 Learning Resources

- [ArduPilot Documentation](https://ardupilot.org/copter/)
- [MAVLink Protocol](https://mavlink.io/)
- [Mission Planner Wiki](https://ardupilot.org/planner/)
- [PyMAVLink Documentation](https://github.com/ArduPilot/pymavlink)

---

**Ready to diagnose your drone! ✅**

**Готов к диагностике вашего дрона! ✅**

🚀 Generated with [Claude Code](https://claude.com/claude-code)
